"""Unit Tests for Context Layer and DOM Pruner.

Validates that DOMPruner simplifies HTML to numbered interactive elements,
enforces token budgets, and resolves selectors correctly.
"""

import unittest
from tools.browser.context import DOMPruner, ContextLifecycleManager


class TestDOMPruner(unittest.TestCase):
    """Tests for DOM pruning and token budgeting."""

    def test_prunes_interactive_elements_with_reference_ids(self):
        pruner = DOMPruner(max_tokens=1000)
        html = """
        <html>
            <head><script>console.log("ignore");</script></head>
            <body>
                <header><div>Logo</div></header>
                <a href="https://example.com/login" id="login-link">Login</a>
                <form id="login-form">
                    <input type="text" id="username" name="user" placeholder="Enter username" />
                    <button type="submit" id="submit-btn">Submit</button>
                </form>
                <footer>Legal text</footer>
            </body>
        </html>
        """
        pruned = pruner.prune(html)
        self.assertGreater(pruned.total_elements, 0)
        self.assertIn("[1]", pruned.simplified_str)
        self.assertIn("Login", pruned.simplified_str)
        self.assertIn("Enter username", pruned.simplified_str)
        self.assertIn("Submit", pruned.simplified_str)
        self.assertNotIn("console.log", pruned.simplified_str)

        # Check selector resolution
        sel_1 = pruned.get_selector(1)
        self.assertEqual(sel_1, "#login-link")
        sel_2 = pruned.get_selector(2)
        self.assertEqual(sel_2, "#login-form")

    def test_enforces_token_budget_truncation(self):
        pruner = DOMPruner(max_tokens=20)  # Very small token budget ~80 chars
        html = "<html><body>" + "".join([f'<a href="/p{i}" id="a{i}">Link Number {i}</a>' for i in range(50)]) + "</body></html>"
        pruned = pruner.prune(html)

        self.assertLess(pruned.estimated_tokens, 50)
        self.assertIn("Truncated", pruned.simplified_str)


class TestContextManagerIntegration(unittest.TestCase):
    """Tests for ContextLifecycleManager legacy and new API compatibility."""

    def test_context_manager_prune_dom(self):
        cm = ContextLifecycleManager()
        html = '<a href="/test" id="test-link">Test</a>'
        pruned = cm.prune_dom(html)
        self.assertEqual(pruned.total_elements, 1)
        self.assertEqual(pruned.get_selector(1), "#test-link")

    def test_legacy_dom_simplifier_delegation(self):
        from tools.browser.planner.simplifier import DOMSimplifier
        simplifier = DOMSimplifier(max_tokens=1000)
        html = '<button id="submit-btn">Submit</button>'
        simplified_str = simplifier.simplify(html)
        self.assertIn("Submit", simplified_str)
        self.assertEqual(simplifier.get_selector(1), "#submit-btn")


if __name__ == "__main__":
    unittest.main()
