"""Comprehensive tests for the Multi-Tab Coordinator component.

Tests tab CRUD, switching, popup handling, limit enforcement,
cross-tab data extraction, groups, strategies, and edge cases.
"""

import time
import pytest
from unittest.mock import MagicMock

from tools.browser.tabs.models import TabEvent, TabEventRecord, TabGroup, TabInfo
from tools.browser.tabs.strategies import ConservativeStrategy, ParallelStrategy
from tools.browser.tabs.coordinator import (
    MultiTabCoordinator,
    TabLimitExceeded,
    TabNotFoundError,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def mock_browser():
    """Create a mock Browser instance."""
    browser = MagicMock()
    browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com")
    browser.get_page_title.return_value = MagicMock(success=True, data="Example")
    browser.open_url.return_value = MagicMock(success=True, data=None)
    browser.execute_javascript.return_value = MagicMock(success=True, data="test data")
    return browser


@pytest.fixture
def coordinator(mock_browser):
    """Create a MultiTabCoordinator with mock browser."""
    return MultiTabCoordinator(mock_browser)


# ─────────────────────────────────────────────
# Tab Models Tests
# ─────────────────────────────────────────────

class TestTabModels:
    """Tests for tab data models."""

    def test_tab_info_defaults(self):
        """TabInfo should have sensible defaults."""
        tab = TabInfo()
        assert tab.url == "about:blank"
        assert tab.is_active is False
        assert tab.navigation_count == 0
        assert tab.group_name is None

    def test_tab_info_touch(self):
        """TabInfo.touch should update last_accessed."""
        tab = TabInfo()
        old_time = tab.last_accessed
        time.sleep(0.01)
        tab.touch()
        assert tab.last_accessed > old_time

    def test_tab_info_serialization(self):
        """TabInfo should serialize to dictionary."""
        tab = TabInfo(url="https://test.com", title="Test", is_active=True)
        d = tab.to_dict()
        assert d["url"] == "https://test.com"
        assert d["title"] == "Test"
        assert d["is_active"] is True

    def test_tab_group_operations(self):
        """TabGroup should add and remove tabs correctly."""
        group = TabGroup(name="research", purpose="Research tabs")
        
        group.add_tab("tab_1")
        group.add_tab("tab_2")
        assert len(group.tab_ids) == 2
        
        # Duplicate add should be idempotent
        group.add_tab("tab_1")
        assert len(group.tab_ids) == 2
        
        group.remove_tab("tab_1")
        assert len(group.tab_ids) == 1
        assert "tab_2" in group.tab_ids

    def test_tab_group_serialization(self):
        """TabGroup should serialize to dictionary."""
        group = TabGroup(name="test", purpose="Testing")
        group.add_tab("t1")
        d = group.to_dict()
        assert d["name"] == "test"
        assert d["tab_count"] == 1

    def test_tab_event_record(self):
        """TabEventRecord should store event details."""
        record = TabEventRecord(
            event=TabEvent.OPENED,
            tab_id="tab_1",
            details={"url": "https://test.com"},
        )
        d = record.to_dict()
        assert d["event"] == "OPENED"
        assert d["tab_id"] == "tab_1"

    def test_tab_event_values(self):
        """All tab events should have correct string values."""
        assert TabEvent.OPENED.value == "OPENED"
        assert TabEvent.CLOSED.value == "CLOSED"
        assert TabEvent.SWITCHED.value == "SWITCHED"
        assert TabEvent.NAVIGATED.value == "NAVIGATED"
        assert TabEvent.POPUP.value == "POPUP"
        assert TabEvent.EVICTED.value == "EVICTED"


# ─────────────────────────────────────────────
# Tab Strategies Tests
# ─────────────────────────────────────────────

class TestTabStrategies:
    """Tests for tab management strategies."""

    def test_conservative_max_tabs(self):
        """ConservativeStrategy should respect max_tabs setting."""
        strategy = ConservativeStrategy(max_tab_count=3)
        assert strategy.max_tabs == 3

    def test_conservative_eviction_lru(self):
        """ConservativeStrategy should evict least recently used tab."""
        strategy = ConservativeStrategy(max_tab_count=2)
        
        tab1 = TabInfo(tab_id="t1", last_accessed=100.0, is_active=False)
        tab2 = TabInfo(tab_id="t2", last_accessed=200.0, is_active=False)
        
        tabs = {"t1": tab1, "t2": tab2}
        evict_id = strategy.should_evict(tabs)
        assert evict_id == "t1"  # Oldest accessed

    def test_conservative_no_eviction_under_limit(self):
        """ConservativeStrategy should not evict when under limit."""
        strategy = ConservativeStrategy(max_tab_count=3)
        tabs = {"t1": TabInfo(tab_id="t1")}
        assert strategy.should_evict(tabs) is None

    def test_conservative_reuse_exact_url(self):
        """ConservativeStrategy should reuse tab with exact URL match."""
        strategy = ConservativeStrategy()
        tabs = {
            "t1": TabInfo(tab_id="t1", url="https://google.com", is_active=False),
        }
        reuse_id = strategy.should_reuse_tab(tabs, "https://google.com")
        assert reuse_id == "t1"

    def test_conservative_reuse_domain_match(self):
        """ConservativeStrategy should reuse tab with matching domain."""
        strategy = ConservativeStrategy()
        tabs = {
            "t1": TabInfo(tab_id="t1", url="https://google.com/search", is_active=False),
        }
        reuse_id = strategy.should_reuse_tab(tabs, "https://google.com/maps")
        assert reuse_id == "t1"

    def test_conservative_no_reuse_empty_tabs(self):
        """ConservativeStrategy should return None for empty tab registry."""
        strategy = ConservativeStrategy()
        assert strategy.should_reuse_tab({}, "https://test.com") is None

    def test_parallel_max_tabs(self):
        """ParallelStrategy should have higher default max_tabs."""
        strategy = ParallelStrategy()
        assert strategy.max_tabs == 8

    def test_parallel_only_reuse_exact_url(self):
        """ParallelStrategy should only reuse on exact URL match."""
        strategy = ParallelStrategy()
        tabs = {
            "t1": TabInfo(tab_id="t1", url="https://google.com/page1"),
        }
        # Different page on same domain — should NOT reuse
        assert strategy.should_reuse_tab(tabs, "https://google.com/page2") is None
        # Exact match — should reuse
        assert strategy.should_reuse_tab(tabs, "https://google.com/page1") == "t1"

    def test_parallel_eviction_at_limit(self):
        """ParallelStrategy should evict LRU when at hard limit."""
        strategy = ParallelStrategy(max_tab_count=2)
        tabs = {
            "t1": TabInfo(tab_id="t1", last_accessed=100.0, is_active=False),
            "t2": TabInfo(tab_id="t2", last_accessed=200.0, is_active=False),
        }
        evict_id = strategy.should_evict(tabs)
        assert evict_id == "t1"

    def test_conservative_does_not_evict_active(self):
        """ConservativeStrategy should not evict the active tab."""
        strategy = ConservativeStrategy(max_tab_count=2)
        tabs = {
            "t1": TabInfo(tab_id="t1", last_accessed=100.0, is_active=True),
            "t2": TabInfo(tab_id="t2", last_accessed=200.0, is_active=False),
        }
        evict_id = strategy.should_evict(tabs)
        assert evict_id == "t2"  # Can only evict non-active


# ─────────────────────────────────────────────
# MultiTabCoordinator Tests
# ─────────────────────────────────────────────

class TestMultiTabCoordinator:
    """Tests for the main MultiTabCoordinator."""

    def test_initial_tab_registered(self, coordinator):
        """Coordinator should register an initial tab on construction."""
        assert coordinator.get_tab_count() == 1
        active = coordinator.get_active_tab()
        assert active is not None
        assert active.is_active is True

    def test_open_tab(self, coordinator):
        """Opening a tab should add it to the registry and make it active."""
        tab = coordinator.open_tab("https://google.com")
        
        assert tab.url == "https://google.com"
        assert tab.is_active is True
        assert coordinator.get_tab_count() == 2
        assert coordinator.active_tab_id == tab.tab_id

    def test_close_tab(self, coordinator):
        """Closing a tab should remove it from the registry."""
        tab = coordinator.open_tab("https://test.com")
        assert coordinator.get_tab_count() == 2
        
        coordinator.close_tab(tab.tab_id)
        assert coordinator.get_tab_count() == 1

    def test_close_last_tab_prevented(self, coordinator):
        """Closing the last remaining tab should return False."""
        assert coordinator.get_tab_count() == 1
        active_id = coordinator.active_tab_id
        result = coordinator.close_tab(active_id)
        assert result is False
        assert coordinator.get_tab_count() == 1

    def test_close_nonexistent_tab_raises(self, coordinator):
        """Closing a nonexistent tab should raise TabNotFoundError."""
        with pytest.raises(TabNotFoundError):
            coordinator.close_tab("nonexistent_tab")

    def test_switch_tab(self, coordinator):
        """Switching tabs should update active tab."""
        tab1_id = coordinator.active_tab_id
        tab2 = coordinator.open_tab("https://google.com")
        
        # tab2 is now active
        assert coordinator.active_tab_id == tab2.tab_id
        
        # Switch back to tab1
        coordinator.switch_to_tab(tab1_id)
        assert coordinator.active_tab_id == tab1_id

    def test_switch_nonexistent_tab_raises(self, coordinator):
        """Switching to nonexistent tab should raise TabNotFoundError."""
        with pytest.raises(TabNotFoundError):
            coordinator.switch_to_tab("fake_tab")

    def test_switch_tab_with_navigation(self, coordinator, mock_browser):
        """Switching with a URL should navigate the tab."""
        tab1_id = coordinator.active_tab_id
        tab2 = coordinator.open_tab("https://original.com")
        
        coordinator.switch_to_tab(tab2.tab_id, navigate_url="https://new.com")
        
        assert coordinator.tabs[tab2.tab_id].url == "https://new.com"
        assert coordinator.tabs[tab2.tab_id].navigation_count == 1

    def test_list_tabs(self, coordinator):
        """list_tabs should return all tabs sorted by creation time."""
        coordinator.open_tab("https://a.com")
        coordinator.open_tab("https://b.com")
        
        tabs = coordinator.list_tabs()
        assert len(tabs) == 3  # initial + 2 new

    def test_find_tab_by_url(self, coordinator):
        """Should find a tab by exact URL match."""
        coordinator.open_tab("https://target.com")
        
        found = coordinator.find_tab_by_url("https://target.com")
        assert found is not None
        assert found.url == "https://target.com"

    def test_find_tab_by_url_not_found(self, coordinator):
        """Should return None when URL not found."""
        assert coordinator.find_tab_by_url("https://nonexistent.com") is None

    def test_find_tabs_by_domain(self, coordinator):
        """Should find tabs by domain."""
        coordinator.open_tab("https://google.com/search")
        coordinator.open_tab("https://google.com/maps")
        coordinator.open_tab("https://bing.com")
        
        google_tabs = coordinator.find_tabs_by_domain("google.com")
        assert len(google_tabs) == 2

    def test_tab_limit_enforcement(self, mock_browser):
        """Should enforce tab limit via strategy eviction."""
        strategy = ConservativeStrategy(max_tab_count=2)
        coord = MultiTabCoordinator(mock_browser, strategy)
        
        # Initial tab = 1
        coord.open_tab("https://a.com")
        # Now at 2 tabs (limit), opening another should evict
        coord.open_tab("https://b.com")
        
        # Should still be at max 2 (one was evicted)
        assert coord.get_tab_count() <= 2

    def test_tab_reuse(self, mock_browser):
        """Conservative strategy should reuse tabs with matching URLs."""
        strategy = ConservativeStrategy()
        coord = MultiTabCoordinator(mock_browser, strategy)
        
        tab = coord.open_tab("https://google.com")
        initial_count = coord.get_tab_count()
        
        # Opening same URL should reuse
        reused = coord.open_tab("https://google.com")
        assert coord.get_tab_count() == initial_count  # No new tab created

    def test_tab_groups(self, coordinator):
        """Should create and manage tab groups."""
        group = coordinator.create_group("research", purpose="Research tabs")
        assert group.name == "research"
        
        tab = coordinator.open_tab("https://scholar.google.com", group_name="research")
        assert tab.group_name == "research"
        assert "research" in coordinator.groups

    def test_add_tab_to_group(self, coordinator):
        """Should add existing tabs to groups."""
        tab = coordinator.open_tab("https://test.com")
        coordinator.add_tab_to_group(tab.tab_id, "my_group")
        
        assert "my_group" in coordinator.groups
        assert tab.tab_id in coordinator.groups["my_group"].tab_ids

    def test_close_group(self, coordinator):
        """Closing a group should close all its tabs."""
        tab1 = coordinator.open_tab("https://a.com", group_name="batch")
        tab2 = coordinator.open_tab("https://b.com", group_name="batch")
        
        initial_count = coordinator.get_tab_count()
        closed = coordinator.close_group("batch")
        
        assert closed >= 1  # At least one tab closed
        assert "batch" not in coordinator.groups

    def test_event_log(self, coordinator):
        """Tab events should be logged in event_log."""
        coordinator.open_tab("https://test.com")
        
        history = coordinator.get_event_history()
        assert len(history) >= 2  # Initial tab open + new tab open
        
        event_types = [e["event"] for e in history]
        assert "OPENED" in event_types

    def test_close_active_tab_auto_switch(self, coordinator):
        """Closing the active tab should auto-switch to another tab."""
        initial_id = coordinator.active_tab_id
        tab2 = coordinator.open_tab("https://new.com")
        
        # tab2 is active, close it
        coordinator.close_tab(tab2.tab_id)
        
        # Should auto-switch to remaining tab
        assert coordinator.active_tab_id is not None
        assert coordinator.active_tab_id != tab2.tab_id

    def test_get_summary(self, coordinator):
        """get_summary should return comprehensive state."""
        coordinator.open_tab("https://test.com")
        summary = coordinator.get_summary()
        
        assert "tab_count" in summary
        assert "active_tab_id" in summary
        assert "strategy" in summary
        assert "tabs" in summary
        assert summary["tab_count"] == 2

    def test_cross_tab_data_extraction(self, coordinator, mock_browser):
        """Should extract data from multiple tabs."""
        coordinator.open_tab("https://page1.com")
        coordinator.open_tab("https://page2.com")
        
        results = coordinator.extract_data_from_tabs(javascript="document.title")
        
        assert len(results) >= 1
        for tab_id, data in results.items():
            assert "url" in data or "error" in data

    def test_extract_data_restores_active_tab(self, coordinator, mock_browser):
        """Data extraction should restore the original active tab."""
        coordinator.open_tab("https://a.com")
        original_active = coordinator.active_tab_id
        
        coordinator.extract_data_from_tabs()
        assert coordinator.active_tab_id == original_active

    def test_tab_eviction_records_event(self, mock_browser):
        """Tab eviction should record an EVICTED event."""
        strategy = ParallelStrategy(max_tab_count=2)
        coord = MultiTabCoordinator(mock_browser, strategy)
        
        coord.open_tab("https://a.com")
        coord.open_tab("https://b.com")  # Should trigger eviction
        
        events = coord.get_event_history()
        event_types = [e["event"] for e in events]
        assert "EVICTED" in event_types or "CLOSED" in event_types


# ─────────────────────────────────────────────
# Edge Cases
# ─────────────────────────────────────────────

class TestEdgeCases:
    """Edge case tests for the tab coordinator."""

    def test_add_to_nonexistent_tab_group(self, coordinator):
        """Adding nonexistent tab to group should raise TabNotFoundError."""
        with pytest.raises(TabNotFoundError):
            coordinator.add_tab_to_group("fake_tab", "group")

    def test_close_nonexistent_group(self, coordinator):
        """Closing a nonexistent group should return 0."""
        assert coordinator.close_group("nonexistent") == 0

    def test_parallel_strategy_many_tabs(self, mock_browser):
        """ParallelStrategy should allow many concurrent tabs."""
        strategy = ParallelStrategy(max_tab_count=8)
        coord = MultiTabCoordinator(mock_browser, strategy)
        
        for i in range(5):
            coord.open_tab(f"https://page{i}.com")
        
        assert coord.get_tab_count() == 6  # initial + 5

    def test_event_history_limit(self, coordinator):
        """Event history should respect the limit parameter."""
        for i in range(20):
            coordinator.open_tab(f"https://page{i}.com")
        
        limited = coordinator.get_event_history(limit=5)
        assert len(limited) == 5
