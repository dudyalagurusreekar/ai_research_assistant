"""End-to-End test for Academic Report Generation with Citations and Charting."""

import pytest

from core.collaboration import SharedWorkspace
from core.workflow.components.citation_manager import CitationManager
from core.workflow.components.goal_analyzer import ResearchGoalAnalyzer
from core.workflow.components.question_generator import ResearchQuestionGenerator
from core.workflow.components.report_composer import ReportComposer
from core.workflow.models.citation import CitationStyle
from core.workflow.models.evidence import EvidenceRecord, EvidenceSourceType


def test_e2e_full_academic_report_generation():
    analyzer = ResearchGoalAnalyzer()
    q_gen = ResearchQuestionGenerator()
    cm = CitationManager()
    composer = ReportComposer()

    goal = analyzer.analyze_goal("Compare Transformer and Mamba LLM Architectures")
    questions = q_gen.generate_questions(goal)

    workspace = SharedWorkspace()
    workspace.set("chart_svg", "<svg><text>Benchmark SVG</text></svg>", artifact_type="text")

    ev1 = EvidenceRecord(
        question_id=questions[0].question_id,
        content="Transformer architecture uses multi-head self-attention.",
        source_type=EvidenceSourceType.LITERATURE,
        source_name="Vaswani et al.",
        source_url="https://arxiv.org/abs/1706.03762",
    )
    citations = cm.extract_citations_from_evidence([ev1])

    report = composer.compose_report(
        goal=goal,
        questions=questions,
        evidence=[ev1],
        conflicts=[],
        citations=citations,
        workspace=workspace,
    )

    assert "Autonomous Research Report" in report.title
    assert "References & Bibliography" in report.markdown_content
    assert "<svg>" in report.markdown_content
