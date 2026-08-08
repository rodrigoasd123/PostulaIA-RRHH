from __future__ import annotations

from .analyzer import analyze_document
from .llm import OllamaClient
from .models import AgentAnswer, DocumentAnalysis, PageText
from .retrieval import LexicalRetriever


class ApplicationAgent:
    def __init__(self, pages: list[PageText], use_ollama: bool = False):
        self.pages = pages
        self.analysis: DocumentAnalysis = analyze_document(pages)
        self.retriever = LexicalRetriever(pages)
        self.use_ollama = use_ollama
        self.llm = OllamaClient()

    def ask(self, question: str) -> AgentAnswer:
        evidence = self.retriever.search(question, limit=4)
        if not evidence:
            return AgentAnswer(
                "No encontre informacion suficiente en el documento para responder esa pregunta.",
                [],
                False,
            )
        if self.use_ollama:
            generated = self.llm.answer(question, evidence)
            if generated:
                return AgentAnswer(generated, evidence, True)
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
