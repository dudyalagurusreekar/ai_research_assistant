import unittest
from tools.core.datetime_tool import DateTimeTool

class TestDateTimeTool(unittest.TestCase):
    def test_forward(self):
        tool = DateTimeTool()
        result = tool.forward()
        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()