from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .models import Evidence


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    def answer(self, question: str, evidence: list[Evidence]) -> str | None:
        context = "\n\n".join(f"[Pagina {e.page}] {e.text}" for e in evidence)
        prompt = (
            "Eres un agente de postulacion responsable. Responde solo con el contexto proporcionado. "
            "No inventes datos. Si falta informacion, dilo claramente. Cita las paginas como [p. N].\n\n"
            f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}\nRESPUESTA:"
        )
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode()).get("response", "").strip() or None
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None
