import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import registry

tools = registry.get_tools()
calculator = tools[0]

print(calculator.forward("2 + 3"))
print(calculator.forward("10 * 5"))
print(calculator.forward("2 ** 8"))
print(calculator.forward("(15 + 5) / 4"))