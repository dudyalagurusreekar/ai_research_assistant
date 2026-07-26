"""Multi-Tab Coordinator — Manages tab lifecycle, switching, and cross-tab operations.

Provides the coordination layer between the BrowserActionExecutor and the
Playwright engine for multi-tab workflows. Maintains a tab registry, handles
popup detection, enforces tab limits via pluggable strategies, and supports
cross-tab data extraction.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from tools.browser.core.browser import Browser
from tools.browser.models.response import ActionResult
from tools.browser.tabs.models import TabEvent, TabEventRecord, TabGroup, TabInfo
from tools.browser.tabs.strategies import ConservativeStrategy, TabStrategy

logger = logging.getLogger("MultiTabCoordinator")


class TabLimitExceeded(Exception):
    """Raised when tab operations exceed the configured tab limit."""
    pass


class TabNotFoundError(Exception):
    """Raised when a referenced tab_id does not exist in the registry."""
    pass


class MultiTabCoordinator:
    """Coordinates multi-tab browser operations with lifecycle management.

    The MultiTabCoordinator maintains a registry of all open tabs, handles
    tab creation/closing/switching, detects popups, and enforces resource
    limits through pluggable strategies.

    Architecture position:
        - Sits between BrowserActionExecutor and the Browser/Playwright engine
        - Manages tab-level state that BrowserStateManager tracks per-snapshot
        - Uses TabStrategy for policy decisions (reuse vs. new tab, eviction)
        - Provides tab-aware action execution for multi-tab workflows

    Attributes:
        browser: The Browser instance for tab operations.
        strategy: Tab management policy (Conservative or Parallel).
        tabs: Registry mapping tab_id → TabInfo.
        groups: Registry of named tab groups.
        event_log: Chronological log of tab lifecycle events.
        active_tab_id: ID of the currently active tab.
    """

    def __init__(
        self,
        browser: Browser,
        strategy: Optional[TabStrategy] = None,
    ) -> None:
        """Initialize the Multi-Tab Coordinator.

        Creates an initial tab entry for the browser's current page.

        Args:
            browser: Browser instance for tab operations.
            strategy: Tab management strategy. Defaults to ConservativeStrategy.
        """
        self.browser = browser
        self.strategy = strategy or ConservativeStrategy()
        self._logger = logger

        # Tab registry
        self.tabs: Dict[str, TabInfo] = {}
        self.groups: Dict[str, TabGroup] = {}
        self.event_log: List[TabEventRecord] = []
        self.active_tab_id: Optional[str] = None

        # Register the initial/current tab
        self._register_initial_tab()

    def _register_initial_tab(self) -> None:
        """Register the browser's current page as the initial tab."""
        try:
            url_res = self.browser.get_current_url()
            title_res = self.browser.get_page_title()

            initial_tab = TabInfo(
                url=url_res.data if url_res.success else "about:blank",
                title=title_res.data if title_res.success else "",
                is_active=True,
            )
            self.tabs[initial_tab.tab_id] = initial_tab
            self.active_tab_id = initial_tab.tab_id

            self._record_event(TabEvent.OPENED, initial_tab.tab_id, {
                "url": initial_tab.url,
                "initial": True,
            })
        except Exception as e:
            self._logger.warning(f"Failed to register initial tab: {e}")
            # Create a placeholder tab
            placeholder = TabInfo(is_active=True)
            self.tabs[placeholder.tab_id] = placeholder
            self.active_tab_id = placeholder.tab_id

    def _record_event(
        self, event: TabEvent, tab_id: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a tab lifecycle event.

        Args:
            event: The event type.
            tab_id: Tab involved in the event.
            details: Optional event-specific details.
        """
        record = TabEventRecord(
            event=event,
            tab_id=tab_id,
            details=details or {},
        )
        self.event_log.append(record)
        self._logger.debug(f"Tab event: {event.value} for {tab_id}")

    def open_tab(
        self,
        url: str = "about:blank",
        group_name: Optional[str] = None,
    ) -> TabInfo:
        """Open a new browser tab and navigate to the given URL.

        Checks strategy for reuse opportunities and tab limits.
        If at capacity, evicts the least important tab per strategy.

        Args:
            url: URL to navigate the new tab to.
            group_name: Optional group name to assign the tab to.

        Returns:
            TabInfo: Information about the newly opened tab.

        Raises:
            TabLimitExceeded: If at capacity and no tab can be evicted.
        """
        # Check if we should reuse an existing tab
        reuse_id = self.strategy.should_reuse_tab(self.tabs, url)
        if reuse_id:
            self._logger.info(f"Reusing tab '{reuse_id}' for URL: {url}")
            return self.switch_to_tab(reuse_id, navigate_url=url)

        # Check if we need to evict
        if len(self.tabs) >= self.strategy.max_tabs:
            evict_id = self.strategy.should_evict(self.tabs)
            if evict_id:
                self._logger.info(f"Evicting tab '{evict_id}' (LRU) to make room.")
                self.close_tab(evict_id, reason="eviction")
            else:
                raise TabLimitExceeded(
                    f"Tab limit ({self.strategy.max_tabs}) reached and no tab can be evicted."
                )

        # Open new tab via browser
        try:
            # Navigate to the URL using the browser's open_url
            # In a real Playwright implementation, this would create a new page
            # For now, we simulate tab opening through the browser facade
            nav_res = self.browser.open_url(url)

            new_tab = TabInfo(
                url=url,
                title=nav_res.title if hasattr(nav_res, 'title') else "",
                is_active=True,
                group_name=group_name,
            )

            # Deactivate previously active tab
            if self.active_tab_id and self.active_tab_id in self.tabs:
                self.tabs[self.active_tab_id].is_active = False

            self.tabs[new_tab.tab_id] = new_tab
            self.active_tab_id = new_tab.tab_id

            # Add to group if specified
            if group_name:
                self._ensure_group(group_name)
                self.groups[group_name].add_tab(new_tab.tab_id)

            self._record_event(TabEvent.OPENED, new_tab.tab_id, {
                "url": url,
                "group": group_name,
            })

            self._logger.info(f"Opened new tab '{new_tab.tab_id}' → {url}")
            return new_tab

        except Exception as e:
            self._logger.error(f"Failed to open tab for URL '{url}': {e}")
            raise

    def close_tab(
        self,
        tab_id: str,
        reason: str = "user_request",
    ) -> bool:
        """Close a browser tab and remove it from the registry.

        If closing the active tab, switches to the most recently accessed
        remaining tab automatically.

        Args:
            tab_id: ID of the tab to close.
            reason: Reason for closing (for event logging).

        Returns:
            bool: True if the tab was closed successfully.

        Raises:
            TabNotFoundError: If the tab_id is not in the registry.
        """
        if tab_id not in self.tabs:
            raise TabNotFoundError(f"Tab '{tab_id}' not found in registry.")

        tab_info = self.tabs[tab_id]

        # Don't close the last tab
        if len(self.tabs) <= 1:
            self._logger.warning("Cannot close the last remaining tab.")
            return False

        # Remove from groups
        for group in self.groups.values():
            group.remove_tab(tab_id)

        # Remove from registry
        del self.tabs[tab_id]

        event_type = TabEvent.EVICTED if reason == "eviction" else TabEvent.CLOSED
        self._record_event(event_type, tab_id, {
            "url": tab_info.url,
            "reason": reason,
        })

        # If we closed the active tab, switch to most recent remaining
        if tab_id == self.active_tab_id:
            remaining = list(self.tabs.values())
            if remaining:
                remaining.sort(key=lambda t: t.last_accessed, reverse=True)
                self.active_tab_id = remaining[0].tab_id
                remaining[0].is_active = True
                remaining[0].touch()

        self._logger.info(f"Closed tab '{tab_id}' (reason: {reason})")
        return True

    def switch_to_tab(
        self,
        tab_id: str,
        navigate_url: Optional[str] = None,
    ) -> TabInfo:
        """Switch focus to a different tab.

        Args:
            tab_id: ID of the tab to switch to.
            navigate_url: Optional URL to navigate the tab to after switching.

        Returns:
            TabInfo: Updated tab information.

        Raises:
            TabNotFoundError: If the tab_id is not in the registry.
        """
        if tab_id not in self.tabs:
            raise TabNotFoundError(f"Tab '{tab_id}' not found in registry.")

        # Deactivate current tab
        if self.active_tab_id and self.active_tab_id in self.tabs:
            self.tabs[self.active_tab_id].is_active = False

        # Activate target tab
        tab = self.tabs[tab_id]
        tab.is_active = True
        tab.touch()
        self.active_tab_id = tab_id

        # Navigate if URL provided
        if navigate_url and navigate_url != tab.url:
            try:
                self.browser.open_url(navigate_url)
                tab.url = navigate_url
                tab.navigation_count += 1
                self._record_event(TabEvent.NAVIGATED, tab_id, {"url": navigate_url})
            except Exception as e:
                self._logger.error(f"Navigation failed for tab '{tab_id}': {e}")

        self._record_event(TabEvent.SWITCHED, tab_id, {"url": tab.url})

        self._logger.debug(f"Switched to tab '{tab_id}' ({tab.url})")
        return tab

    def get_active_tab(self) -> Optional[TabInfo]:
        """Get the currently active tab's information.

        Returns:
            Optional[TabInfo]: Active tab info, or None if no tabs exist.
        """
        if self.active_tab_id and self.active_tab_id in self.tabs:
            return self.tabs[self.active_tab_id]
        return None

    def list_tabs(self) -> List[TabInfo]:
        """Get a list of all open tabs.

        Returns:
            List[TabInfo]: All tabs sorted by creation time.
        """
        tabs = list(self.tabs.values())
        tabs.sort(key=lambda t: t.created_at)
        return tabs

    def find_tab_by_url(self, url: str) -> Optional[TabInfo]:
        """Find a tab by its current URL.

        Args:
            url: URL to search for (exact match).

        Returns:
            Optional[TabInfo]: Matching tab, or None.
        """
        for tab in self.tabs.values():
            if tab.url == url:
                return tab
        return None

    def find_tabs_by_domain(self, domain: str) -> List[TabInfo]:
        """Find all tabs on a given domain.

        Args:
            domain: Domain to search for (e.g., "google.com").

        Returns:
            List[TabInfo]: Tabs on the specified domain.
        """
        matching = []
        for tab in self.tabs.values():
            try:
                from urllib.parse import urlparse
                tab_domain = urlparse(tab.url).netloc.lower()
                if domain.lower() in tab_domain:
                    matching.append(tab)
            except Exception:
                pass
        return matching

    def create_group(self, name: str, purpose: str = "") -> TabGroup:
        """Create a named tab group.

        Args:
            name: Group name.
            purpose: Description of the group's purpose.

        Returns:
            TabGroup: The created group.
        """
        group = TabGroup(name=name, purpose=purpose)
        self.groups[name] = group
        self._logger.debug(f"Created tab group '{name}'")
        return group

    def _ensure_group(self, name: str) -> None:
        """Ensure a tab group exists, creating it if needed.

        Args:
            name: Group name to ensure exists.
        """
        if name not in self.groups:
            self.groups[name] = TabGroup(name=name)

    def add_tab_to_group(self, tab_id: str, group_name: str) -> None:
        """Add a tab to a named group.

        Args:
            tab_id: Tab to add.
            group_name: Target group name (created if needed).

        Raises:
            TabNotFoundError: If the tab_id is not in the registry.
        """
        if tab_id not in self.tabs:
            raise TabNotFoundError(f"Tab '{tab_id}' not found.")
        self._ensure_group(group_name)
        self.groups[group_name].add_tab(tab_id)
        self.tabs[tab_id].group_name = group_name

    def close_group(self, group_name: str) -> int:
        """Close all tabs in a group and remove the group.

        Args:
            group_name: Name of the group to close.

        Returns:
            int: Number of tabs that were closed.
        """
        if group_name not in self.groups:
            return 0

        group = self.groups[group_name]
        closed_count = 0
        # Close tabs in reverse order (most recent first) to preserve active tab
        for tab_id in list(reversed(group.tab_ids)):
            if tab_id in self.tabs and len(self.tabs) > 1:
                try:
                    self.close_tab(tab_id, reason=f"group_close:{group_name}")
                    closed_count += 1
                except Exception:
                    pass

        del self.groups[group_name]
        self._logger.info(f"Closed group '{group_name}': {closed_count} tabs closed")
        return closed_count

    def extract_data_from_tabs(
        self,
        tab_ids: Optional[List[str]] = None,
        javascript: str = "document.body.innerText",
    ) -> Dict[str, Any]:
        """Extract data from multiple tabs by running JavaScript on each.

        Switches to each tab, executes the JavaScript, and collects results.
        Restores the original active tab when done.

        Args:
            tab_ids: List of tab IDs to extract from. Defaults to all tabs.
            javascript: JavaScript expression to evaluate on each tab.

        Returns:
            Dict[str, Any]: Mapping of tab_id → extracted data.
        """
        target_ids = tab_ids or list(self.tabs.keys())
        original_active = self.active_tab_id
        results: Dict[str, Any] = {}

        for tab_id in target_ids:
            if tab_id not in self.tabs:
                results[tab_id] = {"error": "Tab not found"}
                continue

            try:
                self.switch_to_tab(tab_id)
                js_res = self.browser.execute_javascript(javascript)
                results[tab_id] = {
                    "url": self.tabs[tab_id].url,
                    "title": self.tabs[tab_id].title,
                    "data": js_res.data if js_res.success else None,
                    "success": js_res.success,
                }
            except Exception as e:
                results[tab_id] = {
                    "url": self.tabs.get(tab_id, TabInfo()).url,
                    "error": str(e),
                }

        # Restore original active tab
        if original_active and original_active in self.tabs:
            try:
                self.switch_to_tab(original_active)
            except Exception:
                pass

        return results

    def get_tab_count(self) -> int:
        """Get the current number of open tabs.

        Returns:
            int: Number of tabs in the registry.
        """
        return len(self.tabs)

    def get_event_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the most recent tab events.

        Args:
            limit: Maximum number of events to return.

        Returns:
            List[Dict[str, Any]]: Recent events in chronological order.
        """
        recent = self.event_log[-limit:]
        return [e.to_dict() for e in recent]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current tab state.

        Returns:
            Dict[str, Any]: Summary including tab count, groups, and active tab.
        """
        return {
            "tab_count": len(self.tabs),
            "max_tabs": self.strategy.max_tabs,
            "active_tab_id": self.active_tab_id,
            "active_tab_url": (
                self.tabs[self.active_tab_id].url
                if self.active_tab_id and self.active_tab_id in self.tabs
                else None
            ),
            "strategy": type(self.strategy).__name__,
            "groups": {name: g.to_dict() for name, g in self.groups.items()},
            "tabs": [t.to_dict() for t in self.list_tabs()],
            "total_events": len(self.event_log),
        }
