import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from tools.file.file_reader_tool import FileReaderTool

tool = FileReaderTool()

print(
    tool.forward(
        str(root_dir / "requirements.txt")
    )
)