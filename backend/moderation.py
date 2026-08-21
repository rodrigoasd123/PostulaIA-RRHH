from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", stripped).strip()


@dataclass(frozen=True)
class ModerationDecision:
    allowed: bool
    reason: str
    matched_terms: tuple[str, ...] = ()


_OFFENSIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bidiot[oa]s?\b"), "idiota"),
    (re.compile(r"\bestupid[oa]s?\b"), "estupido"),
    (re.compile(r"\bimbecil(?:es)?\b"), "imbecil"),
    (re.compile(r"\btarad[ao]s?\b"), "tarado"),
    (re.compile(r"\bpendej[oa]s?\b"), "pendejo"),
    (re.compile(r"\bbasura\b"), "basura"),
    (re.compile(r"\bmierda\b"), "mierda"),
    (re.compile(r"\bputa?s?\b"), "puta"),
    (re.compile(r"\bputo?s?\b"), "puto"),
    (re.compile(r"\basshole\b"), "asshole"),
    (re.compile(r"\bbitch\b"), "bitch"),
    (re.compile(r"\bfuck\b"), "fuck"),
    (re.compile(r"\bshut up\b"), "shut up"),
    (re.compile(r"\bgo to hell\b"), "go to hell"),
    (re.compile(r"\bvete al carajo\b"), "vete al carajo"),
    (re.compile(r"\bcierra la boca\b"), "cierra la boca"),
    (re.compile(r"\bcallate\b"), "callate"),
    (re.compile(r"\bte odio\b"), "te odio"),
)


BLOCK_REASON = "Lenguaje ofensivo detectado."
BLOCKED_INPUT_MESSAGE = (
    "No puedo ayudar con ese mensaje. Reformúlalo de forma respetuosa y profesional."
)
BLOCKED_OUTPUT_MESSAGE = (
    "No puedo mostrar esa respuesta. Reformula la consulta de forma respetuosa."
)


def moderate_text(text: str) -> ModerationDecision:
    normalized = _normalize_text(text)
    for pattern, term in _OFFENSIVE_PATTERNS:
        if pattern.search(normalized):
            return ModerationDecision(
                allowed=False,
                reason=BLOCK_REASON,
                matched_terms=(term,),
            )
    return ModerationDecision(allowed=True, reason="Mensaje permitido.")
