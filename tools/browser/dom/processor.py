"""DOM Processor for pruning HTML, extracting interactive maps, hash calculation, and token budgeting."""

import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class ProcessedDOM:
    """Output container for processed DOM content."""

    simplified_text: str
    interactive_elements: List[str]
    dom_hash: str
    token_count: int


class DOMProcessor:
    """Simplifies HTML, extracts interactive nodes, detects mutations, and enforces token limits."""

    def __init__(self, max_token_budget: int = 1500) -> None:
        self.max_token_budget = max_token_budget

    def compute_hash(self, html: str) -> str:
        """Compute SHA256 version hash for DOM change detection."""
        return hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]

    def process(self, html: str) -> ProcessedDOM:
        """Prune HTML markup, extract interactive map, compute hash, and enforce token budget."""
        dom_hash = self.compute_hash(html)

        # Remove scripts, styles, comments
        clean = re.sub(r"<(script|style|svg|path).*?>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<!--.*?-->", "", clean, flags=re.DOTALL)

        # Extract interactive elements (inputs, buttons, anchors)
        interactive: List[str] = []
        element_pattern = re.compile(r"<(a|button|input|textarea|select)\b[^>]*>(.*?)</\1>|<input\b[^>]*>", re.IGNORECASE | re.DOTALL)

        for i, match in enumerate(element_pattern.finditer(clean), 1):
            tag_str = match.group(0).strip()
            # Truncate long inner HTML
            tag_str = re.sub(r"\s+", " ", tag_str)[:120]
            interactive.append(f"[{i}] {tag_str}")

        # Strip remaining tags to get clean text
        text_content = re.sub(r"<[^>]+>", " ", clean)
        text_content = re.sub(r"\s+", " ", text_content).strip()

        # Build simplified map
        simplified_map = f"DOM Hash: {dom_hash}\nInteractive Elements ({len(interactive)}):\n" + "\n".join(interactive[:30])
        simplified_map += f"\n\nText Content Excerpt:\n{text_content[:1000]}"

        # Budget enforcement
        token_count = max(1, len(simplified_map) // 4)
        if token_count > self.max_token_budget:
            char_limit = self.max_token_budget * 4
            simplified_map = simplified_map[:char_limit] + "\n...[Truncated by DOM Token Budget]"
            token_count = self.max_token_budget

        return ProcessedDOM(
            simplified_text=simplified_map,
            interactive_elements=interactive,
            dom_hash=dom_hash,
            token_count=token_count,
        )
