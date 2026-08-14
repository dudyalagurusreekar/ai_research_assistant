"""Learning Engine Integration Bridge for Sprint 11 Browser Automation Platform."""

import logging
from typing import Any, Dict, Optional
from core.learning import ContinuousLearningEngine, get_learning_engine
from tools.browser.platform.models import ActionResult

logger = logging.getLogger("Tools.Browser.Integration.LearningIntegration")


class LearningBrowserBridge:
    """Connects Browser Automation Platform performance, selector stability, and domain success rates to ContinuousLearningEngine."""

    def __init__(self, learning_engine: Optional[ContinuousLearningEngine] = None) -> None:
        self.learning_engine = learning_engine or get_learning_engine()

    def record_experience(self, domain: str, action_type: str, result: ActionResult) -> None:
        """Record domain interaction success and latency into Experience Engine memory."""
        experience_data = {
            "domain": domain,
            "action_type": action_type,
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error,
        }

        try:
            if hasattr(self.learning_engine, "record_experience"):
                self.learning_engine.record_experience(experience_data)
            logger.info(f"Recorded browser experience for domain '{domain}' (success={result.success}).")
        except Exception as e:
            logger.warning(f"Failed to record experience in LearningEngine: {e}")
