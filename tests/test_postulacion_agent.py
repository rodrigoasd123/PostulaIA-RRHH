from backend.agent import ApplicationAgent
from backend.models import PageText


PAGES = [
    PageText(1, "Convocatoria Analista de Datos. Requisito obligatorio: título universitario y dos años de experiencia en Python."),
    PageText(2, "La postulación vence el 30/08/2026 a las 18:00. Contrato por tres meses. Quedará descalificado quien entregue documentos incompletos."),
]


def test_analysis_extracts_key_categories():
    analysis = ApplicationAgent(PAGES).analysis
    assert analysis.requirements
    assert analysis.dates
    assert analysis.conditions
    assert analysis.exclusions or analysis.alerts


def test_answer_contains_page_citation():
    result = ApplicationAgent(PAGES).ask("¿Cuál es la fecha límite de postulación?")
    assert result.found
    assert "[p. 2]" in result.answer


def test_unknown_question_is_honest():
    result = ApplicationAgent(PAGES).ask("¿Cuál es el color del uniforme?")
    assert not result.found
    assert "No encontre informacion suficiente" in result.answer
