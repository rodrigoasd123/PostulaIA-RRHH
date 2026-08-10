from __future__ import annotations

from io import BytesIO
import pdfplumber
from pypdf import PdfReader

from .models import PageText


class PdfReadError(ValueError):
    pass


def read_pdf(data: bytes) -> list[PageText]:
    if not data:
        raise PdfReadError("El archivo esta vacio.")

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
                    raise PdfReadError("El PDF esta protegido con contrasena.") from exc
            pages = [PageText(i, (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages, 1)]
        except Exception as exc:
            raise PdfReadError("No se pudo abrir el PDF. Verifica que no este danado.") from exc

    if not any(page.text for page in pages):
        raise PdfReadError(
            "El PDF no contiene texto extraible. Para documentos escaneados se requiere OCR."
        )

    return pages
