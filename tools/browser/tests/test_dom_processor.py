"""Unit tests for DOM Processor."""

import unittest
from tools.browser.dom import DOMProcessor


class TestDOMProcessor(unittest.TestCase):
    """Test DOM pruning, interactive element extraction, and hashing."""

    def test_dom_pruning_and_hashing(self):
        processor = DOMProcessor(max_token_budget=500)
        raw_html = '<html><head><script>alert(1)</script></head><body><h1>Title</h1><a href="/link">Click Me</a></body></html>'

        processed = processor.process(raw_html)
        self.assertTrue(bool(processed.dom_hash))
        self.assertIn("[1] <a href=\"/link\">Click Me</a>", processed.simplified_text)
        self.assertNotIn("alert(1)", processed.simplified_text)


if __name__ == "__main__":
    unittest.main()
