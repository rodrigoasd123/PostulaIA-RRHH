from __future__ import annotations

import os
import re
from typing import Sequence
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env automáticamente
load_dotenv()

from .models import AgentAnswer, Evidence, PageText
from .retrieval import LexicalRetriever

# Intentar importar dependencias de LangChain y Gemini
try:
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


def is_valid_gemini_key(key: str) -> bool:
    """Verifica que la clave tenga un formato válido de API Key de Google (largo >= 20 caracteres y sin espacios)."""
    return bool(key and len(key) >= 20 and " " not in key)


class HybridRAGEngine:
    def __init__(self, pages: list[PageText], gemini_api_key: str | None = None):
        self.pages = pages
        # Sanitizar estrictamente la API Key para evitar 'Illegal header value' en gRPC
        key_raw = (gemini_api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        self.gemini_api_key = re.sub(r'[\r\n\t\s"\']', '', key_raw)
        
        self.lexical_retriever = LexicalRetriever(pages)
        self.vectorstore = None
        self.llm = None

        if LANGCHAIN_AVAILABLE and is_valid_gemini_key(self.gemini_api_key):
            # 1. Inicializar modelo LLM Gemini 1.5 Flash (Free Tier)
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=self.gemini_api_key,
                    temperature=0.2
                )
            except Exception as exc:
                print(f"[RAG Engine Warning] No se pudo inicializar Gemini LLM: {exc}")
                self.llm = None

            # 2. Inicializar Embeddings (text-embedding-004) y VectorDB local (FAISS)
            try:
                documents = [
                    Document(page_content=p.text, metadata={"page": p.page})
                    for p in pages
                    if p.text.strip()
                ]
                
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                self.chunks = splitter.split_documents(documents)
                
                if self.chunks:
                    # Usar el modelo activo de embeddings: models/text-embedding-004
                    embeddings = GoogleGenerativeAIEmbeddings(
                        model="models/text-embedding-004",
                        google_api_key=self.gemini_api_key
                    )
                    self.vectorstore = FAISS.from_documents(self.chunks, embeddings)
            except Exception as exc:
                print(f"[RAG Engine Info] FAISS Vectorstore offline, usando buscador léxico con solapamiento: {exc}")
                self.vectorstore = None

    def search_evidence(self, question: str, limit: int = 4) -> list[Evidence]:
        """Busca evidencia usando VectorStore si existe, o cae a búsqueda léxica."""
        if self.vectorstore:
            try:
                docs_with_scores = self.vectorstore.similarity_search_with_score(question, k=limit)
                evidence = []
                for doc, score in docs_with_scores:
                    page_num = doc.metadata.get("page", 1)
                    evidence.append(Evidence(page=page_num, text=doc.page_content, score=float(score)))
                if evidence:
                    return evidence
            except Exception:
                pass
        return self.lexical_retriever.search(question, limit=limit)

    def ask_gemini(self, question: str, evidence: list[Evidence]) -> str | None:
        """Genera respuesta usando el LLM Gemini 1.5 Flash de LangChain."""
        if not self.llm or not evidence:
            return None

        context = "\n\n".join(f"[Página {e.page}] {e.text}" for e in evidence)
        prompt = (
            "Eres un asistente analista de convocatorias laborales y bases de postulación. "
            "Responde a la pregunta del usuario en español fluido y profesional utilizando ÚNICAMENTE el contexto proporcionado. "
            "Cita siempre las páginas de donde obtuviste la información con el formato [p. X]. "
            "Si no encuentras información suficiente en el documento, indícalo claramente sin inventar datos.\n\n"
            f"CONTEXTO EXTRAÍDO DEL PDF:\n{context}\n\n"
            f"PREGUNTA DEL USUARIO: {question}\n\n"
            "RESPUESTA:"
        )

        try:
            response = self.llm.invoke(prompt)
            return response.content.strip() if hasattr(response, "content") else str(response).strip()
        except Exception as exc:
            print(f"[RAG Engine Error] Fallo al consultar Gemini API: {exc}")
            return None

    @property
    def is_gemini_active(self) -> bool:
        return bool(self.llm and is_valid_gemini_key(self.gemini_api_key))
