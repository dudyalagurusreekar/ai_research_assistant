import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from smolagents import Tool


class WebPageReaderTool(Tool):
    """
    Tool for fetching, cleaning, and extracting information from a single webpage URL.
    """

    name = "webpage_reader"

    description = (
        "Fetches a single webpage URL, cleans HTML clutter (removing ads, scripts, nav, footers), "
        "and extracts clean readable content or specific information matching an optional query."
    )

    inputs = {
        "url": {
            "type": "string",
            "description": "The webpage URL to read (e.g. 'https://example.com/article').",
        },
        "query": {
            "type": "string",
            "description": "Optional keyword or question to filter and extract relevant paragraphs from the page.",
            "nullable": True,
        },
    }

    output_type = "string"

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )

    def forward(self, url: str, query: str = None) -> str:
        url = url.strip()

        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            # Validate URL structure
            parsed = urllib.parse.urlparse(url)
            if not parsed.netloc:
                return f"Error: Invalid URL format '{url}'."

            headers = {
                "User-Agent": self.DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            response = requests.get(
                url,
                timeout=15,
                headers=headers,
                allow_redirects=True,
            )

            response.raise_for_status()

            # Handle encoding
            if response.encoding is None:
                response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract page title
            title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"

            # Remove clutter elements
            for tag in soup([
                "script", "style", "noscript", "header", "footer",
                "nav", "aside", "form", "svg", "iframe", "button", "canvas"
            ]):
                tag.decompose()

            # Extract main readable text
            text = soup.get_text(separator="\n")

            # Clean and normalize lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_content = "\n".join(lines)

            # Filter paragraphs if a query is provided
            if query and query.strip():
                keywords = [k.lower() for k in re.findall(r"\w+", query) if len(k) > 2]
                paragraphs = cleaned_content.split("\n\n") if "\n\n" in cleaned_content else cleaned_content.split("\n")
                
                matched = []
                for p in paragraphs:
                    p_lower = p.lower()
                    if any(kw in p_lower for kw in keywords):
                        matched.append(p.strip())

                if matched:
                    extracted_text = "\n\n".join(matched[:15])
                    return f"Title: {title}\nURL: {url}\n\n=== Extracted Relevant Content for '{query}' ===\n\n{extracted_text[:10000]}"

            # Truncate content for standard response
            return f"Title: {title}\nURL: {url}\n\n=== Clean Page Content ===\n\n{cleaned_content[:12000]}"

        except requests.exceptions.Timeout:
            return f"Error: Request to '{url}' timed out after 15 seconds."
        except requests.exceptions.HTTPError as err:
            return f"Error: HTTP {err.response.status_code} error fetching '{url}'."
        except requests.exceptions.RequestException as err:
            return f"Error: Failed to fetch webpage '{url}': {str(err)}"
        except Exception as err:
            return f"Error: Failed to parse webpage content from '{url}': {str(err)}"