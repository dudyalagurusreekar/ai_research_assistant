"""Evidence Aggregator — Multi-source evidence harvesting and provenance tagging."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.workflow.models.evidence import (
    EvidenceConfidence,
    EvidenceRecord,
    EvidenceSourceType,
)
from core.workflow.models.question import ResearchQuestion
from utils.logger import get_logger

logger = get_logger("EvidenceAggregator")


class EvidenceAggregator:
    """Aggregates findings across literature search, workspace, data analytics, knowledge graph, and code execution."""

    def aggregate_evidence(
        self, questions: List[ResearchQuestion], workspace: Any, kg_engine: Optional[Any] = None
    ) -> List[EvidenceRecord]:
        """Harvest evidence from workspace artifacts and Knowledge Graph."""
        evidence_list: List[EvidenceRecord] = []

        for q in questions:
            # 1. Harvest from SharedWorkspace
            if hasattr(workspace, "get"):
                res_sum = workspace.get("research_summary")
                if res_sum:
                    record = EvidenceRecord(
                        question_id=q.question_id,
                        content=str(res_sum),
                        source_type=EvidenceSourceType.LITERATURE,
                        source_name="Literature Research Agent",
                        confidence=EvidenceConfidence.HIGH,
                        confidence_score=0.92,
                        provenance_tags=["agent:research", "workspace:research_summary"],
                    )
                    evidence_list.append(record)

                data_stats = workspace.get("data_stats")
                if data_stats and isinstance(data_stats, dict):
                    record = EvidenceRecord(
                        question_id=q.question_id,
                        content=f"Data Statistics: {data_stats}",
                        source_type=EvidenceSourceType.DATA_ANALYSIS,
                        source_name="Data Intelligence Agent",
                        confidence=EvidenceConfidence.HIGH,
                        confidence_score=0.95,
                        provenance_tags=["agent:data", "workspace:data_stats"],
                    )
                    evidence_list.append(record)

                code_res = workspace.get("code_execution_result")
                if code_res and isinstance(code_res, dict):
                    record = EvidenceRecord(
                        question_id=q.question_id,
                        content=f"Code Execution Output: {code_res.get('stdout', '')}",
                        source_type=EvidenceSourceType.CODE_EXECUTION,
                        source_name="Code Execution Agent",
                        confidence=EvidenceConfidence.HIGH,
                        confidence_score=0.90,
                        provenance_tags=["agent:code", "workspace:code_result"],
                    )
                    evidence_list.append(record)

            # 2. Harvest from Knowledge Graph
            if kg_engine and hasattr(kg_engine, "query"):
                try:
                    res = kg_engine.query(q.question_text)
                    if res and hasattr(res, "matched_nodes") and res.matched_nodes:
                        concepts = ", ".join([n.name for n in res.matched_nodes[:3]])
                        record = EvidenceRecord(
                            question_id=q.question_id,
                            content=f"Knowledge Graph Concepts: {concepts}",
                            source_type=EvidenceSourceType.KNOWLEDGE_GRAPH,
                            source_name="Knowledge Graph Engine",
                            confidence=EvidenceConfidence.HIGH,
                            confidence_score=0.88,
                            provenance_tags=["kg:nodes"],
                        )
                        evidence_list.append(record)
                except Exception as exc:
                    logger.warning(f"Error querying KnowledgeGraph in EvidenceAggregator: {exc}")

        logger.info(f"EvidenceAggregator collected {len(evidence_list)} EvidenceRecord(s)")
        return evidence_list
