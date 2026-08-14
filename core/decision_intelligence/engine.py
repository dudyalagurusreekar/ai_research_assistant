"""Master Decision Intelligence & Recommendation Engine for Sprint 13."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.decision_intelligence.components.confidence_engine import ConfidenceEngine
from core.decision_intelligence.components.decision_analyzer import DecisionAnalyzer
from core.decision_intelligence.components.evidence_aggregator import EvidenceAggregator
from core.decision_intelligence.components.option_generator import OptionGenerator
from core.decision_intelligence.components.recommendation_generator import RecommendationGenerator
from core.decision_intelligence.components.risk_assessment import RiskAssessmentEngine
from core.decision_intelligence.components.scenario_simulator import ScenarioSimulator
from core.decision_intelligence.components.tradeoff_analyzer import TradeoffAnalyzer
from core.decision_intelligence.metrics import DecisionMetricsEngine
from core.decision_intelligence.models.decision_request import DecisionRequest
from core.decision_intelligence.models.decision_response import DecisionResponse
from core.decision_intelligence.models.recommendation import DecisionRecommendationReport
from utils.logger import get_logger

logger = get_logger("DecisionIntelligenceEngine")


class DecisionIntelligenceEngine:
    """Master Orchestrator Engine for ARA Sprint 13 Decision Intelligence & Recommendation Engine."""

    def __init__(self, metrics_engine: Optional[DecisionMetricsEngine] = None) -> None:
        self.metrics = metrics_engine or DecisionMetricsEngine()

        # Instantiate 8 modular components
        self.decision_analyzer = DecisionAnalyzer()
        self.option_generator = OptionGenerator()
        self.evidence_aggregator = EvidenceAggregator()
        self.tradeoff_analyzer = TradeoffAnalyzer()
        self.risk_assessment = RiskAssessmentEngine()
        self.scenario_simulator = ScenarioSimulator()
        self.confidence_engine = ConfidenceEngine()
        self.recommendation_generator = RecommendationGenerator()

    def process_decision_request(self, request: DecisionRequest) -> DecisionResponse:
        """Execute complete 8-step decision intelligence analysis pipeline end-to-end."""
        start_time = time.time()
        logger.info(f"Processing DecisionRequest: {request.decision_id} (Query: '{request.user_query[:50]}...')")

        try:
            # Step 1: Decision Analyzer (Extract context, objectives, constraints)
            context = self.decision_analyzer.analyze_context(
                query=request.user_query,
                topic=request.topic,
                domain=request.domain,
                explicit_objectives=request.explicit_objectives,
                explicit_constraints=request.explicit_constraints,
                context_data=request.context_data,
                risk_tolerance=request.risk_tolerance,
                urgency_level=request.urgency_level,
            )

            # Step 2: Option Generator (Synthesize & check constraint feasibility)
            options = self.option_generator.generate_options(
                context=context,
                preset_options=request.preset_options,
            )

            # Step 3: Evidence Aggregator (Aggregate & link evidence items)
            evidence_items = self.evidence_aggregator.aggregate_evidence(
                context=context,
                options=options,
                subsystem_sources=request.context_data,
            )

            # Step 4: Trade-off Analyzer (MCDA scoring, weighted matrix, Pareto frontier)
            tradeoff_matrix = self.tradeoff_analyzer.analyze_tradeoffs(
                context=context,
                options=options,
                evidence_items=evidence_items,
            )

            # Step 5: Risk Assessment Engine (Identify risk factors, severity, mitigations)
            risk_profiles = self.risk_assessment.evaluate_risks(
                context=context,
                options=options,
            )

            # Step 6: Scenario Simulator (Simulate alternative scenarios & weight sensitivity)
            simulation_results = self.scenario_simulator.run_simulations(
                context=context,
                options=options,
                tradeoff_matrix=tradeoff_matrix,
            )

            # Step 7: Confidence Engine (Quantify uncertainty & confidence intervals)
            confidence_assessments = self.confidence_engine.evaluate_confidence(
                options=options,
                evidence_items=evidence_items,
            )

            # Step 8: Recommendation Generator (Synthesize report & human choice boundaries)
            report = self.recommendation_generator.generate_recommendation_report(
                context=context,
                options=options,
                tradeoff_matrix=tradeoff_matrix,
                risk_profiles=risk_profiles,
                simulation_results=simulation_results,
                confidence_assessments=confidence_assessments,
                evidence_items=evidence_items,
            )

            exec_time_ms = round((time.time() - start_time) * 1000.0, 2)

            top_conf = (
                report.top_recommendation.supporting_evidence_count * 0.1
                if report.top_recommendation
                else 0.8
            )
            top_risk = (
                risk_profiles[report.top_recommendation.option_id].overall_risk_score
                if report.top_recommendation and report.top_recommendation.option_id in risk_profiles
                else 1.0
            )

            self.metrics.record_evaluation(
                success=True,
                latency_ms=exec_time_ms,
                option_count=len(options),
                evidence_count=len(evidence_items),
                pareto_count=len(tradeoff_matrix.pareto_frontier_option_ids),
                top_confidence=top_conf,
                top_risk=top_risk,
            )

            response = DecisionResponse(
                request_id=request.decision_id,
                status="success",
                report=report,
                execution_time_ms=exec_time_ms,
            )
            logger.info(f"DecisionRequest {request.decision_id} successfully executed in {exec_time_ms} ms.")
            return response

        except Exception as e:
            exec_time_ms = round((time.time() - start_time) * 1000.0, 2)
            logger.error(f"Error processing DecisionRequest {request.decision_id}: {e}", exc_info=True)
            self.metrics.record_evaluation(success=False, latency_ms=exec_time_ms)
            return DecisionResponse(
                request_id=request.decision_id,
                status="error",
                execution_time_ms=exec_time_ms,
                error_message=str(e),
            )
