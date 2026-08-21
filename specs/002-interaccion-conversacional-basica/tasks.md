# Tareas — SPEC-002

- [x] **T-001 — Clasificar y responder interacciones conversacionales locales**
  - Cubre: FR-001 a FR-004, FR-006, NFR-001, NFR-002, SEC-001, SEC-002; AC-001 a AC-004.
  - Archivos: `backend/agent.py`.
  - Evidencia: respuestas locales antes de la recuperación; moderación con precedencia.

- [x] **T-002 — Probar la nueva ruta y preservar consultas documentales**
  - Cubre: FR-005; AC-001 a AC-005.
  - Archivos: `tests/test_postulacion_agent.py`.
  - Evidencia: `python -m pytest -q` → 26 passed en 1.19 s.

- [x] **T-003 — Registrar evidencia y actualizar estado**
  - Cubre: todos los requisitos y criterios de aceptación.
  - Archivos: `spec.md`, `plan.md`, `tasks.md`.

## Puertas de salida

- [x] Todos los requisitos obligatorios están cubiertos.
- [x] No quedan bloqueantes.
- [x] Existe estrategia de reversión.
