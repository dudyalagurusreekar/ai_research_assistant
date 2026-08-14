"""Integration tests for Planner → Knowledge Graph concept enrichment."""

import pytest

from core.knowledge_graph import KnowledgeGraphEngine, PlannerKnowledgeIntegration
from core.planner.models.context import PlannerContext


def test_planner_knowledge_integration():
    kg_engine = KnowledgeGraphEngine()
    kg_engine.ingest_text("Transformer architectures optimize multi-step research DAG generation.")

    integration = PlannerKnowledgeIntegration(kg_engine)
    planner_ctx = PlannerContext(user_query="Transformer architectures")

    enriched_ctx = integration.enhance_planner_context(planner_ctx)
    assert any("Transformer" in c for c in enriched_ctx.constraints.stopping_criteria) or any("Transformer" in r for r in enriched_ctx.reasoning_trace)
