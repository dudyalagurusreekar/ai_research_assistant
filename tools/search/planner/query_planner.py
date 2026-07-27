"""Query Planner for normalizing search terms and selecting target providers."""

import re
from typing import Dict, List, Any, Optional
from tools.search.models.search_models import SearchQuery, QueryIntent
from tools.search.interfaces.provider import IQueryPlanner
from infrastructure.logging.logger import StructuredLogger


class QueryPlanner(IQueryPlanner):
    """Analyzes raw search strings, detects query intent, and constructs optimized SearchQuery plans."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("QueryPlanner")

    async def plan_query(self, raw_query: str, options: Optional[Dict[str, Any]] = None) -> SearchQuery:
        """Analyze raw query string and return structured SearchQuery."""
        opts = options or {}
        cleaned_query = raw_query.strip()
        
        # 1. Detect file type filters (e.g., filetype:pdf, ext:docx)
        file_types = []
        filetype_matches = re.findall(r"(?:filetype|ext):([a-zA-Z0-9]+)", cleaned_query, re.IGNORECASE)
        if filetype_matches:
            file_types = [ft.lower() for ft in filetype_matches]
            cleaned_query = re.sub(r"(?:filetype|ext):[a-zA-Z0-9]+", "", cleaned_query, flags=re.IGNORECASE).strip()

        # 2. Detect site/domain filters (e.g., site:github.com, site:arxiv.org)
        domain_filters = []
        site_matches = re.findall(r"site:([a-zA-Z0-9.-]+)", cleaned_query, re.IGNORECASE)
        if site_matches:
            domain_filters = [d.lower() for d in site_matches]
            cleaned_query = re.sub(r"site:[a-zA-Z0-9.-]+", "", cleaned_query, flags=re.IGNORECASE).strip()

        normalized_query = " ".join(cleaned_query.split())

        # 3. Detect intent
        intent = self._detect_intent(raw_query, opts)

        # 4. Target provider selection based on intent
        target_providers = opts.get("target_providers", [])
        if not target_providers:
            target_providers = self._select_providers_for_intent(intent)

        query_plan = SearchQuery(
            raw_query=raw_query,
            normalized_query=normalized_query or raw_query,
            intent=intent,
            target_providers=target_providers,
            domain_filters=domain_filters,
            file_type_filters=file_types,
            max_results=opts.get("max_results", 10),
            timeout_seconds=opts.get("timeout_seconds", 15.0),
            enable_cache=opts.get("enable_cache", True),
            custom_params=opts,
        )

        self._logger.debug(f"Planned query '{raw_query}': intent={intent.value}, providers={target_providers}")
        return query_plan

    def _detect_intent(self, query: str, options: Dict[str, Any]) -> QueryIntent:
        """Infer search intent from query string content and options."""
        if "intent" in options and isinstance(options["intent"], QueryIntent):
            return options["intent"]
            
        q_lower = query.lower()

        academic_terms = ["arxiv", "paper", "doi", "journal", "publication", "abstract", "citation", "pubmed", "openalex"]
        if any(term in q_lower for term in academic_terms):
            return QueryIntent.ACADEMIC

        code_terms = ["github", "repo", "repository", "code", "commit", "pull request", "function", "def "]
        if any(term in q_lower for term in code_terms):
            return QueryIntent.CODE_GITHUB

        local_terms = ["local", "document", "my files", "ingested", "processed", "pdf:"]
        if any(term in q_lower for term in local_terms):
            return QueryIntent.LOCAL_DOCUMENT

        return QueryIntent.GENERAL_WEB

    def _select_providers_for_intent(self, intent: QueryIntent) -> List[str]:
        """Map intent to default provider strategy names."""
        if intent == QueryIntent.ACADEMIC:
            return ["academic_search", "web_search"]
        elif intent == QueryIntent.CODE_GITHUB:
            return ["github_search", "web_search"]
        elif intent == QueryIntent.LOCAL_DOCUMENT:
            return ["local_document_search"]
        elif intent == QueryIntent.HYBRID:
            return ["web_search", "academic_search", "local_document_search"]
        return ["web_search"]
