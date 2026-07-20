import requests
from bs4 import BeautifulSoup
from smolagents import Tool


class WebPageReaderTool(Tool):
    name = "webpage_reader"

    description = (
        "Reads the content of a webpage from a URL and returns clean text."
    )

    inputs = {
        "url": {
            "type": "string",
            "description": "The webpage URL."
        }
    }

    output_type = "string"

    def forward(self, url: str):

        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            response = requests.get(
                url,
                timeout=15,
                headers=headers,
            )

            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup([
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "nav",
                "aside"
            ]):
                tag.decompose()

            text = soup.get_text(separator="\n")

            lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            cleaned = "\n".join(lines)

            return cleaned[:12000]

        except Exception as e:
            return f"Error: {e}"