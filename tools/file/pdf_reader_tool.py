from pathlib import Path
import pypdf
from smolagents import Tool


class PdfReaderTool(Tool):
    """
    Tool for reading, parsing, and extracting text from PDF files.
    """

    name = "pdf_reader"

    description = (
        "Reads a local PDF document file and extracts clean text content page by page. "
        "Use this tool whenever the user asks to read, analyze, summarize, or extract text from a PDF file."
    )

    inputs = {
        "path": {
            "type": "string",
            "description": "Full local file path to the PDF document.",
        },
        "max_pages": {
            "type": "integer",
            "description": "Maximum number of pages to read (default is 50).",
            "nullable": True,
        },
    }

    output_type = "string"

    def forward(self, path: str, max_pages: int = 50) -> str:
        file_path = Path(path.strip())

        if not file_path.exists():
            return f"Error: File not found at path '{path}'."

        if file_path.is_dir():
            return f"Error: Path '{path}' is a directory, not a PDF file."

        if file_path.suffix.lower() != ".pdf":
            return f"Error: File '{file_path.name}' does not have a .pdf extension."

        try:
            reader = pypdf.PdfReader(str(file_path))

            if reader.is_encrypted:
                try:
                    # Attempt empty password decrypt
                    reader.decrypt("")
                except Exception:
                    return f"Error: PDF document '{file_path.name}' is password protected / encrypted."

            total_pages = len(reader.pages)
            pages_to_read = min(total_pages, max_pages or 50)

            extracted_pages = []

            for page_num in range(pages_to_read):
                page = reader.pages[page_num]
                text = page.extract_text() or ""
                
                # Clean whitespace
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                page_text = "\n".join(lines)

                if page_text:
                    extracted_pages.append(f"--- [Page {page_num + 1} of {total_pages}] ---\n{page_text}")

            if not extracted_pages:
                return f"PDF '{file_path.name}' (Total Pages: {total_pages}) contains no extractable text (it might be scanned images)."

            content = "\n\n".join(extracted_pages)
            summary_header = f"File: {file_path.name}\nTotal Pages: {total_pages} | Pages Read: {pages_to_read}\n\n"
            
            # Allow up to 15,000 chars for comprehensive output
            return (summary_header + content)[:15000]

        except Exception as err:
            return f"Error reading PDF file '{file_path.name}': {str(err)}"
