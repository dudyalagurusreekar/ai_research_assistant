"""Research Question Generator — Generates hypothesis-driven sub-questions targeting specialized roles."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.collaboration.models.agent_info import AgentRole
from core.workflow.models.goal import GoalDomain, ResearchGoal
from core.workflow.models.question import QuestionPriority, QuestionStatus, ResearchQuestion
from utils.logger import get_logger

logger = get_logger("ResearchQuestionGenerator")


class ResearchQuestionGenerator:
    """Generates structured sub-questions with assigned target roles and hypotheses based on ResearchGoal."""

    def generate_questions(self, goal: ResearchGoal) -> List[ResearchQuestion]:
        """Decompose ResearchGoal into prioritized sub-questions."""
        questions: List[ResearchQuestion] = []
        raw = goal.raw_query.lower()

        # 1. Literature / Factual Research Question
        q_lit = ResearchQuestion(
            question_text=f"What are the foundational principles, state-of-the-art literature, and primary findings regarding '{goal.title}'?",
            hypothesis=f"Literature provides documented theoretical and empirical benchmarks for {goal.title}.",
            target_role=AgentRole.RESEARCH,
            required_capabilities=["web_search", "lit_synthesis"],
            priority=QuestionPriority.HIGH,
            execution_wave=0,
        )
        questions.append(q_lit)

        # 2. Data / Quantitative Benchmark Question (if relevant or multi-stage)
        if goal.domain in (GoalDomain.DATA_ANALYTICS, GoalDomain.COMPUTER_SCIENCE) or "data" in raw or "benchmark" in raw or "compare" in raw:
            q_data = ResearchQuestion(
                question_text=f"What are the quantitative statistical metrics, dataset profiles, and empirical performance trends for '{goal.title}'?",
                hypothesis=f"Quantitative analysis reveals measurable performance gains and statistical trends.",
                target_role=AgentRole.DATA,
                required_capabilities=["data_profiling", "visualization", "statistical_analysis"],
                priority=QuestionPriority.HIGH,
                execution_wave=0,  # Parallel with research wave
            )
            questions.append(q_data)

        # 3. Code Implementation Question (if code requested or technical)
        if "code" in raw or "implement" in raw or "algorithm" in raw or goal.domain == GoalDomain.COMPUTER_SCIENCE:
            q_code = ResearchQuestion(
                question_text=f"What algorithm or Python implementation can verify the execution logic for '{goal.title}'?",
                hypothesis=f"Algorithmic Python execution validates correctness in a sandboxed environment.",
                target_role=AgentRole.CODE,
                required_capabilities=["code_generation", "safe_execution"],
                priority=QuestionPriority.NORMAL,
                dependencies=[q_lit.question_id],
                execution_wave=1,
            )
            questions.append(q_code)

        # 4. Report Writing Question
        q_write = ResearchQuestion(
            question_text=f"How can multi-agent research findings, quantitative metrics, and code implementations be synthesized into a structured analytical report for '{goal.title}'?",
            hypothesis=f"Synthesized prose, data tables, and SVG charts provide a complete analytical research report.",
            target_role=AgentRole.WRITER,
            required_capabilities=["report_generation", "content_synthesis"],
            priority=QuestionPriority.HIGH,
            dependencies=[q.question_id for q in questions],
            execution_wave=2,
        )
        questions.append(q_write)

        # 5. Quality Audit & Review Question
        q_rev = ResearchQuestion(
            question_text=f"Are all facts, dataset metrics, code blocks, and conclusions in the research report for '{goal.title}' verified, accurate, and free of contradictions?",
            hypothesis=f"Reviewer audit validates high quality score and verifies factual consistency.",
            target_role=AgentRole.REVIEWER,
            required_capabilities=["quality_assurance", "code_review", "fact_checking"],
            priority=QuestionPriority.CRITICAL,
            dependencies=[q_write.question_id],
            execution_wave=3,
        )
        questions.append(q_rev)

        logger.info(f"ResearchQuestionGenerator generated {len(questions)} prioritized sub-questions for '{goal.title}'")
        return questions
