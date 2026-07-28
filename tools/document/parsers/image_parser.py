"""Image Document & OCR Parser using Pillow and pytesseract."""

import io
from typing import List, Union, BinaryIO
from tools.document.parsers.base import BaseDocumentParser
from tools.document.models.document import NormalizedDocument, DocumentImage
from tools.document.models.format import DocumentFormat
from tools.document.models.context import ProcessingContext

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class ImageOCRParser(BaseDocumentParser):
    """Parser strategy for image files (PNG, JPG, WEBP, BMP, GIF, TIFF)."""

    @property
    def supported_formats(self) -> List[DocumentFormat]:
        return [DocumentFormat.IMAGE]

    async def parse(
        self,
        source: Union[str, bytes, BinaryIO],
        context: ProcessingContext,
    ) -> NormalizedDocument:
        raw_bytes = self._read_bytes(source)
        file_name = getattr(source, "name", "image.png") if not isinstance(source, (str, bytes)) else (source if isinstance(source, str) else "image.png")
        doc = self._create_initial_document(source, file_name=file_name, mime_type="image/png")

        img_obj = DocumentImage(
            caption=file_name,
            mime_type=doc.metadata.mime_type,
            raw_bytes=raw_bytes,
        )

        if PIL_AVAILABLE:
            try:
                pil_img = Image.open(io.BytesIO(raw_bytes))
                img_obj.width, img_obj.height = pil_img.size
                img_obj.mime_type = f"image/{pil_img.format.lower()}" if pil_img.format else "image/png"
                doc.metadata.mime_type = img_obj.mime_type

                if PYTESSERACT_AVAILABLE and context.config.enable_ocr:
                    ocr_text = pytesseract.image_to_string(pil_img, lang=context.config.ocr_language)
                    if ocr_text and ocr_text.strip():
                        img_obj.ocr_text = ocr_text.strip()
                        doc.full_text = img_obj.ocr_text
                        doc.add_section(title="OCR Extracted Text", level=1, content=doc.full_text)
                    else:
                        doc.full_text = f"[Image Document: {file_name} ({img_obj.width}x{img_obj.height} px)]"
                else:
                    doc.full_text = f"[Image Document: {file_name} ({img_obj.width}x{img_obj.height} px)]"
            except Exception as e:
                self._logger.error(f"Error processing PIL image: {e}")
                doc.full_text = f"[Image Document: {file_name} ({len(raw_bytes)} bytes)]"
        else:
            doc.full_text = f"[Image Document: {file_name} ({len(raw_bytes)} bytes)]"

        doc.images.append(img_obj)
        return doc
