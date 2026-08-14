"""PatternAnalyzer for identifying execution trends, optimal tool pairs, and anti-patterns."""

from typing import List, Dict, Any, Optional
from collections import Counter
from utils.logger import get_logger
from core.learning.models.context import ExperienceRecord, PatternInsight, ExperienceOutcome
from core.learning.components.experience_store import ExperienceStore

logger = get_logger("PatternAnalyzer")


class PatternAnalyzer:
    """Analyzes historical experience records to extract domain insights and execution patterns."""

    def __init__(self, experience_store: ExperienceStore):
        self.store = experience_store

    def analyze_intent_patterns(self, intent: str) -> Optional[PatternInsight]:
        """Analyzes historical records for a specific intent category."""
        records = self.store.get_records_by_intent(intent)
        if not records:
            return None

        total_records = len(records)
        successful = [r for r in records if r.outcome == ExperienceOutcome.SUCCESS]
        success_rate = len(successful) / total_records if total_records > 0 else 0.0

        # Frequency count of selected tools in successful runs
        tool_counter = Counter()
        for r in successful:
            for t in r.selected_tools:
                tool_counter[t] += 1

        # Most common parallel waves count
        wave_counter = Counter([r.parallel_waves for r in successful])
        suggested_waves = wave_counter.most_common(1)[0][0] if wave_counter else 2

        # Extract common failure error messages
        failures = [r for r in records if r.outcome != ExperienceOutcome.SUCCESS]
        failure_modes = []
        for r in failures:
            failure_modes.extend(r.error_logs)

        # Calculate top recommended tools (used in at least 30% of successful runs)
        optimal_tools = [
            t for t, count in tool_counter.most_common()
            if (count / max(1, len(successful))) >= 0.3
        ]

        pattern_id = f"pat_{intent.lower()}"
        insight = PatternInsight(
            pattern_id=pattern_id,
            intent=intent,
            sample_count=total_records,
            optimal_tools=optimal_tools,
            suggested_wave_count=suggested_waves,
            avg_success_rate=success_rate,
            common_failure_modes=failure_modes[:5],
            confidence=min(total_records / 5.0, 1.0),
        )
        return insight

    def get_tool_co_occurrence(self) -> Dict[str, Dict[str, int]]:
        """Calculates co-occurrence matrix of tools across successful historical workflows."""
        co_matrix: Dict[str, Dict[str, int]] = {}
        records = [r for r in self.store.list_records() if r.outcome == ExperienceOutcome.SUCCESS]

        for r in records:
            tools = r.selected_tools
            for i in range(len(tools)):
                t1 = tools[i]
                if t1 not in co_matrix:
                    co_matrix[t1] = {}
                for j in range(i + 1, len(tools)):
                    t2 = tools[j]
                    co_matrix[t1][t2] = co_matrix[t1].get(t2, 0) + 1
                    if t2 not in co_matrix:
                        co_matrix[t2] = {}
                    co_matrix[t2][t1] = co_matrix[t2].get(t1, 0) + 1

        return co_matrix
