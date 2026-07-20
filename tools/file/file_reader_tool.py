from pathlib import Path
from smolagents import Tool


class FileReaderTool(Tool):

    name = "file_reader"

    description = (
    "Use this tool whenever the user asks to read, display, "
    "open, inspect, summarize, or analyze the contents of a "
    "local text file. The input must be the complete file path."
    )

    inputs = {
        "path": {
            "type": "string",
            "description": "Full path to a text file."
        }
    }

    output_type = "string"

    def forward(self, path: str):

        file = Path(path)

        if not file.exists():
            return f"File not found: {path}"

        if file.is_dir():
            return "The given path is a directory."

        # Try reading with BOM detection first
        with open(file, "rb") as f:
            raw = f.read()

        encodings = [
            "utf-8-sig",
            "utf-8",
            "utf-16",
            "utf-16-le",
            "utf-16-be",
            "cp1252",
            "latin-1"
        ]

        for encoding in encodings:
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                pass

        return "Unable to decode this file."