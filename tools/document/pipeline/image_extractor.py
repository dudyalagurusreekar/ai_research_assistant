"""ImageExtractorStep for processing embedded images and triggering OCR when text is sparse."""

from tools.document.interfaces.pipeline import IPipelineStep
from tools.document.models.document import NormalizedDocument
from tools.document.models.context import ProcessingContext
from infrastructure.logging.logger import StructuredLogger

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class ImageExtractorStep(IPipelineStep):
    """Pipeline step managing image dimension inspection and OCR processing."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ImageExtractorStep")

    @property
    def name(self) -> str:
        return "ImageExtractorStep"

    async def process(
        self,
        document: NormalizedDocument,
        context: ProcessingContext,
    ) -> NormalizedDocument:
        if not context.config.enable_image_extraction:
            return document

        for img in document.images:
            # Inspect dimensions if raw_bytes available and PIL present
            if img.raw_bytes and PIL_AVAILABLE and (not img.width or not img.height):
                try:
                    pil_img = Image.open(io.BytesIO(img.raw_bytes))
                    img.width, img.height = pil_img.size
                except Exception as e:
                    self._logger.debug(f"Could not read PIL image dimensions: {e}")

            # Perform OCR if enabled and pytesseract available
            if (
                context.config.enable_ocr
                and img.raw_bytes
                and PYTESSERACT_AVAILABLE
                and not img.ocr_text
            ):
                try:
                    pil_img = Image.open(io.BytesIO(img.raw_bytes))
                    ocr_result = pytesseract.image_to_string(pil_img, lang=context.config.ocr_language)
                    if ocr_result and len(ocr_result.strip()) > 0:
                        img.ocr_text = ocr_result.strip()
                        self._logger.debug(f"OCR extracted {len(img.ocr_text)} characters for image '{img.image_id}'")
                except Exception as e:
                    context.add_warning(f"OCR processing failed for image '{img.image_id}': {e}")

        return document
