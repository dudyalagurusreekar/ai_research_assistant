from ddgs import DDGS
from smolagents import Tool


class WebSearchTool(Tool):
    name = "web_search"

    description = (
        "Search the web and return the top search results."
    )

    inputs = {
        "query": {
            "type": "string",
            "description": "Search query"
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results",
            "nullable": True,
        }
    }

    output_type = "string"

    def forward(self, query: str, max_results: int = 5) -> str:

        results = DDGS().text(query, max_results=max_results)

        if not results:
            return "No search results."

        output = []

        for i, r in enumerate(results, 1):

            output.append(
                f"""{i}.
Title: {r['title']}
URL: {r['href']}
Snippet: {r['body']}
"""
            )

        return "\n".join(output)