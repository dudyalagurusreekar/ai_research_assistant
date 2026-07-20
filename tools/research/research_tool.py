from typing import List
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from smolagents import Tool


class ResearchTool(Tool):
    name = "research"

    description = (
        "Research a topic by searching the web, reading the best webpages, "
        "and returning a consolidated research summary."
    )

    inputs = {
        "query": {
            "type": "string",
            "description": "Research topic"
        }
    }

    output_type = "string"

    SEARCH_RESULTS = 2
    PAGE_CHAR_LIMIT = 800
    REQUEST_TIMEOUT = 10

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/137 Safari/537.36"
        )
    }

    def forward(self, query: str) -> str:

        search_results = self.search(query)

        if not search_results:
            return "No useful search results found."

        report = [
            "=" * 80,
            f"Research Report: {query}",
            "=" * 80,
            "",
        ]

        for index, result in enumerate(search_results, start=1):

            title = result["title"]
            url = result["href"]

            report.append(f"[{index}] {title}")
            report.append(url)

            text = self.read_page(url)

            if text:
                report.append(text)

            report.append("\n" + "-" * 80 + "\n")

        return "\n".join(report)

    def search(self, query: str) -> List[dict]:

        try:
            results = list(
                DDGS().text(
                    query,
                    max_results=self.SEARCH_RESULTS
                )
            )

            unique = []
            seen = set()

            for result in results:

                url = result["href"]

                if url not in seen:
                    seen.add(url)
                    unique.append(result)

            return unique

        except Exception:
            return []

    def read_page(self, url: str) -> str:

        try:

            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=self.REQUEST_TIMEOUT
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            for tag in soup([
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "aside",
                "noscript"
            ]):
                tag.decompose()

            text = soup.get_text(separator="\n")

            lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            cleaned = "\n".join(lines)

            paragraphs = cleaned.split("\n")

            filtered = []

            for p in paragraphs:
                p = p.strip()

                if len(p) < 40:
                    continue

                filtered.append(p)

            return "\n\n".join(filtered)[: self.PAGE_CHAR_LIMIT]

        except Exception:
            return ""