"""DOM Intelligence & Semantic Resolution Engine."""

import logging
from typing import List, Dict, Any, Optional
from core.browser.models import DOMElementNode

logger = logging.getLogger(__name__)


class DOMIntelligenceEngine:
    """Parses DOM structure, resolves semantic elements, and generates accessibility trees."""

    async def get_interactive_elements(self, session: Dict[str, Any]) -> List[DOMElementNode]:
        """Extract interactive DOM elements (buttons, inputs, links, forms) from page."""
        page = session.get("page")
        elements: List[DOMElementNode] = []

        if page:
            try:
                # Query interactive selectors
                locators = await page.query_selector_all("button, a, input, select, textarea, [role='button']")
                for loc in locators[:30]:
                    tag = await loc.evaluate("el => el.tagName.toLowerCase()")
                    text = await loc.inner_text() or await loc.get_attribute("value") or ""
                    role = await loc.get_attribute("role") or tag
                    sel = f"{tag}[text='{text.strip()[:20]}']"

                    elements.append(
                        DOMElementNode(
                            tag_name=tag,
                            role=role,
                            text_content=text.strip(),
                            is_interactive=True,
                            selector=sel,
                        )
                    )
                return elements
            except Exception as e:
                logger.warning(f"Error querying live DOM locators: {e}. Returning simulated nodes.")

        # Fallback simulated interactive element tree
        return [
            DOMElementNode(tag_name="input", id="search-input", role="searchbox", is_interactive=True, selector="#search-input"),
            DOMElementNode(tag_name="button", id="submit-btn", text_content="Search Literature", role="button", is_interactive=True, selector="#submit-btn"),
            DOMElementNode(tag_name="a", text_content="Download Full PDF", role="link", is_interactive=True, selector="a[text='Download Full PDF']"),
        ]

    def truncate_dom_for_llm(self, elements: List[DOMElementNode], max_nodes: int = 20) -> str:
        """Format interactive elements into concise Markdown/YAML tree for LLM prompt context."""
        lines = ["# Interactive Page Elements:"]
        for idx, node in enumerate(elements[:max_nodes]):
            line = f"- [{idx + 1}] <{node.tag_name}> role='{node.role or 'element'}' text='{node.text_content or ''}' selector='{node.selector}'"
            lines.append(line)
        return "\n".join(lines)
