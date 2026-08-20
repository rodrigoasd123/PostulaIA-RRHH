from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

from .models import Evidence, PageText

TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_+-]{1,}")
SENTENCE_RE = re.compile(r"(?<=[.!?;:])\s+|\n+")
STOPWORDS = {
    "para", "como", "esta", "este", "estos", "estas", "desde", "hasta", "sobre",
    "entre", "donde", "cuando", "cual", "cuales", "quien", "tiene", "debe", "del",
    "las", "los", "una", "uno", "unos", "unas", "que", "por", "con", "sin", "sus", "de",
    "son", "ser", "sea", "se", "al", "el", "la", "un", "y", "o", "en", "es", "mi",
}


def normalize(value: str) -> str:
    value = value.replace("|", " ")
    value = unicodedata.normalize("NFKD", value.lower())
    clean = "".join(ch for ch in value if not unicodedata.combining(ch))
    return " ".join(clean.split())


def tokens(value: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(normalize(value)) if t not in STOPWORDS]


def chunks_from_pages(pages: list[PageText], max_chars: int = 900, overlap_chars: int = 150) -> list[Evidence]:
    chunks: list[Evidence] = []
    for page in pages:
        current = ""
        sentences = [s.strip() for s in SENTENCE_RE.split(page.text) if s.strip()]
        for idx, sentence in enumerate(sentences):
            sentence_clean = " ".join(sentence.split()).strip()
            if not sentence_clean:
                continue
            if current and len(current) + len(sentence_clean) + 1 > max_chars:
                chunks.append(Evidence(page.page, current))
                # Preservar parte del texto anterior como solapamiento (overlap)
                overlap_text = current[-overlap_chars:] if len(current) > overlap_chars else current
                current = f"{overlap_text} {sentence_clean}".strip()
            else:
                current = f"{current} {sentence_clean}".strip()
        if current:
            chunks.append(Evidence(page.page, current))
    return chunks


class LexicalRetriever:
    def __init__(self, pages: list[PageText]):
        self.chunks = chunks_from_pages(pages)
        self.term_counts = [Counter(tokens(chunk.text)) for chunk in self.chunks]
        self.doc_freq = Counter(term for counts in self.term_counts for term in counts)

    def search(self, query: str, limit: int = 4) -> list[Evidence]:
        query_terms = tokens(query)
        if not query_terms:
            return []
        total = max(len(self.chunks), 1)
        ranked: list[Evidence] = []
        for chunk, counts in zip(self.chunks, self.term_counts):
            length_norm = 1 + 0.15 * math.log1p(sum(counts.values()))
            score = 0.0
            for term in query_terms:
                tf = counts.get(term, 0)
                if tf:
                    idf = math.log((total + 1) / (self.doc_freq[term] + 0.5)) + 1
                    score += (1 + math.log(tf)) * idf
            if score:
                ranked.append(Evidence(chunk.page, chunk.text, score / length_norm))
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:limit]
