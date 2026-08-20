from backend import rag_engine
from backend.models import PageText
from backend.rag_engine import (
    DEFAULT_FREE_GEMINI_MODEL,
    FREE_GEMINI_MODELS,
    HybridRAGEngine,
    resolve_free_gemini_models,
)


def test_default_model_is_free_flash_lite(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    models = resolve_free_gemini_models()

    assert models[0] == DEFAULT_FREE_GEMINI_MODEL
    assert all("flash-lite" in model for model in models)
    assert all("pro" not in model.lower() for model in models)


def test_pro_model_configuration_is_rejected(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.1-pro-preview")

    models = resolve_free_gemini_models()

    assert models == FREE_GEMINI_MODELS
    assert "gemini-3.1-pro-preview" not in models


def test_hr_mode_does_not_create_remote_embeddings(monkeypatch):
    class FakeChatModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ForbiddenEmbeddings:
        def __init__(self, **kwargs):
            raise AssertionError("Los embeddings remotos no deben crearse para CV")

    monkeypatch.setattr(rag_engine, "LANGCHAIN_AVAILABLE", True)
    monkeypatch.setattr(rag_engine, "ChatGoogleGenerativeAI", FakeChatModel)
    monkeypatch.setattr(rag_engine, "GoogleGenerativeAIEmbeddings", ForbiddenEmbeddings)

    engine = HybridRAGEngine(
        [PageText(1, "Experiencia con Python")],
        gemini_api_key="x" * 24,
        use_remote_embeddings=False,
    )

    assert engine.llm is not None
    assert engine.vectorstore is None
