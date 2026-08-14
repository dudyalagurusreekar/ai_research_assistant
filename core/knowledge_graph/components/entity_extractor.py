"""Entity Extractor — Extracts typed named entities from text, research papers, code, and structured data."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from core.knowledge_graph.models.node import EntityNode, EntityType
from utils.logger import get_logger

logger = get_logger("EntityExtractor")


class EntityExtractor:
    """Extracts typed entity nodes with confidence scores, aliases, and properties using spaCy NLP + regex fallback."""

    def __init__(self) -> None:
        self._nlp = None
        self._spacy_available = False
        try:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
                self._spacy_available = True
                logger.info("EntityExtractor initialized with spaCy 'en_core_web_sm'")
            except Exception as e:
                # Blank english pipeline fallback
                self._nlp = spacy.blank("en")
                self._spacy_available = True
                logger.info(f"EntityExtractor initialized blank spaCy pipeline: {e}")
        except ImportError:
            logger.info("spaCy module not available; running with rule-based regex extractor")

        # Common domain patterns & keyword indicators
        self._keyword_type_map = {
            "dataset": EntityType.DATASET,
            "data": EntityType.DATASET,
            "corpus": EntityType.DATASET,
            "benchmark": EntityType.DATASET,
            "model": EntityType.MODEL,
            "llm": EntityType.MODEL,
            "agent": EntityType.MODEL,
            "transformer": EntityType.MODEL,
            "method": EntityType.METHOD,
            "algorithm": EntityType.METHOD,
            "technique": EntityType.METHOD,
            "framework": EntityType.CONCEPT,
            "architecture": EntityType.CONCEPT,
            "pipeline": EntityType.CONCEPT,
            "metric": EntityType.METRIC,
            "accuracy": EntityType.METRIC,
            "score": EntityType.METRIC,
            "latency": EntityType.METRIC,
            "speedup": EntityType.METRIC,
            "precision": EntityType.METRIC,
            "recall": EntityType.METRIC,
            "tool": EntityType.TOOL,
            "code": EntityType.CODE_SYMBOL,
            "function": EntityType.CODE_SYMBOL,
            "class": EntityType.CODE_SYMBOL,
            "author": EntityType.AUTHOR,
            "paper": EntityType.DOCUMENT,
            "report": EntityType.DOCUMENT,
        }

        self._spacy_label_map = {
            "PERSON": EntityType.AUTHOR,
            "ORG": EntityType.CONCEPT,
            "GPE": EntityType.LOCATION,
            "LOC": EntityType.LOCATION,
            "PRODUCT": EntityType.TOOL,
            "WORK_OF_ART": EntityType.DOCUMENT,
            "EVENT": EntityType.CONCEPT,
            "DATE": EntityType.CONCEPT,
        }

    def extract_from_text(self, text: str, source_id: str = "text_source") -> List[EntityNode]:
        """Extract typed entities from natural text or research markdown."""
        entities: List[EntityNode] = []
        if not text:
            return entities

        seen: Dict[str, str] = {}

        # 1. spaCy NLP Extraction (if available)
        if self._spacy_available and self._nlp is not None:
            try:
                doc = self._nlp(text[:25000])  # limit length to avoid memory overload
                for ent in getattr(doc, "ents", []):
                    clean_term = ent.text.strip()
                    if len(clean_term) < 2 or clean_term.lower() in ["this", "that", "with", "from", "have", "been"]:
                        continue
                    canon = clean_term.lower()
                    if canon in seen:
                        continue
                    seen[canon] = clean_term

                    spacy_label = ent.label_
                    etype = self._spacy_label_map.get(spacy_label, self._infer_entity_type(clean_term, text))

                    node = EntityNode(
                        name=clean_term,
                        canonical_name=canon,
                        entity_type=etype,
                        confidence_score=0.90,
                        properties={
                            "source_id": source_id,
                            "extracted_by": "spacy",
                            "spacy_label": spacy_label,
                        },
                    )
                    entities.append(node)
            except Exception as err:
                logger.warning(f"spaCy extraction failed: {err}; falling back to regex")

        # 2. Capitalized Proper Nouns & Technical Term Regex Extraction
        pattern = r"\b([A-Z][a-zA-Z0-9_\-\.]{2,}(?:\s+[A-Z][a-zA-Z0-9_\-\.]+)*)\b"
        matches = re.findall(pattern, text)

        for term in matches:
            clean_term = term.strip()
            if len(clean_term) < 3 or clean_term.lower() in [
                "this", "that", "with", "from", "have", "been", "were", "where", "what", "which", "there"
            ]:
                continue

            canon = clean_term.lower()
            if canon in seen:
                continue
            seen[canon] = clean_term

            # Infer entity type
            etype = self._infer_entity_type(clean_term, text)
            node = EntityNode(
                name=clean_term,
                canonical_name=canon,
                entity_type=etype,
                confidence_score=0.85,
                properties={"source_id": source_id, "extracted_by": "regex", "extracted_term": clean_term},
            )
            entities.append(node)

        logger.debug(f"EntityExtractor extracted {len(entities)} entity nodes from text")
        return entities


    def extract_from_structured_data(self, data: Dict[str, Any], source_id: str = "structured_data") -> List[EntityNode]:
        """Extract entity nodes from structured dict records (e.g. data intelligence reports, planner contexts)."""
        entities: List[EntityNode] = []

        for key, val in data.items():
            if isinstance(val, str) and len(val) > 2:
                etype = self._infer_entity_type(key, key)
                node = EntityNode(
                    name=key,
                    canonical_name=key.lower().strip(),
                    entity_type=etype,
                    confidence_score=0.90,
                    properties={"source_id": source_id, "value": str(val)[:200]},
                )
                entities.append(node)
            elif isinstance(val, (int, float)):
                node = EntityNode(
                    name=key,
                    canonical_name=key.lower().strip(),
                    entity_type=EntityType.METRIC,
                    confidence_score=0.95,
                    properties={"source_id": source_id, "metric_value": val},
                )
                entities.append(node)

        return entities

    def _infer_entity_type(self, term: str, context_text: str) -> EntityType:
        """Infer EntityType based on term words and context heuristics."""
        clean_t = term.lower()
        for kw, etype in self._keyword_type_map.items():
            if kw in clean_t:
                return etype

        # Context text check
        for kw, etype in self._keyword_type_map.items():
            if kw in context_text.lower()[:300]:
                return etype

        return EntityType.CONCEPT
