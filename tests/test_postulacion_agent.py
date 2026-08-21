from backend.agent import ApplicationAgent
from backend.cache_models import CachedResponse
from backend.moderation import BLOCKED_INPUT_MESSAGE, BLOCKED_OUTPUT_MESSAGE
from backend.models import Evidence, PageText


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


def test_offensive_question_is_blocked_before_search(monkeypatch):
    agent = ApplicationAgent(PAGES)

    def fail_search(*args, **kwargs):
        raise AssertionError("search_evidence no debe ejecutarse para mensajes ofensivos")

    monkeypatch.setattr(agent.rag_engine, "search_evidence", fail_search)

    result = agent.ask("Eres un idiota")

    assert not result.found
    assert result.answer == BLOCKED_INPUT_MESSAGE


def test_offensive_generated_answer_is_sanitized(monkeypatch):
    agent = ApplicationAgent(PAGES)
    monkeypatch.setattr(
        agent.rag_engine,
        "search_evidence",
        lambda question, limit=4: [Evidence(page=1, text="Evidencia sobre Python", score=1.0)],
    )
    monkeypatch.setattr(agent.rag_engine, "ask_gemini", lambda question, evidence: "Eres un idiota")
    agent.gemini_api_key = "x" * 20

    result = agent.ask("¿Qué evidencia existe sobre Python?")

    assert not result.found
    assert result.answer == BLOCKED_OUTPUT_MESSAGE

def test_greeting_returns_oriented_message_without_search(monkeypatch):
    agent = ApplicationAgent(PAGES)

    def fail_search(*args, **kwargs):
        raise AssertionError("No debe buscar evidencia para un saludo")

    monkeypatch.setattr(agent.rag_engine, "search_evidence", fail_search)
    result = agent.ask("Hola")

    assert not result.found
    assert "CV seleccionado" in result.answer
    assert "Python" in result.answer


def test_help_request_returns_usage_without_search(monkeypatch):
    agent = ApplicationAgent(PAGES)

    def fail_search(*args, **kwargs):
        raise AssertionError("No debe buscar evidencia para una solicitud de ayuda")

    monkeypatch.setattr(agent.rag_engine, "search_evidence", fail_search)
    result = agent.ask("¿Qué puedes hacer?")

    assert not result.found
    assert "perfil" in result.answer
    assert "SQL" in result.answer


def test_thanks_returns_brief_professional_message_without_search(monkeypatch):
    agent = ApplicationAgent(PAGES)

    def fail_search(*args, **kwargs):
        raise AssertionError("No debe buscar evidencia para un agradecimiento")

    monkeypatch.setattr(agent.rag_engine, "search_evidence", fail_search)
    result = agent.ask("Muchas gracias")

    assert not result.found
    assert "De nada" in result.answer


def test_offensive_greeting_is_blocked_before_conversation_search(monkeypatch):
    agent = ApplicationAgent(PAGES)

    def fail_search(*args, **kwargs):
        raise AssertionError("No debe buscar evidencia para un mensaje bloqueado")

    monkeypatch.setattr(agent.rag_engine, "search_evidence", fail_search)
    result = agent.ask("Hola idiota")

    assert not result.found
    assert result.answer == BLOCKED_INPUT_MESSAGE


def test_agent_purpose_question_returns_usage_without_search(monkeypatch):
    agent = ApplicationAgent(PAGES)

    def fail_search(*args, **kwargs):
        raise AssertionError("No debe buscar evidencia para una pregunta sobre el propósito del agente")

    monkeypatch.setattr(agent.rag_engine, "search_evidence", fail_search)
    result = agent.ask("para que sirve este agente?")

    assert not result.found
    assert "perfil" in result.answer
    assert "SQL" in result.answer


class StubCacheService:
    def __init__(self, cached: CachedResponse | None = None):
        self.cached = cached
        self.get_calls = 0
        self.search_calls = 0
        self.stored = []
        self.hit_calls = []
        self.miss_calls = 0

    def get_response(self, context, question):
        self.get_calls += 1
        return self.cached

    def search(self, profile_identity, cv_identity, question, limit=4):
        self.search_calls += 1
        return []

    def store_response(self, context, question, answer, evidence):
        self.stored.append((context, question, answer, evidence))
        return True

    def record_response_hit(self, context, response):
        self.hit_calls.append((context, response))

    def record_response_miss(self):
        self.miss_calls += 1


def test_cached_answer_avoids_retrieval_and_model(monkeypatch):
    cache = StubCacheService(
        CachedResponse(
            answer="Respuesta cacheada con evidencia.",
            evidence=(Evidence(page=1, text="Python", score=1.0),),
            match_type="exact",
            similarity=1.0,
        )
    )
    agent = ApplicationAgent(
        PAGES,
        cache_service=cache,
        cache_profile_hash="profile",
        cache_cv_hash="cv",
        use_remote_embeddings=False,
    )
    monkeypatch.setattr(
        agent.rag_engine,
        "search_evidence",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("No debe buscar")),
    )

    result = agent.ask("¿Qué evidencia existe sobre Python?")

    assert result.origin == "cache"
    assert result.answer == "Respuesta cacheada con evidencia."
    assert cache.get_calls == 1
    assert cache.search_calls == 0
    assert len(cache.hit_calls) == 1
    assert cache.miss_calls == 0


def test_offensive_input_never_reads_or_writes_cache():
    cache = StubCacheService()
    agent = ApplicationAgent(
        PAGES,
        cache_service=cache,
        cache_profile_hash="profile",
        cache_cv_hash="cv",
        use_remote_embeddings=False,
    )

    result = agent.ask("Hola idiota")

    assert result.answer == BLOCKED_INPUT_MESSAGE
    assert cache.get_calls == 0
    assert cache.search_calls == 0
    assert cache.stored == []
    assert cache.hit_calls == []
    assert cache.miss_calls == 0


def test_offensive_cached_output_is_blocked():
    cache = StubCacheService(
        CachedResponse(
            answer="Eres un idiota",
            evidence=(Evidence(page=1, text="Python"),),
            match_type="exact",
            similarity=1.0,
        )
    )
    agent = ApplicationAgent(
        PAGES,
        cache_service=cache,
        cache_profile_hash="profile",
        cache_cv_hash="cv",
        use_remote_embeddings=False,
    )

    result = agent.ask("¿Qué evidencia existe sobre Python?")

    assert not result.found
    assert result.origin == "blocked"
    assert result.answer == BLOCKED_OUTPUT_MESSAGE
    assert cache.hit_calls == []
    assert cache.miss_calls == 0


def test_cache_miss_is_recorded_once_after_all_routes(monkeypatch):
    cache = StubCacheService()
    agent = ApplicationAgent(
        PAGES,
        gemini_api_key="fake-key",
        use_ollama=True,
        cache_service=cache,
        cache_profile_hash="profile",
        cache_cv_hash="cv",
        use_remote_embeddings=False,
    )
    monkeypatch.setattr(agent, "_search_evidence", lambda question: [])

    agent.ask("¿Qué evidencia existe sobre Rust?")

    assert cache.get_calls > 1
    assert cache.miss_calls == 1
    assert cache.hit_calls == []
