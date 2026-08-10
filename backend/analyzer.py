from __future__ import annotations

import re

from .models import DocumentAnalysis, Evidence, PageText
from .retrieval import SENTENCE_RE, normalize

PATTERNS = {
    "requirements": re.compile(r"\b(requisit|experien|formaci|titulo|grado|colegiad|certific|conocim|habilidad|perfil|debera contar|indispensable)"),
    "dates": re.compile(r"\b(fecha|plazo|cronograma|hasta el|vence|vencimiento|presentaci|postulaci|entrevista|publicaci)"),
    "conditions": re.compile(r"\b(contrato|remuneraci|honorario|sueldo|jornada|horario|modalidad|duraci|obligaci|funciones|periodo)"),
    "exclusions": re.compile(r"\b(no podra|no podr[aá]n|exclu|impedimento|incompatib|descalific|eliminad|no sera|inadmisible)"),
    "alerts": re.compile(r"\b(penalidad|exclusiv|renuncia|descalific|eliminad|sin derecho|no reembols|confidencial|disponibilidad inmediata|ad honorem|sin remuneraci|responsabilidad)"),
}
DATE_VALUE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d{1,2}\s+de\s+[a-z]+(?:\s+de\s+\d{4})?|\d{1,2}:\d{2})\b", re.I)


def _sentences(pages: list[PageText]):
    for page in pages:
        for raw in SENTENCE_RE.split(page.text):
            sentence = " ".join(raw.split()).strip(" -•\t")
            if 12 <= len(sentence) <= 650:
                yield page.page, sentence


def _collect(pages: list[PageText], pattern: re.Pattern, limit: int = 12, seen: set | None = None) -> list[Evidence]:
    if seen is None:
        seen = set()
    matches = []
    for page, sentence in _sentences(pages):
        key = normalize(sentence)
        if pattern.search(key) and key not in seen:
            seen.add(key)
            matches.append(Evidence(page, sentence))
    return matches[:limit]


def analyze_document(pages: list[PageText]) -> DocumentAnalysis:
    first_lines = [line.strip() for line in pages[0].text.splitlines() if line.strip()]
    title = first_lines[0][:120] if first_lines else "Convocatoria analizada"
    
    seen = set()
    requirements = _collect(pages, PATTERNS["requirements"], seen=seen)
    dates = _collect(pages, re.compile(PATTERNS["dates"].pattern + "|" + DATE_VALUE.pattern, re.I), seen=seen)
    conditions = _collect(pages, PATTERNS["conditions"], seen=seen)
    exclusions = _collect(pages, PATTERNS["exclusions"], seen=seen)
    alerts = _collect(pages, PATTERNS["alerts"], seen=seen)
    summary_parts = []
    if requirements:
        summary_parts.append(f"Se detectaron {len(requirements)} referencias a requisitos o perfil.")
    if dates:
        summary_parts.append(f"Se identificaron {len(dates)} menciones de fechas o plazos.")
    if conditions:
        summary_parts.append(f"Hay {len(conditions)} condiciones laborales o contractuales relevantes.")
    if alerts or exclusions:
        summary_parts.append(f"Conviene revisar {len(alerts) + len(exclusions)} posibles alertas o exclusiones.")
    if not summary_parts:
        summary_parts.append("El documento fue procesado, pero no se detectaron secciones tipicas con suficiente claridad.")
    return DocumentAnalysis(
        title=title,
        summary=" ".join(summary_parts),
        requirements=requirements,
        dates=dates,
        conditions=conditions,
        exclusions=exclusions,
        alerts=alerts,
    )
