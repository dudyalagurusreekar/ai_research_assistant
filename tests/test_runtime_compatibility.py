import unittest
import tempfile
import os
from agents.runtime.compatibility import ExecutionCompatibilityLayer
from agents.runtime.fallbacks import requests_fallback, pandas_fallback, numpy_fallback

class TestRuntimeCompatibility(unittest.TestCase):
    def setUp(self):
        self.comp_layer = ExecutionCompatibilityLayer()

    def test_static_rewrites(self):
        code_1 = "import requests\nresp = requests.get('https://example.com')"
        rewritten_1 = self.comp_layer.rewrite_statically(code_1, None)
        self.assertIsNotNone(rewritten_1)
        self.assertIn("agents.runtime.fallbacks.requests_fallback", rewritten_1)

        code_2 = "from pandas import read_csv\ndf = read_csv('data.csv')"
        rewritten_2 = self.comp_layer.rewrite_statically(code_2, None)
        self.assertIsNotNone(rewritten_2)
        self.assertIn("agents.runtime.fallbacks.pandas_fallback", rewritten_2)

        code_3 = "res = file_reader(filepath='report.txt')"
        rewritten_3 = self.comp_layer.rewrite_statically(code_3, None)
        self.assertIsNotNone(rewritten_3)
        self.assertIn("path=", rewritten_3)

    def test_requests_fallback(self):
        resp = requests_fallback.Response("http://test.com", 200, b'{"status": "ok"}', {})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, '{"status": "ok"}')
        self.assertEqual(resp.json(), {"status": "ok"})

    def test_pandas_fallback(self):
        df = pandas_fallback.DataFrame([{"a": 1, "b": 10}, {"a": 2, "b": 20}])
        self.assertEqual(df.shape, (2, 2))
        self.assertEqual(len(df), 2)
        
        col_a = df["a"]
        self.assertEqual(col_a.to_list(), [1, 2])
        self.assertEqual(col_a.mean(), 1.5)
        self.assertEqual(col_a.sum(), 3)

        filtered_df = df[df["a"] > 1]
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df["b"].to_list(), [20])

        rows = list(df.iterrows())
        self.assertEqual(len(rows), 2)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
        try:
            df.to_csv(tmp_path, index=False)
            df2 = pandas_fallback.read_csv(tmp_path)
            self.assertEqual(df2.shape, (2, 2))
            self.assertEqual(df2["b"].to_list(), [10, 20])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_numpy_fallback(self):
        arr = numpy_fallback.array([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(numpy_fallback.mean(arr), 2.5)
        self.assertEqual(numpy_fallback.sum(arr), 10.0)
        self.assertAlmostEqual(numpy_fallback.std(arr), 1.118033988749895)
        
        zeros_arr = numpy_fallback.zeros((2, 3))
        self.assertEqual(zeros_arr.tolist(), [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
