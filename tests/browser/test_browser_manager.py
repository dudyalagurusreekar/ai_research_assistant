"""Unit tests for Browser Manager & Security Guard."""

import asyncio
import pytest
from core.browser.browser_manager import BrowserManager
from core.browser.navigation_engine import NavigationEngine
from core.browser.security_guard import BrowserSecurityGuard
from core.browser.models import BrowserSessionConfig, WorkflowStep


def test_browser_security_guard_domain_validation():
    guard = BrowserSecurityGuard(blocked_domains=["malicious.com"])
    assert guard.validate_url("https://ncbi.nlm.nih.gov/pubmed") is True

    with pytest.raises(ValueError, match="restricted"):
        guard.validate_url("https://malicious.com/exploit")


def test_browser_security_guard_captcha_forbidden():
    guard = BrowserSecurityGuard()
    step = WorkflowStep(step_id="s1", action_type="TYPE", selector="#captcha-input", value="bypass_captcha")
    
    with pytest.raises(PermissionError, match="CAPTCHA"):
        guard.validate_action(step)


def test_browser_manager_session_lifecycle():
    async def _test():
        manager = BrowserManager()
        cfg = BrowserSessionConfig(session_id="bs_test_01", user_id="usr_01", browser_type="chromium")
        
        session = await manager.create_session(cfg)
        assert session["session_id"] == "bs_test_01"
        assert session["is_active"] is True

        retrieved = manager.get_session("bs_test_01")
        assert retrieved is not None

        await manager.close_session("bs_test_01")
        assert manager.get_session("bs_test_01") is None

    asyncio.run(_test())


def test_navigation_engine():
    async def _test():
        nav = NavigationEngine()
        session = {"session_id": "bs_nav_01", "page": None, "current_url": "about:blank", "history": []}
        
        meta = await nav.navigate(session, "https://nature.com/articles/genetics")
        assert meta.url == "https://nature.com/articles/genetics"
        assert meta.status_code == 200

    asyncio.run(_test())
