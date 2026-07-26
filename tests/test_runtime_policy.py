import unittest
from agents.runtime.policy import ImportPolicyManager, ImportStatus

class TestRuntimePolicy(unittest.TestCase):
    def test_evaluate_imports(self):
        manager = ImportPolicyManager(additional_authorized_imports=["litellm"])
        
        res = manager.evaluate_import("math")
        self.assertEqual(res["status"], ImportStatus.ALLOW)
        
        res = manager.evaluate_import("litellm")
        self.assertEqual(res["status"], ImportStatus.ALLOW)

        res = manager.evaluate_import("subprocess")
        self.assertEqual(res["status"], ImportStatus.BLOCK)
        
        res = manager.evaluate_import("requests")
        self.assertEqual(res["status"], ImportStatus.RESTRICT)
        self.assertEqual(res["fallback"], "agents.runtime.fallbacks.requests_fallback")

        res = manager.evaluate_import("non_existent_mock_library_xyz")
        self.assertEqual(res["status"], ImportStatus.UNAVAILABLE)
