"""End-to-End research workflow tests for Sprint 11 Browser Automation Platform."""

import pytest
import asyncio
from tools.browser.platform.engine import BrowserPlatformEngine
from tools.browser.platform.models import BrowserAction, ActionType, ExtractionSchema
from tools.browser.platform.security_layer import SecurityLayer, SecurityAssessmentResult


def test_e2e_autonomous_research_workflow():
    """Simulate a complete multi-step autonomous research session."""
    async def _test():
        engine = BrowserPlatformEngine()
        assert await engine.initialize() is True

        # 1. Step 1: Navigate to target portal
        nav_res = await engine.navigate("https://example.com")
        assert nav_res.success is True

        # 2. Step 2: Build DOM understanding tree
        dom_tree = await engine.get_dom_tree()
        assert dom_tree is not None

        # 3. Step 3: Extract structured data schema
        schema = ExtractionSchema(
            schema_id="articles_schema",
            name="Research Articles",
            fields={"header": "h1"},
        )
        ext_res = await engine.extract_schema(schema)
        assert ext_res.success is True

        # 4. Step 4: Capture screenshot artifact
        screenshot_res = await engine.capture_screenshot()
        assert screenshot_res.success is True
        assert screenshot_res.screenshot_path is not None

        # 5. Step 5: Verify metrics tracking
        metrics = engine.metrics_engine.get_summary()
        assert metrics["total_actions"] >= 2
        assert metrics["success_rate_pct"] == 100.0

        await engine.shutdown()

    asyncio.run(_test())


def test_e2e_security_guardrail_confirmation_gate():
    """Verify security guardrail gate intercepts destructive high-impact action."""
    async def _test():
        confirmed_actions = []

        def _user_confirmation_callback(action: BrowserAction, assessment: SecurityAssessmentResult) -> bool:
            confirmed_actions.append(action)
            return True  # Simulate user approving high-impact action

        security = SecurityLayer(user_confirmation_callback=_user_confirmation_callback)
        engine = BrowserPlatformEngine(security_layer=security)
        await engine.initialize()

        destructive_action = BrowserAction(
            action_type=ActionType.NAVIGATE,
            url="https://example.com/delete-account-confirm",
            text="Delete research dataset permanently",
        )

        res = await engine.execute_action(destructive_action)
        assert res.success is True
        assert len(confirmed_actions) == 1
        assert confirmed_actions[0].action_type == ActionType.NAVIGATE

        await engine.shutdown()

    asyncio.run(_test())
