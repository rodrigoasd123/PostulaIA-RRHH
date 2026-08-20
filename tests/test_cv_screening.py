from backend.agent import ApplicationAgent
from backend.cv_screening import (
    build_review_context,
    extract_criteria,
    load_candidate_documents,
    review_candidate,
    screen_candidates,
)
from backend.models import PageText


PROFILE = [
    PageText(
        1,
        "Analista de Datos. Requisito obligatorio: experiencia de dos años con Python y SQL. "
        "Requisito obligatorio: título universitario en Ingeniería de Sistemas.",
    )
]


def test_extracts_requirements_with_profile_page():
    extraction = extract_criteria(PROFILE)

    assert len(extraction.criteria) == 2
    assert extraction.criteria[0].identifier == "C-001"
    assert extraction.criteria[0].page == 1
    assert "python" in extraction.criteria[0].terms


def test_candidate_score_and_evidence_are_explainable_and_deterministic():
    extraction = extract_criteria(PROFILE)
    pages = [
        PageText(1, "Profesional con dos años de experiencia desarrollando soluciones en Python y SQL."),
        PageText(2, "Título universitario de Ingeniería de Sistemas."),
    ]

    first = review_candidate("ana.pdf", pages, extraction)
    second = review_candidate("ana.pdf", pages, extraction)

    assert first.score == second.score
    assert first.score >= 80
    assert all(match.cv_evidence is not None for match in first.matches)
    assert first.matches[0].status == "Coincidencia alta"
    assert first.matches[0].cv_evidence.page == 1


def test_ranking_uses_score_then_filename_as_stable_tiebreaker():
    extraction = extract_criteria(PROFILE)
    complete = [PageText(1, "Dos años de experiencia con Python y SQL. Título universitario en Ingeniería de Sistemas.")]
    partial = [PageText(1, "Experiencia en Python.")]
    tied = {"zoe.pdf": complete, "bea.pdf": partial, "ana.pdf": complete}

    ranked = screen_candidates(tied, extraction)

    assert [review.filename for review in ranked] == ["ana.pdf", "zoe.pdf", "bea.pdf"]
    assert ranked[0].score == ranked[1].score


def test_sensitive_requirement_is_excluded_from_score_and_reported():
    pages = [
        PageText(
            1,
            "Requisito obligatorio: experiencia en atención al cliente. "
            "Requisito obligatorio: edad mínima de 25 años y fotografía reciente.",
        )
    ]

    extraction = extract_criteria(pages)

    assert len(extraction.criteria) == 1
    assert len(extraction.excluded_sensitive) == 1
    assert "edad" in extraction.excluded_sensitive[0].text.lower()


def test_profile_without_requirements_does_not_invent_criteria():
    extraction = extract_criteria([PageText(1, "Nuestra empresa inició operaciones en Lima en 2020.")])

    assert extraction.criteria == []
    assert review_candidate("cv.pdf", [PageText(1, "Python")], extraction).score == 0


def test_invalid_cv_is_isolated_without_blocking_valid_candidates():
    def fake_reader(data: bytes, mode: str):
        if data == b"bad":
            from backend.pdf_reader import PdfReadError

            raise PdfReadError("PDF ilegible")
        return [PageText(1, "Experiencia en Python")]

    loaded, errors = load_candidate_documents(
        {"valido.pdf": b"ok", "danado.pdf": b"bad"},
        "normal",
        reader=fake_reader,
    )

    assert list(loaded) == ["valido.pdf"]
    assert errors == {"danado.pdf": "PDF ilegible"}


def test_review_context_labels_profile_and_selected_cv_without_persistence():
    context = build_review_context(
        [PageText(2, "Requisito: Python")],
        [PageText(3, "Experiencia con Python")],
    )

    assert context[0].page == 1
    assert "PERFIL DEL PUESTO, PÁGINA 2" in context[0].text
    assert context[1].page == 2
    assert "CV SELECCIONADO, PÁGINA 3" in context[1].text


def test_local_agent_answers_from_labeled_profile_and_cv_context():
    context = build_review_context(
        [PageText(1, "Requisito obligatorio: experiencia en Python.")],
        [PageText(2, "Experiencia demostrable desarrollando servicios con Python.")],
    )

    result = ApplicationAgent(
        context,
        gemini_api_key="",
        use_remote_embeddings=False,
    ).ask("¿Qué evidencia existe sobre Python?")

    assert result.found
    assert "FUENTE:" in result.answer
    assert "[p." in result.answer
