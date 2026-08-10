from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from typing import Literal

import pdfplumber
from pypdf import PdfReader

from .models import PageText


class PdfReadError(ValueError):
    pass


PdfReadMode = Literal["normal", "ocr"]


def read_pdf(data: bytes, mode: PdfReadMode = "normal") -> list[PageText]:
    if not data:
        raise PdfReadError("El archivo está vacío.")

    if mode == "ocr":
        return _read_pdf_with_ocr(data)
    if mode != "normal":
        raise PdfReadError("El método de lectura debe ser 'normal' u 'ocr'.")

    return _read_pdf_normally(data)


def _read_pdf_normally(data: bytes) -> list[PageText]:
    """Extract selectable text and tables without rendering the PDF."""

    pages: list[PageText] = []

    # 1. Intentar extracción avanzada con pdfplumber (maneja tablas y columnas)
    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text_content = page.extract_text() or ""
                normalized_text = " ".join(text_content.split()).lower()

                # Extraer tablas si existen y formatearlas como Markdown solo si aportan texto nuevo
                tables = page.extract_tables()
                if tables:
                    table_texts = []
                    for table in tables:
                        rows = []
                        for row in table:
                            clean_row = [str(cell or "").replace("\n", " ").strip() for cell in row]
                            # Verificar si las celdas principales ya fueron extraídas en el texto de la página
                            meaningful_cells = [c.lower() for c in clean_row if len(c.strip()) > 3]
                            already_in_text = meaningful_cells and all(c in normalized_text for c in meaningful_cells)
                            if any(clean_row) and not already_in_text:
                                rows.append("| " + " | ".join(clean_row) + " |")
                        if rows:
                            table_texts.append("\n".join(rows))
                    if table_texts:
                        text_content += "\n\n" + "\n\n".join(table_texts)

                pages.append(PageText(i, text_content.strip()))
    except Exception:
        pages = []

    # 2. Fallback a pypdf si pdfplumber no obtuvo texto
    if not pages or not any(page.text for page in pages):
        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception as exc:
                    raise PdfReadError("El PDF está protegido con contraseña.") from exc
            pages = [PageText(i, (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages, 1)]
        except Exception as exc:
            raise PdfReadError("No se pudo abrir el PDF. Verifica que no esté dañado.") from exc

    if not any(page.text for page in pages):
        raise PdfReadError(
            "El PDF no contiene texto extraíble. Vuelve a cargarlo usando el método OCR."
        )

    return pages


@lru_cache(maxsize=1)
def _get_ocr_engine():
    """Create the local OCR engine once and reuse it across Streamlit reruns."""
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:
        raise PdfReadError(
            "El modo OCR no está instalado. Ejecuta: "
            "python -m pip install -r requirements.txt"
        ) from exc

    try:
        return RapidOCR(params={"Global.log_level": "warning"})
    except Exception as exc:
        raise PdfReadError("No se pudo iniciar el motor OCR local.") from exc


def _read_pdf_with_ocr(data: bytes) -> list[PageText]:
    """Render each page and recognize its visible text with local OCR."""
    try:
        import numpy as np
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise PdfReadError(
            "El modo OCR no está instalado. Ejecuta: "
            "python -m pip install -r requirements.txt"
        ) from exc

    engine = _get_ocr_engine()
    pages: list[PageText] = []
    source = BytesIO(data)

    try:
        document = pdfium.PdfDocument(source)
    except Exception as exc:
        raise PdfReadError("No se pudo abrir el PDF. Verifica que no esté dañado.") from exc

    try:
        for page_number in range(1, len(document) + 1):
            page = document[page_number - 1]
            bitmap = None
            try:
                # 144 DPI is a useful balance between OCR accuracy, memory and speed.
                bitmap = page.render(scale=2.0)
                image = np.asarray(bitmap.to_pil().convert("RGB"))
                result = engine(image)
                texts = getattr(result, "txts", None) or ()
                page_text = "\n".join(text.strip() for text in texts if text and text.strip())
                pages.append(PageText(page_number, page_text))
            finally:
                if bitmap is not None:
                    bitmap.close()
                page.close()
    except PdfReadError:
        raise
    except Exception as exc:
        raise PdfReadError("No se pudo procesar el documento con OCR.") from exc
    finally:
        document.close()
        source.close()

    if not any(page.text for page in pages):
        raise PdfReadError(
            "El OCR no pudo reconocer texto. Prueba con un escaneo más nítido o con mayor resolución."
        )

    return pages
