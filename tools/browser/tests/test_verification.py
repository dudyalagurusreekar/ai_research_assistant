"""Unit tests for Browser Action Verifier."""

import unittest
from tools.browser.verification import BrowserActionVerifier


class TestBrowserActionVerifier(unittest.TestCase):
    """Test action verification checks."""

    def test_verifications(self):
        verifier = BrowserActionVerifier()

        url_res = verifier.verify_url("wikipedia.org", "https://en.wikipedia.org/wiki/Main_Page")
        self.assertTrue(url_res.passed)

        dom_res = verifier.verify_dom_mutation("hash_1", "hash_2")
        self.assertTrue(dom_res.passed)

        elem_res = verifier.verify_element_present("#submit", "<div><button id='submit'>Go</button></div>")
        self.assertTrue(elem_res.passed)


if __name__ == "__main__":
    unittest.main()
