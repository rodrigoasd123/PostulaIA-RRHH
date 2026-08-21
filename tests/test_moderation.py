from backend.moderation import BLOCKED_INPUT_MESSAGE, ModerationDecision, moderate_text


def test_moderation_is_deterministic_for_same_text():
    first = moderate_text("Eres un idiota")
    second = moderate_text("Eres un idiota")

    assert first == second
    assert isinstance(first, ModerationDecision)
    assert not first.allowed
    assert first.reason == "Lenguaje ofensivo detectado."
    assert first.matched_terms == ("idiota",)


def test_moderation_allows_professional_question():
    decision = moderate_text("¿Qué experiencia en Python tiene el candidato?")

    assert decision.allowed
    assert decision.reason == "Mensaje permitido."


def test_moderation_handles_accented_insults():
    decision = moderate_text("No seas estúpido, responde bien.")

    assert not decision.allowed
    assert decision.matched_terms == ("estupido",)
    assert BLOCKED_INPUT_MESSAGE.startswith("No puedo ayudar")