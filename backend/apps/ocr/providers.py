"""OCR provider abstraction.

Every provider implements the same `extract(file_path, content_type)` contract
and returns an `OcrResult`. This keeps the rest of the pipeline (field
parsing, validation) completely decoupled from *how* text was pulled off the
document, so swapping Tesseract for AWS Textract / Google Document AI /
Azure Document Intelligence later only means adding a new provider class and
pointing OCR_PROVIDER at it -- nothing else in the app changes.
"""

import logging
from dataclasses import dataclass, field

from django.conf import settings

logger = logging.getLogger(__name__)

IMAGE_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/tiff"}
PDF_CONTENT_TYPES = {"application/pdf"}


@dataclass
class OcrResult:
    raw_text: str
    page_count: int
    word_confidences: list = field(default_factory=list)  # 0-100 per recognized word
    provider: str = ""
    is_demo_fallback: bool = False  # True when no real OCR engine actually ran

    @property
    def mean_confidence(self):
        if not self.word_confidences:
            return 0.0
        return sum(self.word_confidences) / len(self.word_confidences)


class BaseOCRProvider:
    name = "base"

    def extract(self, file_path, content_type) -> OcrResult:
        raise NotImplementedError


class TesseractOCRProvider(BaseOCRProvider):
    """Local OCR using Tesseract (pytesseract) + pdf2image/Pillow for PDFs.

    This is real OCR: no field values are invented. If Tesseract or Poppler
    are not installed on the host, `is_available()` returns False and the
    caller should fall back to `DemoOCRProvider` instead of silently
    producing fake results.
    """

    name = "tesseract"

    def is_available(self):
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def _load_images(self, file_path, content_type):
        from PIL import Image

        if content_type in PDF_CONTENT_TYPES or str(file_path).lower().endswith(".pdf"):
            from pdf2image import convert_from_path

            return convert_from_path(file_path, dpi=200)
        return [Image.open(file_path).convert("RGB")]

    def _preprocess(self, pil_image):
        """Light preprocessing (grayscale + threshold) to improve OCR
        accuracy on scanned invoices, using OpenCV."""
        import cv2
        import numpy as np

        arr = np.array(pil_image)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def extract(self, file_path, content_type) -> OcrResult:
        import pytesseract
        from pytesseract import Output

        images = self._load_images(file_path, content_type)
        full_text_parts = []
        confidences = []

        for img in images:
            try:
                processed = self._preprocess(img)
            except Exception:
                processed = img  # fall back to unprocessed image if cv2 preprocessing fails

            data = pytesseract.image_to_data(processed, output_type=Output.DICT)
            # Group words by (block, paragraph, line) so the reconstructed
            # text preserves real line breaks -- several downstream parsing
            # heuristics (e.g. "vendor name is the first line") depend on it.
            current_line_key = None
            current_line_words = []
            page_lines = []

            def flush_line():
                if current_line_words:
                    page_lines.append(" ".join(current_line_words))

            for i, word in enumerate(data.get("text", [])):
                if not (word and word.strip()):
                    continue
                line_key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
                if line_key != current_line_key:
                    flush_line()
                    current_line_words = []
                    current_line_key = line_key
                current_line_words.append(word)
                try:
                    conf = float(data["conf"][i])
                    if conf >= 0:
                        confidences.append(conf)
                except (ValueError, IndexError):
                    pass
            flush_line()
            full_text_parts.append("\n".join(page_lines))

        return OcrResult(
            raw_text="\n".join(full_text_parts),
            page_count=len(images),
            word_confidences=confidences,
            provider=self.name,
            is_demo_fallback=False,
        )


class DemoOCRProvider(BaseOCRProvider):
    """Deterministic fallback used when no real OCR engine is available
    (or OCR_PROVIDER=demo is explicitly configured) so the product still
    functions end-to-end for a demo without external dependencies.

    IMPORTANT: this does NOT read the document contents. It synthesizes a
    plausible-looking but clearly-labeled placeholder result so downstream
    field parsing has *something* to validate against. The UI always shows
    `ocr_provider="demo"` so nobody can mistake this for real AI/OCR output.
    """

    name = "demo"

    def extract(self, file_path, content_type) -> OcrResult:
        logger.warning(
            "DemoOCRProvider engaged for %s -- no real OCR was performed. "
            "This is a fallback path, not an AI extraction result.",
            file_path,
        )
        placeholder_text = (
            "DEMO FALLBACK DOCUMENT\n"
            "No OCR engine was available to read this file's contents.\n"
            "Please fill in the extracted fields manually on the review screen."
        )
        return OcrResult(
            raw_text=placeholder_text,
            page_count=1,
            word_confidences=[0.0],
            provider=self.name,
            is_demo_fallback=True,
        )


def get_ocr_provider() -> BaseOCRProvider:
    provider_name = getattr(settings, "OCR_PROVIDER", "tesseract")

    if provider_name == "tesseract":
        provider = TesseractOCRProvider()
        if provider.is_available():
            return provider
        logger.warning("Tesseract not available on this host; falling back to DemoOCRProvider.")
        return DemoOCRProvider()

    if provider_name == "demo":
        return DemoOCRProvider()

    # Placeholders for future cloud providers -- structured so adding one is
    # a matter of implementing BaseOCRProvider and registering it here.
    if provider_name in ("textract", "docai", "azure"):
        logger.warning(
            "OCR_PROVIDER=%s is not yet implemented in this build; using DemoOCRProvider.", provider_name
        )
        return DemoOCRProvider()

    return DemoOCRProvider()
