import pytest
from tools.browser.recovery.strategies import CaptchaRecoveryStrategy
from tools.browser.recovery.base import RecoveryContext
from tools.browser.models.response import ActionResult
from tools.browser.recovery.classifier import ErrorCategory

class MockJSResult:
    def __init__(self, success, data):
        self.success = success
        self.data = data

class MockBrowser:
    def execute_javascript(self, script):
        # Mock finding a captcha
        if "reCAPTCHA" in script or "cf-turnstile" in script:
            return MockJSResult(True, "CAPTCHA element found.")
        return MockJSResult(False, None)

def test_captcha_recovery_strategy():
    strategy = CaptchaRecoveryStrategy()
    
    browser = MockBrowser()
    failed_result = ActionResult(
        url="https://example.com",
        title="Just a moment...",
        success=False,
        errors=["Timeout"]
    )
    
    ctx = RecoveryContext(
        browser=browser,
        action_dict={"action": "click", "selector": "#test"},
        failed_result=failed_result,
        error_category=ErrorCategory.CAPTCHA_INTERRUPTION,
        error_message="Timeout on page"
    )
    
    result = strategy.attempt(ctx)
    
    assert not result.success
    assert result.strategy_used == "captcha_recovery"
    
    # Check that it returns an ActionResult with a planner feedback
    assert not result.action_result.success
    assert "CAPTCHA blocked access" in result.action_result.errors[-1]
    assert "planner_feedback" in result.action_result.data
