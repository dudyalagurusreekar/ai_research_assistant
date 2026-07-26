"""Completion Detector Pipeline Coordinator.

Runs the strategy check chain, aggregates confidence, overrides states for blocks,
and returns the final CompletionStatus.
"""

import logging
from typing import Any, Dict, List, Optional

from tools.browser.core.browser import Browser
from tools.browser.detector.base import (
    BaseCompletionStrategy,
    CompletionContext,
    CompletionState,
    CompletionStatus,
    InvalidObjectiveError,
)
from tools.browser.detector.strategies import (
    ArtifactSuccessStrategy,
    ExecutionAnomalyStrategy,
    ObjectiveEvidenceStrategy,
    StateBlockedStrategy,
    UrlRedirectionStrategy,
)

logger = logging.getLogger("CompletionDetector.Pipeline")


class CompletionDetector:
    """Enterprise-grade task completion detector coordinating multi-strategy checks.

    Attributes:
        browser: Active Browser facade.
        strategies: List of active evaluation strategy instances.
        weights: Strategy weights dict for confidence aggregation.
        completed_threshold: Confidence boundary to mark task as COMPLETED.
        uncertain_threshold: Confidence boundary to mark task as UNCERTAIN.
    """

    def __init__(
        self,
        browser: Browser,
        strategies: Optional[List[BaseCompletionStrategy]] = None,
        weights: Optional[Dict[str, float]] = None,
        completed_threshold: float = 0.70,
        uncertain_threshold: float = 0.20,
    ) -> None:
        """Initialize the CompletionDetector.

        Args:
            browser: The active Browser facade.
            strategies: The list of verification strategies.
            weights: The mapping of strategy names to aggregation weights.
            completed_threshold: Threshold to decide COMPLETED.
            uncertain_threshold: Threshold to decide UNCERTAIN.
        """
        self.browser = browser
        self.strategies = strategies or [
            ObjectiveEvidenceStrategy(),
            ArtifactSuccessStrategy(),
            UrlRedirectionStrategy(),
            StateBlockedStrategy(),
            ExecutionAnomalyStrategy(),
        ]
        
        # Default strategy weights
        self.weights = weights or {
            "objective_evidence": 0.50,
            "artifact_success": 0.30,
            "url_redirection": 0.20,
        }
        
        self.completed_threshold = completed_threshold
        self.uncertain_threshold = uncertain_threshold
        self._logger = logger

    def evaluate_completion(
        self,
        objective: str,
        history: List[Dict[str, Any]],
        extracted_artifacts: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CompletionStatus:
        """Run all strategies to determine if the task has met its objective.

        Args:
            objective: Natural language task goal.
            history: List of past actions executed.
            extracted_artifacts: Variables, files, or scraping records.
            metadata: Custom execution state parameters.

        Returns:
            CompletionStatus: Detailed outcome structure.

        Raises:
            InvalidObjectiveError: If the goal is empty or invalid.
        """
        if not objective or not objective.strip():
            raise InvalidObjectiveError("Objective string must be non-empty.")

        ctx = CompletionContext(
            objective=objective,
            browser=self.browser,
            history=history,
            extracted_artifacts=extracted_artifacts or {},
            metadata=metadata or {},
        )

        self._logger.info(f"Completion Detector evaluating objective: '{objective}'")

        individual_results: Dict[str, CompletionStatus] = {}
        
        # Run all strategies
        for strategy in self.strategies:
            try:
                res = strategy.evaluate(ctx)
                individual_results[strategy.name] = res
                self._logger.debug(
                    f"Strategy '{strategy.name}' returned state={res.state.value}, "
                    f"confidence={res.confidence:.2f}"
                )
            except Exception as e:
                self._logger.error(f"Strategy '{strategy.name}' failed: {e}")
                individual_results[strategy.name] = CompletionStatus(
                    CompletionState.INCOMPLETE, 0.0, f"Execution failed: {e}"
                )

        # 1. Hard Overrides (Blocked, Impossible, or Partial blockers)
        blocked_res = individual_results.get("state_blocked")
        if blocked_res and blocked_res.state in [CompletionState.BLOCKED, CompletionState.IMPOSSIBLE] and blocked_res.confidence >= 0.8:
            self._logger.warning(f"Blocking override triggered: {blocked_res.explanation}")
            return blocked_res

        anomaly_res = individual_results.get("execution_anomaly")
        if anomaly_res and anomaly_res.state == CompletionState.IMPOSSIBLE and anomaly_res.confidence >= 0.8:
            self._logger.warning(f"Execution anomaly override triggered: {anomaly_res.explanation}")
            return anomaly_res

        # 2. Weighted Confidence score aggregation
        weighted_score = 0.0
        total_weight = 0.0
        collected_evidence: List[str] = []
        explanations: List[str] = []
        completed_count = 0
        partial_count = 0

        for name, weight in self.weights.items():
            res = individual_results.get(name)
            if res:
                # Add to weighted aggregation
                weighted_score += res.confidence * weight
                total_weight += weight
                
                # Track state indicators
                if res.state == CompletionState.COMPLETED:
                    completed_count += 1
                elif res.state == CompletionState.PARTIAL:
                    partial_count += 1

                if res.explanation:
                    explanations.append(f"{name}: {res.explanation}")
                if res.evidence:
                    collected_evidence.extend(res.evidence)

        # Normalize score
        final_confidence = (weighted_score / total_weight) if total_weight > 0.0 else 0.0

        # 3. Determine overall CompletionState based on score and counts
        if final_confidence >= self.completed_threshold or completed_count >= 2:
            final_state = CompletionState.COMPLETED
            explanation = "Objective has been satisfied according to verification signals."
        elif completed_count == 1 or partial_count >= 1 or final_confidence >= self.uncertain_threshold:
            # High probability but not fully verified, or partial signs
            final_state = CompletionState.UNCERTAIN
            explanation = "Objective appears satisfied but is uncertain; requires visual or user verification."
        elif final_confidence > 0.15:
            final_state = CompletionState.PARTIAL
            explanation = "Task is partially completed; some goals satisfied, others pending."
        else:
            final_state = CompletionState.INCOMPLETE
            explanation = "Objective is incomplete. Active steps required."

        # Capping logic: if objective explicitly requires file downloads/scraping,
        # but the artifact is missing, cap COMPLETED -> UNCERTAIN.
        implies_download = any(w in objective.lower() for w in ["download", "save", "pdf", "csv", "xlsx", "zip", "export"])
        implies_extraction = any(w in objective.lower() for w in ["extract", "scrape", "get details", "list", "collect"])
        artifact_res = individual_results.get("artifact_success")
        if (implies_download or implies_extraction) and (not artifact_res or artifact_res.state != CompletionState.COMPLETED):
            if final_state == CompletionState.COMPLETED:
                final_state = CompletionState.UNCERTAIN
                explanation += " | Capped to UNCERTAIN because expected download/extraction artifacts were not fully verified."

        if explanations:
            explanation += " Details: " + " | ".join(explanations)

        self._logger.info(
            f"Completion detection finished: state={final_state.value}, "
            f"confidence={final_confidence:.2%}"
        )

        return CompletionStatus(
            state=final_state,
            confidence=final_confidence,
            explanation=explanation,
            evidence=collected_evidence,
            details={
                "individual_results": {k: v.to_dict() for k, v in individual_results.items()},
                "completed_count": completed_count,
                "partial_count": partial_count,
            },
        )
