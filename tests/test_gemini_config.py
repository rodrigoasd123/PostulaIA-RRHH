from backend.rag_engine import (
    DEFAULT_FREE_GEMINI_MODEL,
    FREE_GEMINI_MODELS,
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
