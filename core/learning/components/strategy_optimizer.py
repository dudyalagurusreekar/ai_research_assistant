"""StrategyOptimizer for synthesizing experience insights into actionable strategy recommendations."""

from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from core.learning.models.context import (
    StrategyRecommendation,
    PatternInsight,
    ExperienceRecord,
    ExperienceOutcome,
)
from core.learning.components.experience_store import ExperienceStore
from core.learning.components.pattern_analyzer import PatternAnalyzer
from core.learning.components.tool_performance_db import ToolPerformanceDatabase
from core.learning.components.provider_performance_db import ProviderPerformanceDatabase

logger = get_logger("StrategyOptimizer")


class StrategyOptimizer:
    """Synthesizes historical patterns, tool performance, and provider reliability to formulate strategy recommendations."""

    def __init__(
        self,
        experience_store: ExperienceStore,
        pattern_analyzer: PatternAnalyzer,
        tool_db: ToolPerformanceDatabase,
        provider_db: ProviderPerformanceDatabase,
    ):
        self.store = experience_store
        self.analyzer = pattern_analyzer
        self.tool_db = tool_db
        self.provider_db = provider_db

    def recommend_strategy(
        self, query: str, intent: Optional[str] = None, candidate_tools: Optional[List[str]] = None
    ) -> StrategyRecommendation:
        """Formulates ranked strategy recommendations for an incoming query."""
        if candidate_tools is None:
            candidate_tools = [
                "search_tool", "browser_tool", "document_tool",
                "code_tool", "memory_tool", "vision_tool", "report_tool", "python_interpreter"
            ]

        rec = StrategyRecommendation(query=query, intent=intent)

        # 1. Look up similar past records
        similar = self.store.find_similar_records(query, intent=intent, limit=5)
        if similar:
            successes = [r for r in similar if r.outcome == ExperienceOutcome.SUCCESS]
            rec.historical_success_probability = len(successes) / len(similar)
            rec.confidence = min(len(similar) / 5.0, 1.0)

            # Recommend tools used in successful similar queries
            rec_tools_set = set()
            for r in successes:
                rec_tools_set.update(r.selected_tools)
            
            # Rank recommended tools by tool performance database
            if rec_tools_set:
                rec.recommended_tools = self.tool_db.rank_tools(list(rec_tools_set))
        
        # 2. Consult pattern analyzer for intent-level insights
        if intent:
            insight = self.analyzer.analyze_intent_patterns(intent)
            if insight:
                rec.recommended_max_waves = insight.suggested_wave_count
                if not rec.recommended_tools and insight.optimal_tools:
                    rec.recommended_tools = self.tool_db.rank_tools(insight.optimal_tools)

                if insight.common_failure_modes:
                    rec.risk_warnings = insight.common_failure_modes
                
                rec.insight_summary = (
                    f"Intent '{intent}' pattern derived from {insight.sample_count} historical tasks "
                    f"with {insight.avg_success_rate * 100:.1f}% success rate."
                )

        # 3. If no specific tool recommendations, fallback to ranking candidate tools
        if not rec.recommended_tools:
            rec.recommended_tools = self.tool_db.rank_tools(candidate_tools[:3])

        # 4. Recommend preferred providers based on provider DB reliability
        all_providers = ["gemini/gemini-2.5-flash", "gemini/gemini-3-flash-preview", "ollama/phi3:latest", "openai/gpt-4o"]
        rec.preferred_providers = self.provider_db.rank_providers(all_providers)

        logger.info(f"Generated StrategyRecommendation for query '{query[:40]}...': {len(rec.recommended_tools)} tools recommended, confidence={rec.confidence:.2f}")
        return rec
