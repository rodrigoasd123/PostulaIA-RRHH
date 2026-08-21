from __future__ import annotations

from .analyzer import analyze_document
from .cache_models import CacheContext, DocumentIdentity
from .cache_service import CacheService
from .llm import OllamaClient
from .moderation import BLOCKED_INPUT_MESSAGE, BLOCKED_OUTPUT_MESSAGE, moderate_text
from .models import AgentAnswer, DocumentAnalysis, Evidence, PageText
from .rag_engine import HybridRAGEngine


_CONVERSATIONAL_RESPONSES = {
    "hola": (
        "¡Hola! Puedo ayudarte a revisar cómo el CV seleccionado se relaciona con el perfil "
        "del puesto. Por ejemplo: ¿Qué experiencia del CV respalda el requisito de Python?"
    ),
    "buenas": "¡Hola! Puedo ayudarte a revisar la evidencia documental del CV frente al perfil.",
    "qué puedes hacer": (
        "Puedo responder preguntas sobre la evidencia del CV seleccionado frente al perfil del "
        "puesto. Por ejemplo: ¿El CV muestra experiencia en SQL?"
    ),
    "que puedes hacer": (
        "Puedo responder preguntas sobre la evidencia del CV seleccionado frente al perfil del "
        "puesto. Por ejemplo: ¿El CV muestra experiencia en SQL?"
    ),
    "para qué sirve este agente": (
        "Puedo responder preguntas sobre la evidencia del CV seleccionado frente al perfil del "
        "puesto. Por ejemplo: ¿El CV muestra experiencia en SQL?"
    ),
    "para que sirve este agente": (
        "Puedo responder preguntas sobre la evidencia del CV seleccionado frente al perfil del "
        "puesto. Por ejemplo: ¿El CV muestra experiencia en SQL?"
    ),
    "gracias": "¡De nada! Si quieres, puedo ayudarte a revisar otro requisito del perfil.",
    "muchas gracias": "¡De nada! Si quieres, puedo ayudarte a revisar otro requisito del perfil.",
    "adiós": "¡Hasta luego! Cuando quieras, puedo ayudarte a revisar la evidencia documental del CV.",
    "hasta luego": "¡Hasta luego! Cuando quieras, puedo ayudarte a revisar la evidencia documental del CV.",
}


