"""DOM Simplifier Engine for AI Browser Planner.

Parses raw HTML, filters out static structure, extracts interactive elements,
and maps them to unique reference IDs and CSS selectors for LLM reasoning.
"""

from typing import List, Dict, Optional
from bs4 import Tag


class InteractiveNode:
    """Representation of a simplified interactive DOM node."""

    def __init__(
        self,
        ref_id: int,
        tag_name: str,
        text: str,
        attributes: Dict[str, str],
        selector: str,
    ) -> None:
        self.ref_id = ref_id
        self.tag_name = tag_name.lower()
        self.text = text.strip()
        self.attributes = attributes
        self.selector = selector

    def to_string(self) -> str:
        """Format node attributes into a single readable line for the LLM."""
        attrs_str = ", ".join(f"{k}: \"{v}\"" for k, v in self.attributes.items() if v)
        text_part = f" \"{self.text}\"" if self.text else ""
        attrs_part = f" ({attrs_str})" if attrs_str else ""
        return f"[{self.ref_id}] {self.tag_name.upper()}{text_part}{attrs_part}"


class DOMSimplifier:
    """Parses raw HTML and builds a simplified model of the interactive elements on the page.

    Delegates to DOMPruner to enforce token budgets and clean boilerplate/noise.
    """

    def __init__(self, max_tokens: int = 1500) -> None:
        from tools.browser.context.pruner import DOMPruner

        self.pruner = DOMPruner(max_tokens=max_tokens)
        self.nodes: List[InteractiveNode] = []
        self.node_map: Dict[int, InteractiveNode] = {}

    def simplify(self, html: str) -> str:
        """Parse raw HTML, extract interactive elements, and return a clean text representation.

        Args:
            html (str): Raw page HTML source code.

        Returns:
            str: Simplified text representation of interactive elements.
        """
        self.nodes = []
        self.node_map = {}

        if not html:
            return "No content available on the page."

        pruned = self.pruner.prune(html)

        for ref_id, pr_el in pruned.elements.items():
            node = InteractiveNode(
                ref_id=ref_id,
                tag_name=pr_el.tag,
                text=pr_el.text,
                attributes=pr_el.attributes,
                selector=pr_el.selector,
            )
            self.nodes.append(node)
            self.node_map[ref_id] = node

        if not self.nodes:
            return "No interactive elements found on the page."

        return "\n".join(node.to_string() for node in self.nodes)

    def get_selector(self, ref_id: int) -> Optional[str]:
        """Resolve a reference ID to its original CSS selector.

        Args:
            ref_id (int): Node reference ID.

        Returns:
            Optional[str]: Target CSS selector or None.
        """
        node = self.node_map.get(ref_id)
        return node.selector if node else None

    def _build_selector(self, element: Tag) -> str:
        """Legacy helper for backward compatibility."""
        if element.get("id"):
            return f"#{element['id']}"
        return element.name

    def _is_hidden(self, element: Tag) -> bool:
        """Legacy helper for backward compatibility."""
        return False
