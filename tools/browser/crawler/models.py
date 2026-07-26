"""Data Transfer Objects and Data Models for the Web Crawling Subsystem.

This module provides `CrawlNode`, `CrawlStats`, and `CrawlResult` models to represent
crawled page nodes, crawl telemetry statistics, and link lineage graphs.
"""

from dataclasses import dataclass, field
import time
from typing import List, Dict, Any, Optional

from tools.browser.models.page import PageState


@dataclass
class CrawlNode:
    """Represents a single visited page node within the crawl graph.

    Attributes:
        url (str): Resolved URL of the crawled webpage.
        depth (int): Depth level from the initial seed URL.
        parent_url (Optional[str]): Parent URL that linked to this node.
        page_state (Optional[PageState]): Extracted PageState DTO.
        status_code (int): HTTP response status code.
        timestamp (float): UNIX timestamp when node was fetched.
    """

    url: str
    depth: int = 0
    parent_url: Optional[str] = None
    page_state: Optional[PageState] = None
    status_code: int = 200
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert CrawlNode to serializable dictionary format."""
        return {
            "url": self.url,
            "depth": self.depth,
            "parent_url": self.parent_url,
            "status_code": self.status_code,
            "title": self.page_state.metadata.title if self.page_state else "",
            "summary": self.page_state.get_summary(200) if self.page_state else "",
            "timestamp": self.timestamp,
        }


@dataclass
class CrawlStats:
    """Execution metrics and statistics for a crawling job.

    Attributes:
        start_time (float): UNIX start timestamp.
        end_time (float): UNIX completion timestamp.
        total_duration_seconds (float): Execution duration in seconds.
        total_pages_crawled (int): Total count of fetched pages.
        failed_urls_count (int): Number of URLs that encountered errors.
        robots_disallowed_count (int): Number of URLs skipped due to robots.txt.
        documents_collected_count (int): Count of discovered research documents.
    """

    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    total_duration_seconds: float = 0.0
    total_pages_crawled: int = 0
    failed_urls_count: int = 0
    robots_disallowed_count: int = 0
    documents_collected_count: int = 0

    def finalize(self) -> None:
        """Calculate final execution metrics upon crawl completion."""
        self.end_time = time.time()
        self.total_duration_seconds = round(self.end_time - self.start_time, 2)


@dataclass
class CrawlResult:
    """Aggregated output model representing a completed web crawl.

    Attributes:
        seed_url (str): Initial seed URL.
        nodes (List[CrawlNode]): List of all crawled page nodes.
        stats (CrawlStats): Crawl execution statistics.
        link_graph (Dict[str, List[str]]): Map of parent URLs to discovered child links.
    """

    seed_url: str
    nodes: List[CrawlNode] = field(default_factory=list)
    stats: CrawlStats = field(default_factory=CrawlStats)
    link_graph: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert CrawlResult to serializable dictionary representation for AI agents."""
        return {
            "seed_url": self.seed_url,
            "total_pages": len(self.nodes),
            "stats": {
                "duration_seconds": self.stats.total_duration_seconds,
                "failed_urls": self.stats.failed_urls_count,
                "robots_disallowed": self.stats.robots_disallowed_count,
                "documents_collected": self.stats.documents_collected_count,
            },
            "nodes": [node.to_dict() for node in self.nodes],
            "link_graph": self.link_graph,
        }
