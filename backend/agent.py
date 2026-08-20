from __future__ import annotations

from .analyzer import analyze_document
from .llm import OllamaClient
from .models import AgentAnswer, DocumentAnalysis, PageText
from .rag_engine import HybridRAGEngine


class ApplicationAgent:
    def __init__(
        self,
        pages: list[PageText],
        use_ollama: bool = False,
        gemini_api_key: str | None = None,
        use_remote_embeddings: bool = True,
    ):
        self.pages = pages
        self.analysis: DocumentAnalysis = analyze_document(pages)
        self.use_ollama = use_ollama
        self.gemini_api_key = gemini_api_key
        self.rag_engine = HybridRAGEngine(
            pages,
            gemini_api_key=gemini_api_key,
            use_remote_embeddings=use_remote_embeddings,
        )
        self.llm = OllamaClient()

    def ask(self, question: str) -> AgentAnswer:
        evidence = self.rag_engine.search_evidence(question, limit=4)
        if not evidence:
            return AgentAnswer(
                "No encontre informacion suficiente en el documento para responder esa pregunta.",
                [],
                False,
            )

        # 1. Intentar respuesta con Gemini API (si se proporcionó clave)
        if self.gemini_api_key:
            gemini_ans = self.rag_engine.ask_gemini(question, evidence)
            if gemini_ans:
                return AgentAnswer(gemini_ans, evidence, True)

        # 2. Intentar respuesta con Ollama Local (si está activado)
        if self.use_ollama:
            generated = self.llm.answer(question, evidence)
            if generated:
                return AgentAnswer(generated, evidence, True)

        # 3. Respuesta determinística por búsqueda léxica con citas de página
        extracts = []
        for item in evidence[:3]:
            text = item.text if len(item.text) <= 420 else item.text[:417].rstrip() + "..."
            extracts.append(f"- {text} [p. {item.page}]")
        answer = (
            "Esto es lo mas relevante que encontre en la convocatoria:\n\n"
            + "\n".join(extracts)
            + "\n\nLa respuesta se basa unicamente en el PDF. Revisa los fragmentos citados antes de tomar una decision."
        )
        return AgentAnswer(answer, evidence, True)
