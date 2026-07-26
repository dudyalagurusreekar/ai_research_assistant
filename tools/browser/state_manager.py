import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from tools.browser.core.browser import Browser
from tools.browser.browser.state import BrowserState, BrowserStateSnapshot

logger = logging.getLogger("BrowserStateMemoryManager")


class BrowserStateMemoryManager:
    """Manages browser state snapshot history, versions, diffs, and rollbacks."""

    def __init__(self, browser: Browser, max_history_size: int = 50) -> None:
        """Initialize the state manager.

        Args:
            browser (Browser): Browser orchestrator facade.
            max_history_size (int): Max history snapshots limit to cache.
        """
        self.browser = browser
        self.max_history_size = max_history_size
        self.history: List[BrowserStateSnapshot] = []
        self.current_version = 0
        self._logger = logger

        self.state = BrowserState()

        # Persistent metadata tracking (not repeatedly sent to LLM)
        self.navigation_history: List[str] = self.state.navigation_history
        self.downloaded_files: List[str] = self.state.downloaded_files
        self.screenshots: List[str] = self.state.screenshots
        self.extracted_data: List[Dict[str, Any]] = self.state.extracted_data

    def record_screenshot(self, filepath: str) -> None:
        """Track screenshot artifact path."""
        if filepath and filepath not in self.screenshots:
            self.screenshots.append(filepath)

    def record_download(self, filepath: str) -> None:
        """Track downloaded file path."""
        if filepath and filepath not in self.downloaded_files:
            self.downloaded_files.append(filepath)

    def record_extracted_data(self, key: str, value: Any) -> None:
        """Track extracted structured text or data fields."""
        self.extracted_data.append({
            "key": key,
            "value": value,
            "timestamp": time.time()
        })

    def capture_state(self, previous_action: Optional[Dict[str, Any]] = None) -> BrowserStateSnapshot:
        """Capture the live state of the browser.

        Args:
            previous_action (Optional[Dict[str, Any]]): The action leading to this state.

        Returns:
            BrowserStateSnapshot: Immutable state snapshot.
        """
        # Fetch base fields
        url_res = self.browser.get_current_url()
        url = url_res.data if url_res.success else "about:blank"

        title_res = self.browser.get_page_title()
        title = title_res.data if title_res.success else ""

        html_res = self.browser.get_page_html()
        dom = html_res.data if html_res.success else ""

        # Track navigation history
        if not self.navigation_history or self.navigation_history[-1] != url:
            self.navigation_history.append(url)

        # Track screenshot path if the action was a screenshot
        if previous_action and previous_action.get("action") == "capture_screenshot":
            path_val = previous_action.get("url") or previous_action.get("text_input")
            if path_val:
                self.record_screenshot(path_val)

        # Open tabs and active context page details
        tabs = []
        active_idx = 0
        try:
            if self.browser.automation and hasattr(self.browser.automation, "strategy"):
                strat = self.browser.automation.strategy
                if hasattr(strat, "_context") and strat._context:
                    for idx, p in enumerate(strat._context.pages):
                        try:
                            p_url = p.url
                            tabs.append(p_url)
                            if strat._page and p == strat._page:
                                active_idx = idx
                        except Exception:
                            pass
        except Exception:
            pass

        if not tabs:
            tabs = [url]

        # Get Cookies (Synchronously routed to background event loop)
        cookies = []
        try:
            if self.browser.automation and hasattr(self.browser.automation, "strategy"):
                strat = self.browser.automation.strategy
                if hasattr(strat, "_context") and strat._context:
                    cookies = self.browser.automation._run_sync(strat._context.cookies())
        except Exception:
            pass

        # Extract Local/Session Storage via JS execution
        local_storage = {}
        session_storage = {}
        try:
            ls_res = self.browser.execute_javascript("JSON.stringify(window.localStorage)")
            if ls_res.success and ls_res.data:
                local_storage = json.loads(ls_res.data)
        except Exception:
            pass

        try:
            ss_res = self.browser.execute_javascript("JSON.stringify(window.sessionStorage)")
            if ss_res.success and ss_res.data:
                session_storage = json.loads(ss_res.data)
        except Exception:
            pass

        # Extract Scroll coordinates
        scroll = {"x": 0, "y": 0}
        try:
            scroll_res = self.browser.execute_javascript(
                "JSON.stringify({x: window.scrollX || window.pageXOffset, y: window.scrollY || window.pageYOffset})"
            )
            if scroll_res.success and scroll_res.data:
                scroll = json.loads(scroll_res.data)
        except Exception:
            pass

        # Extract active/focused element selector path
        focused_el = None
        try:
            script = """(() => {
                const el = document.activeElement;
                if (!el || el === document.body) return null;
                if (el.id) return '#' + el.id;
                if (el.className) {
                    const firstClass = el.className.trim().split(/\\s+/)[0];
                    if (firstClass) return el.tagName.toLowerCase() + '.' + firstClass;
                }
                return el.tagName.toLowerCase();
            })()"""
            focus_res = self.browser.execute_javascript(script)
            if focus_res.success and focus_res.data:
                focused_el = focus_res.data
        except Exception:
            pass

        # Extract Form elements metadata
        detected_forms = []
        try:
            form_script = """(() => {
                const forms = [];
                document.querySelectorAll("form").forEach((form, idx) => {
                    const id = form.id || `form-${idx}`;
                    const inputs = [];
                    form.querySelectorAll("input, select, textarea").forEach(input => {
                        inputs.push({
                            id: input.id,
                            name: input.name,
                            type: input.type || input.tagName.toLowerCase(),
                            value: input.value
                        });
                    });
                    forms.push({ id, action: form.action, inputs });
                });
                return JSON.stringify(forms);
            })()"""
            form_res = self.browser.execute_javascript(form_script)
            if form_res.success and form_res.data:
                detected_forms = json.loads(form_res.data)
        except Exception:
            pass

        # Create Immutable Snapshot
        snapshot = BrowserStateSnapshot(
            version=self.current_version,
            timestamp=time.time(),
            url=url,
            title=title,
            dom_snapshot=dom,
            tabs=tabs,
            active_tab_index=active_idx,
            cookies=cookies,
            local_storage=local_storage,
            session_storage=session_storage,
            scroll_position=scroll,
            focused_element_selector=focused_el,
            detected_forms=detected_forms,
            previous_action=previous_action,
        )

        self.history.append(snapshot)
        self.current_version += 1

        if len(self.history) > self.max_history_size:
            self.history.pop(0)

        self.state.update_state(snapshot, previous_action=previous_action)

        self._logger.info(f"Captured state snapshot version={snapshot.version} url='{snapshot.url}'")
        return snapshot

    def diff_snapshots(self, snap_a: BrowserStateSnapshot, snap_b: BrowserStateSnapshot) -> Dict[str, Any]:
        """Compute state differences between two snapshots."""
        cookies_a = {c["name"]: c["value"] for c in snap_a.cookies if "name" in c}
        cookies_b = {c["name"]: c["value"] for c in snap_b.cookies if "name" in c}
        added_cookies = [k for k in cookies_b if k not in cookies_a]
        removed_cookies = [k for k in cookies_a if k not in cookies_b]
        changed_cookies = [k for k in cookies_b if k in cookies_a and cookies_b[k] != cookies_a[k]]

        added_ls = [k for k in snap_b.local_storage if k not in snap_a.local_storage]
        removed_ls = [k for k in snap_a.local_storage if k not in snap_b.local_storage]
        changed_ls = [k for k in snap_b.local_storage if k in snap_a.local_storage and snap_b.local_storage[k] != snap_a.local_storage[k]]

        scroll_changed = (
            snap_a.scroll_position.get("x") != snap_b.scroll_position.get("x") or
            snap_a.scroll_position.get("y") != snap_b.scroll_position.get("y")
        )

        return {
            "url_changed": snap_a.url != snap_b.url,
            "title_changed": snap_a.title != snap_b.title,
            "added_cookies": added_cookies,
            "removed_cookies": removed_cookies,
            "changed_cookies": changed_cookies,
            "local_storage": {
                "added": added_ls,
                "removed": removed_ls,
                "changed": changed_ls,
            },
            "scroll_changed": scroll_changed,
            "focus_changed": snap_a.focused_element_selector != snap_b.focused_element_selector,
        }

    def rollback_to(self, version: int) -> BrowserStateSnapshot:
        """Rollback the active browser state to match a previously recorded snapshot version."""
        target_snap = None
        for snap in self.history:
            if snap.version == version:
                target_snap = snap
                break

        if not target_snap:
            raise ValueError(f"Snapshot version {version} not found in history cache.")

        self._logger.warning(f"Initiating browser state rollback to version={version} url='{target_snap.url}'")

        self.browser.open_url(target_snap.url)

        try:
            if self.browser.automation and hasattr(self.browser.automation, "strategy"):
                strat = self.browser.automation.strategy
                if hasattr(strat, "_context") and strat._context:
                    self.browser.automation._run_sync(strat._context.clear_cookies())
                    if target_snap.cookies:
                        self.browser.automation._run_sync(strat._context.add_cookies(target_snap.cookies))
        except Exception as e:
            self._logger.error(f"Failed to restore cookies during rollback: {e}")

        try:
            ls_json = json.dumps(target_snap.local_storage)
            self.browser.execute_javascript(f"""
                window.localStorage.clear();
                const ls = {ls_json};
                for (const k in ls) {{ window.localStorage.setItem(k, ls[k]); }}
            """)
        except Exception as e:
            self._logger.error(f"Failed to restore LocalStorage during rollback: {e}")

        try:
            ss_json = json.dumps(target_snap.session_storage)
            self.browser.execute_javascript(f"""
                window.sessionStorage.clear();
                const ss = {ss_json};
                for (const k in ss) {{ window.sessionStorage.setItem(k, ss[k]); }}
            """)
        except Exception as e:
            self._logger.error(f"Failed to restore SessionStorage during rollback: {e}")

        try:
            scroll_x = target_snap.scroll_position.get("x", 0)
            scroll_y = target_snap.scroll_position.get("y", 0)
            self.browser.execute_javascript(f"window.scrollTo({scroll_x}, {scroll_y})")
        except Exception as e:
            self._logger.error(f"Failed to restore scroll position: {e}")

        self.browser.open_url(target_snap.url)
        self.state.rollback_state(target_snap)
        return target_snap

    def serialize_history(self) -> str:
        """Serialize memory history cache to a JSON string representation."""
        data = {
            "version": self.current_version,
            "snapshots": [snap.to_dict() for snap in self.history]
        }
        return json.dumps(data, indent=2)

    def deserialize_history(self, json_data: str) -> None:
        """Deserialize and populate state manager memory from JSON."""
        data = json.loads(json_data)
        self.current_version = data.get("version", 0)
        self.history = [BrowserStateSnapshot.from_dict(snap) for snap in data.get("snapshots", [])]
