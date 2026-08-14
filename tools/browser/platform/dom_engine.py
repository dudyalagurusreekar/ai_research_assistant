"""DOM Understanding Engine for Sprint 11 Browser Automation Platform."""

import logging
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from tools.browser.platform.models import DOMNode, DOMTree

logger = logging.getLogger("Tools.Browser.Platform.DOMEngine")


class DOMUnderstandingEngine:
    """Parses, simplifies, and maps DOM tree structures into structured LLM representations."""

    INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "form", "details", "summary"}

    async def build_dom_tree(self, page: Any) -> DOMTree:
        """Extract and build a structured DOM representation from active page."""
        url = getattr(page, "url", "about:blank")
        html_content = ""

        if hasattr(page, "content"):
            try:
                html_content = await page.content()
            except Exception as e:
                logger.warning(f"Error fetching page content for DOM tree: {e}")
                html_content = "<html><body></body></html>"
        else:
            html_content = "<html><body><h1>Mock DOM Page</h1></body></html>"

        title = ""
        if hasattr(page, "title"):
            try:
                title = await page.title()
            except Exception:
                title = "Untitled Page"

        return self.parse_html_to_dom_tree(html_content, url=url, title=title)

    def parse_html_to_dom_tree(self, html_content: str, url: str = "", title: str = "") -> DOMTree:
        """Parse HTML string into strongly typed DOMTree."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts, styles, noscript tags
        for element in soup(["script", "style", "noscript", "svg"]):
            element.decompose()

        if not title and soup.title:
            title = soup.title.string or ""

        nodes: List[DOMNode] = []
        interactive_elements: List[DOMNode] = []
        node_id_counter = 0

        body = soup.find("body") or soup
        for element in body.find_all(True):
            node_id_counter += 1
            tag_name = element.name.lower()
            text = element.get_text(strip=True)

            attrs = {k: str(v) for k, v in element.attrs.items() if isinstance(v, (str, list))}
            role = attrs.get("role")
            is_interactive = (
                tag_name in self.INTERACTIVE_TAGS
                or "onclick" in attrs
                or role in {"button", "link", "checkbox", "menuitem", "tab"}
            )

            # Construct CSS selector
            elem_id = attrs.get("id")
            elem_class = attrs.get("class")
            if elem_id:
                selector = f"{tag_name}#{elem_id}"
            elif elem_class:
                classes = ".".join(elem_class.split()) if isinstance(elem_class, str) else ".".join(elem_class)
                selector = f"{tag_name}.{classes}" if classes else tag_name
            else:
                selector = tag_name

            node = DOMNode(
                node_id=node_id_counter,
                tag_name=tag_name,
                text_content=text[:100],  # Truncate text content
                attributes=attrs,
                selector=selector,
                is_interactive=is_interactive,
                role=role,
            )

            nodes.append(node)
            if is_interactive:
                interactive_elements.append(node)

        simplified_html = self.clean_and_simplify_html(html_content)

        return DOMTree(
            url=url,
            title=title,
            nodes=nodes,
            interactive_elements=interactive_elements,
            accessibility_tree={"root": {"role": "document", "children_count": len(interactive_elements)}},
            simplified_html=simplified_html,
            total_nodes=len(nodes),
        )

    def clean_and_simplify_html(self, html_content: str, max_chars: int = 4000) -> str:
        """Produce clean, simplified, token-efficient HTML snippet for LLM prompts."""
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "iframe"]):
            tag.decompose()

        cleaned = str(soup.body or soup)
        # Collapse multiple spaces / newlines
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r">\s+<", "><", cleaned)

        if len(cleaned) > max_chars:
            return cleaned[:max_chars] + "...[truncated]"
        return cleaned

    def format_interactive_elements_for_llm(self, dom_tree: DOMTree) -> str:
        """Format interactive DOM elements into bullet list representation for LLM decision making."""
        lines = [f"Page Title: {dom_tree.title}", f"URL: {dom_tree.url}", "Interactive Elements:"]

        for idx, elem in enumerate(dom_tree.interactive_elements[:30], 1):
            text = f'"{elem.text_content}"' if elem.text_content else ""
            attr_str = " ".join(f'{k}="{v}"' for k, v in elem.attributes.items() if k in {"name", "type", "placeholder", "href", "id"})
            lines.append(f"  [{idx}] <{elem.tag_name} selector='{elem.selector}' {attr_str}> {text}")

        return "\n".join(lines)
