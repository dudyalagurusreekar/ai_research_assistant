"""DOM Pruning & Minimal Representation Engine (`tools/browser/context/pruner.py`).

Reduces verbose raw HTML to an extremely compact, numbered interactive element map
and concise text summary, enforcing strict token budgets to minimize LLM prompt size
and latency.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from bs4 import Tag
import logging

from tools.browser.parsers.cleaner import HTMLCleaner

logger = logging.getLogger("DOMPruner")


@dataclass
class PrunedElement:
    """An interactive DOM element with an assigned numeric reference ID."""

    ref_id: int
    tag: str
    text: str
    attributes: Dict[str, str] = field(default_factory=dict)
    selector: str = ""

    def to_compact_string(self) -> str:
        """Format as a compact numbered line for LLM prompts."""
        attrs_str = ""
        for k, v in self.attributes.items():
            if v:
                attrs_str += f' {k}="{v}"'
        content = f" {self.text}" if self.text else ""
        return f"[{self.ref_id}] <{self.tag}{attrs_str}>{content}</{self.tag}>"


@dataclass
class PrunedDOM:
    """The result of pruning a DOM tree for minimal LLM context."""

    simplified_str: str
    elements: Dict[int, PrunedElement] = field(default_factory=dict)
    total_elements: int = 0
    estimated_tokens: int = 0

    def get_selector(self, ref_id: int) -> Optional[str]:
        """Resolve a numeric reference ID to its CSS selector."""
        el = self.elements.get(ref_id)
        return el.selector if el else None


class DOMPruner:
    """Prunes HTML trees into compact, numbered interactive element lists.

    Enforces token budgets by truncating or aggregating low-priority elements
    while preserving interactive inputs, links, buttons, and forms.
    """

    INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "form"}

    def __init__(self, max_tokens: int = 1500) -> None:
        """Initialize DOM Pruner.

        Args:
            max_tokens (int): Maximum token budget for the pruned DOM string (approx 4 chars per token).
        """
        self.max_tokens = max_tokens
        self.max_chars = max_tokens * 4

    def prune(self, raw_html: str, url: Optional[str] = None) -> PrunedDOM:
        """Prune raw HTML into a minimal interactive element representation.

        Args:
            raw_html (str): Raw HTML string from the browser.
            url (Optional[str]): Current URL for logging/context.

        Returns:
            PrunedDOM: Pruned string and reference ID map.
        """
        if not raw_html or not raw_html.strip():
            return PrunedDOM(simplified_str="No DOM content available.", elements={}, total_elements=0, estimated_tokens=5)

        cleaner = HTMLCleaner(remove_boilerplate=False)
        soup = cleaner.clean(raw_html)
        elements: Dict[int, PrunedElement] = {}
        lines: List[str] = []
        ref_id = 1
        current_chars = 0

        for tag in soup.find_all(list(self.INTERACTIVE_TAGS)):
            if not isinstance(tag, Tag):
                continue

            tag_name = tag.name.lower()
            if tag_name == "input" and str(tag.get("type", "")).lower() == "hidden":
                continue
            text = tag.get_text(strip=True)[:100]

            # Extract priority attributes
            attrs = {}
            if "id" in tag.attrs and tag["id"]:
                attrs["id"] = str(tag["id"])
            if "name" in tag.attrs and tag["name"]:
                attrs["name"] = str(tag["name"])
            if "type" in tag.attrs and tag["type"]:
                attrs["type"] = str(tag["type"])
            if "placeholder" in tag.attrs and tag["placeholder"]:
                attrs["placeholder"] = str(tag["placeholder"])[:50]
            if tag_name == "a" and "href" in tag.attrs and tag["href"]:
                attrs["href"] = str(tag["href"])[:60]
            if "value" in tag.attrs and tag["value"]:
                attrs["value"] = str(tag["value"])[:50]

            # Determine CSS selector
            selector = self._build_selector(tag)

            el = PrunedElement(
                ref_id=ref_id,
                tag=tag_name,
                text=text,
                attributes=attrs,
                selector=selector,
            )
            line = el.to_compact_string()

            # Check character/token budget
            if current_chars + len(line) > self.max_chars:
                lines.append(f"... [Truncated {len(soup.find_all(list(self.INTERACTIVE_TAGS))) - ref_id + 1} remaining interactive elements to enforce {self.max_tokens} token budget] ...")
                break

            elements[ref_id] = el
            lines.append(line)
            current_chars += len(line) + 1
            ref_id += 1

        simplified_str = "\n".join(lines) if lines else "No interactive elements detected on page."
        estimated_tokens = len(simplified_str) // 4

        return PrunedDOM(
            simplified_str=simplified_str,
            elements=elements,
            total_elements=len(elements),
            estimated_tokens=estimated_tokens,
        )

    def _build_selector(self, tag: Tag) -> str:
        """Construct a unique CSS selector for a BeautifulSoup Tag."""
        if "id" in tag.attrs and tag["id"]:
            return f"#{tag['id']}"
        if "name" in tag.attrs and tag["name"] and tag.name in ["input", "select", "textarea"]:
            return f"{tag.name}[name='{tag['name']}']"

        parent = tag.parent
        if not parent or parent.name == "[document]":
            return tag.name

        siblings = parent.find_all(tag.name, recursive=False)
        parent_sel = self._build_selector(parent) if parent.name != "[document]" else ""
        if len(siblings) <= 1:
            if parent_sel:
                return f"{parent_sel} > {tag.name}"
            return tag.name

        idx = siblings.index(tag) + 1
        if parent_sel:
            return f"{parent_sel} > {tag.name}:nth-of-type({idx})"
        return f"{tag.name}:nth-of-type({idx})"
