# Plan — SPEC-002

## Resumen técnico

Se añadió una clasificación local y determinista de interacción conversacional básica en `ApplicationAgent`. El flujo quedó: moderación existente → clasificación conversacional → recuperación documental y generación opcional. Las respuestas conversacionales no incluyen evidencia ni afirman hallazgos documentales.

## Componentes afectados

| Componente | Cambio |
|---|---|
| `backend/agent.py` | Respuestas locales para saludo, ayuda, agradecimiento y despedida antes de `search_evidence`. |
| `tests/test_postulacion_agent.py` | Pruebas de saludo, ayuda, agradecimiento y precedencia de moderación. |
| `frontend/streamlit_postulacion.py` | Sin cambios: renderiza el contrato `AgentAnswer` existente. |

## Decisiones

- Reglas locales y exactas para mensajes breves: sin red, sin proveedor y reproducibles.
- Moderación antes de la cortesía: un saludo ofensivo continúa bloqueado.
- Consultas documentales conservan Gemini opcional, Ollama opcional y fallback extractivo.

## Compatibilidad y reversión

No hay datos, dependencias, configuración ni API nuevos. Para revertir, retirar `_CONVERSATIONAL_RESPONSES` y su rama previa a `search_evidence` en `backend/agent.py`.

## Evidencia

| AC | Evidencia |
|---|---|
| AC-001 | Prueba de saludo sin búsqueda de evidencia. |
| AC-002 | Prueba de ayuda sin búsqueda de evidencia. |
| AC-003 | Prueba de agradecimiento sin búsqueda de evidencia. |
| AC-004 | Prueba de saludo ofensivo bloqueado antes de la búsqueda. |
| AC-005 | Suite completa: `python -m pytest -q` → 26 passed. |

## Aprobación

- [x] Plan aprobado implícitamente al autorizar la implementación el 2026-08-20.
