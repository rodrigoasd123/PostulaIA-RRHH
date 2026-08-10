"""Compatibilidad con la nueva estructura backend."""
from backend import ApplicationAgent, QueryHistory, Evidence, PageText, PdfReadError, read_pdf

__all__ = ["ApplicationAgent", "QueryHistory", "Evidence", "PageText", "PdfReadError", "read_pdf"]
