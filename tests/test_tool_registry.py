import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import registry

print("Registered tools count:", len(registry.get_tools()))
print("Registered tool names:", registry.list_tools())