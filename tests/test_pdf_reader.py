import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from pypdf import PdfWriter
from tools.file.pdf_reader_tool import PdfReaderTool

# Create a sample PDF file for testing
sample_pdf_path = root_dir / "scratch" / "test_sample.pdf"
sample_pdf_path.parent.mkdir(parents=True, exist_ok=True)

writer = PdfWriter()
page = writer.add_blank_page(width=612, height=792)

# Save sample PDF
with open(sample_pdf_path, "wb") as f:
    writer.write(f)

print("Sample test PDF created at:", sample_pdf_path)

tool = PdfReaderTool()
result = tool.forward(str(sample_pdf_path))
print("--- PdfReaderTool Output ---")
print(result)
