import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.web.webpage_reader import WebPageReaderTool

tool = WebPageReaderTool()

print("--- Testing Standard Webpage Reader ---")
result_standard = tool.forward("https://en.wikipedia.org/wiki/Python_(programming_language)")
print("Standard Result Output Length:", len(result_standard))
print("Standard Result Header:")
print("\n".join(result_standard.splitlines()[:10]))

print("\n--- Testing Webpage Reader with Query Extraction ---")
result_query = tool.forward(
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    query="Guido van Rossum"
)
print("Query Result Output Length:", len(result_query))
print("Query Result Header:")
print("\n".join(result_query.splitlines()[:15]))
