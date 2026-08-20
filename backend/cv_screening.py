from __future__ import annotations

import re
from collections.abc import Mapping
from collections.abc import Callable

from .models import (
    CandidateReview,
    CriteriaExtraction,
    CriterionMatch,
    Evidence,
    PageText,
    ScreeningCriterion,
)
from .pdf_reader import PdfReadError, read_pdf
from .retrieval import chunks_from_pages, normalize, tokens


BOILERPLATE_TERMS = {
    "requisito",
    "requisitos",
    "obligatorio",
    "obligatorios",
    "indispensable",
    "indispensables",
    "perfil",
    "debera",
    "deberan",
    "contar",
    "requiere",
    "requerido",
    "requerida",
    "solicita",
}

# These criteria must never influence an employment screening score. The list is
# intentionally conservative; a human reviewer can still inspect the warning.
SENSITIVE_CRITERION_RE = re.compile(
    r"\b(edad|sexo|genero|estado civil|nacionalidad|religion|embarazo|gestante|"
    r"discapacidad|fotografia|foto carnet|raza|etnia|orientacion sexual|identidad de genero)\b"
)
REQUIREMENT_RE = re.compile(
    r"\b(requisit|experien|formaci|titulo|grado|colegiad|certific|conocim|"
    r"habilidad|perfil|debera contar|indispensable)"
)
CLAUSE_RE = re.compile(r"(?<=[.!?;])\s+|\n+")


def extract_criteria(profile_pages: list[PageText]) -> CriteriaExtraction:
    """Extract scoreable job requirements while excluding sensitive criteria."""

    criteria: list[ScreeningCriterion] = []
    excluded_sensitive: list[Evidence] = []
    seen: set[str] = set()

    requirement_evidence: list[Evidence] = []
    for page in profile_pages:
        for raw_clause in CLAUSE_RE.split(page.text):
            clause = " ".join(raw_clause.split()).strip(" -•\t")
            normalized_clause = normalize(clause)
            if 12 <= len(clause) <= 650 and REQUIREMENT_RE.search(normalized_clause):
                requirement_evidence.append(Evidence(page=page.page, text=clause))

    for evidence in requirement_evidence:
        normalized = normalize(evidence.text)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)

        if SENSITIVE_CRITERION_RE.search(normalized):
            excluded_sensitive.append(evidence)
            continue

        meaningful_terms = tuple(
            dict.fromkeys(term for term in tokens(evidence.text) if term not in BOILERPLATE_TERMS)
        )
        if not meaningful_terms:
            continue

        criteria.append(
            ScreeningCriterion(
                identifier=f"C-{len(criteria) + 1:03d}",
                text=evidence.text,
                page=evidence.page,
                terms=meaningful_terms,
            )
        )

    return CriteriaExtraction(criteria=criteria, excluded_sensitive=excluded_sensitive)


def _best_cv_evidence(pages: list[PageText], criterion: ScreeningCriterion) -> Evidence | None:
    criterion_terms = set(criterion.terms)
    best: Evidence | None = None
    for chunk in chunks_from_pages(pages):
        overlap = criterion_terms.intersection(tokens(chunk.text))
        if not overlap:
            continue
        score = len(overlap) / len(criterion_terms)
        if best is None or score > best.score or (score == best.score and chunk.page < best.page):
            best = Evidence(page=chunk.page, text=chunk.text, score=score)
    return best


def review_candidate(
    filename: str,
    pages: list[PageText],
    extraction: CriteriaExtraction,
) -> CandidateReview:
    """Calculate a deterministic documentary-coverage score for one CV."""

    candidate_terms = set(tokens("\n".join(page.text for page in pages)))
    matches: list[CriterionMatch] = []

    for criterion in extraction.criteria:
        matched = tuple(term for term in criterion.terms if term in candidate_terms)
        coverage = len(matched) / len(criterion.terms)
        if coverage >= 0.75:
            status = "Coincidencia alta"
        elif coverage >= 0.35:
            status = "Coincidencia parcial"
        else:
            status = "Sin evidencia suficiente"
        matches.append(
            CriterionMatch(
                criterion=criterion,
                coverage=coverage,
                status=status,
                matched_terms=matched,
                cv_evidence=_best_cv_evidence(pages, criterion),
            )
        )

    score = 0
    if matches:
        score = int((sum(match.coverage for match in matches) / len(matches)) * 100 + 0.5)
    return CandidateReview(filename=filename, score=score, matches=matches)


def screen_candidates(
    candidates: Mapping[str, list[PageText]],
    extraction: CriteriaExtraction,
) -> list[CandidateReview]:
    """Review and stably rank candidates by score, then filename."""

    reviews = [review_candidate(filename, pages, extraction) for filename, pages in candidates.items()]
    return sorted(reviews, key=lambda review: (-review.score, review.filename.casefold(), review.filename))


def load_candidate_documents(
    documents: Mapping[str, bytes],
    mode: str,
    max_bytes: int = 20 * 1024 * 1024,
    reader: Callable[[bytes, str], list[PageText]] = read_pdf,
) -> tuple[dict[str, list[PageText]], dict[str, str]]:
    """Read a CV batch while isolating validation and parser errors per file."""

    loaded: dict[str, list[PageText]] = {}
    errors: dict[str, str] = {}
    for filename, data in documents.items():
        if len(data) > max_bytes:
            errors[filename] = "El archivo supera el límite de 20 MB."
            continue
        try:
            loaded[filename] = reader(data, mode)
        except PdfReadError as exc:
            errors[filename] = str(exc)
    return loaded, errors


def build_review_context(profile_pages: list[PageText], cv_pages: list[PageText]) -> list[PageText]:
    """Build an in-memory RAG document with explicit source labels."""

    context: list[PageText] = []
    combined_page = 1
    for page in profile_pages:
        context.append(
            PageText(
                page=combined_page,
                text=f"[FUENTE: PERFIL DEL PUESTO, PÁGINA {page.page}]\n{page.text}",
            )
        )
        combined_page += 1
    for page in cv_pages:
        context.append(
            PageText(
                page=combined_page,
                text=f"[FUENTE: CV SELECCIONADO, PÁGINA {page.page}]\n{page.text}",
            )
        )
        combined_page += 1
    return context
