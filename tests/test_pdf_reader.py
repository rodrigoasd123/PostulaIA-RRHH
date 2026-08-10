from io import BytesIO
from types import SimpleNamespace

from PIL import Image
import pytest

from backend import pdf_reader
from backend.pdf_reader import PdfReadError, read_pdf


def scanned_pdf_bytes() -> bytes:
    image = Image.new("RGB", (800, 500), "white")
    output = BytesIO()
    image.save(output, format="PDF", resolution=144)
    return output.getvalue()


def test_ocr_mode_renders_pages_and_returns_recognized_text(monkeypatch):
    received_images = []

    class FakeOcrEngine:
        def __call__(self, image):
            received_images.append(image)
            return SimpleNamespace(txts=("REQUISITO OBLIGATORIO", "Título universitario"))

    monkeypatch.setattr(pdf_reader, "_get_ocr_engine", lambda: FakeOcrEngine())

    pages = read_pdf(scanned_pdf_bytes(), mode="ocr")

    assert len(pages) == 1
    assert pages[0].page == 1
    assert "REQUISITO OBLIGATORIO" in pages[0].text
    assert received_images[0].shape[2] == 3


def test_normal_mode_suggests_ocr_for_image_only_pdf():
    with pytest.raises(PdfReadError, match="OCR"):
        read_pdf(scanned_pdf_bytes(), mode="normal")


def test_rejects_unknown_reading_mode():
    with pytest.raises(PdfReadError, match="normal.*ocr"):
        read_pdf(b"not-empty", mode="automatico")
