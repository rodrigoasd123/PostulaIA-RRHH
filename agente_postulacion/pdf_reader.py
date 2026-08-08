from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from .models import PageText


class PdfReadError(ValueError):
    pass


def read_pdf(data: bytes) -> list[PageText]:
    if not data:
        raise PdfReadError("El archivo esta vacio.")
    try:
        reader = PdfReader(BytesIO(data))
    except Exception as exc:
        raise PdfReadError("No se pudo abrir el PDF. Verifica que no este danado.") from exc
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise PdfReadError("El PDF esta protegido con contrasena.") from exc
    pages = [PageText(i, (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages, 1)]
    if not any(page.text for page in pages):
        raise PdfReadError(
            "El PDF no contiene texto extraible. Para documentos escaneados se requiere OCR."
        )
    return pages
