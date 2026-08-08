from __future__ import annotations

import sqlite3
from pathlib import Path


class QueryHistory:
    def __init__(self, path: str | Path = "data/agente_postulacion.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY, document TEXT, question TEXT, answer TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )

    def _connect(self):
        return sqlite3.connect(self.path)

    def add(self, document: str, question: str, answer: str) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO queries(document, question, answer) VALUES (?, ?, ?)",
                (document, question, answer),
            )

    def recent(self, limit: int = 10):
        with self._connect() as db:
            return db.execute(
                "SELECT document, question, answer, created_at FROM queries ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