class ApplicationAgent:
    def __init__(
        self,
        pages: list[PageText],
        use_ollama: bool = False,
        gemini_api_key: str | None = None,
        use_remote_embeddings: bool = True,
        cache_service: CacheService | None = None,
        cache_profile_hash: str | None = None,
        cache_cv_hash: str | None = None,
        profile_identity: DocumentIdentity | None = None,
        cv_identity: DocumentIdentity | None = None,
    ):
        self.pages = pages
        self.analysis: DocumentAnalysis = analyze_document(pages)
        self.use_ollama = use_ollama
        self.gemini_api_key = gemini_api_key
        self.cache_service = cache_service
        self.cache_profile_hash = cache_profile_hash
        self.cache_cv_hash = cache_cv_hash
        self.profile_identity = profile_identity
        self.cv_identity = cv_identity
        self.rag_engine = HybridRAGEngine(
            pages,
            gemini_api_key=gemini_api_key,
            use_remote_embeddings=use_remote_embeddings,
        )
        self.llm = OllamaClient()

    def _wrap_answer(self, answer: str, evidence: list[Evidence], origin: str = "local") -> AgentAnswer:
        decision = moderate_text(answer)
        if not decision.allowed:
            return AgentAnswer(BLOCKED_OUTPUT_MESSAGE, [], False, origin="blocked")
        return AgentAnswer(answer, evidence, True, origin=origin)

    def _cache_context(self, response_route: str) -> CacheContext | None:
        if not self.cache_service or not self.cache_profile_hash or not self.cache_cv_hash:
            return None
        return CacheContext(
            profile_hash=self.cache_profile_hash,
            cv_hash=self.cache_cv_hash,
            response_route=response_route,
        )

    def _candidate_routes(self) -> list[str]:
        routes: list[str] = []
        if self.gemini_api_key:
            routes.extend(f"gemini:{model}" for model in self.rag_engine.free_gemini_models)
        if self.use_ollama:
            routes.append(f"ollama:{self.llm.model}")
        routes.append("local:extractive-v1")
        return routes

    def _cached_answer(self, question: str) -> AgentAnswer | None:
        if not self.cache_service:
            return None
        completed_lookup = False
        for route in self._candidate_routes():
            context = self._cache_context(route)
            if context is None:
                continue
            try:
                cached = self.cache_service.get_response(context, question)
            except Exception:
                continue
            completed_lookup = True
            if cached is None:
                continue
            decision = moderate_text(cached.answer)
            if not decision.allowed:
                return AgentAnswer(BLOCKED_OUTPUT_MESSAGE, [], False, origin="blocked")
            try:
                self.cache_service.record_response_hit(context, cached)
            except Exception:
                pass
            return AgentAnswer(cached.answer, list(cached.evidence), True, origin="cache")
        if completed_lookup:
            try:
                self.cache_service.record_response_miss()
            except Exception:
                pass
        return None

    def _store_answer(self, route: str, question: str, result: AgentAnswer) -> None:
        if not self.cache_service or not result.found or result.origin == "blocked":
            return
        context = self._cache_context(route)
        if context is None:
            return
        try:
            self.cache_service.store_response(context, question, result.answer, result.evidence)
        except Exception:
            return

    def _search_evidence(self, question: str) -> list[Evidence]:
        if self.cache_service:
            try:
                evidence = self.cache_service.search(
                    self.profile_identity,
                    self.cv_identity,
                    question,
                    limit=4,
                )
                if evidence:
                    return evidence
            except Exception:
                pass
        return self.rag_engine.search_evidence(question, limit=4)

    def ask(self, question: str) -> AgentAnswer:
        decision = moderate_text(question)
        if not decision.allowed:
            return AgentAnswer(BLOCKED_INPUT_MESSAGE, [], False, origin="blocked")

        normalized_question = question.casefold().strip().strip("¡!¿?.,")
        conversational_reply = _CONVERSATIONAL_RESPONSES.get(normalized_question)
        if conversational_reply:
            return AgentAnswer(conversational_reply, [], False, origin="local")

        cached = self._cached_answer(question)
        if cached:
            return cached

        evidence = self._search_evidence(question)
        if not evidence:
            return AgentAnswer(
                "No encontre informacion suficiente en el documento para responder esa pregunta.",
                [],
                False,
                origin="local",
            )

        if self.gemini_api_key:
            gemini_ans = self.rag_engine.ask_gemini(question, evidence)
            if gemini_ans:
                result = self._wrap_answer(gemini_ans, evidence, origin="generated")
                model = self.rag_engine.last_gemini_model or self.rag_engine.gemini_model
                self._store_answer(f"gemini:{model}", question, result)
                return result

        if self.use_ollama:
            generated = self.llm.answer(question, evidence)
            if generated:
                result = self._wrap_answer(generated, evidence, origin="generated")
                self._store_answer(f"ollama:{self.llm.model}", question, result)
                return result

        extracts = []
        for item in evidence[:3]:
            text = item.text if len(item.text) <= 420 else item.text[:417].rstrip() + "..."
            extracts.append(f"- {text} [p. {item.page}]")
        answer = (
            "Esto es lo mas relevante que encontre en la convocatoria:\n\n"
            + "\n".join(extracts)
            + "\n\nLa respuesta se basa unicamente en el PDF. Revisa los fragmentos citados antes de tomar una decision."
        )
        result = self._wrap_answer(answer, evidence, origin="local")
        self._store_answer("local:extractive-v1", question, result)
        return result
