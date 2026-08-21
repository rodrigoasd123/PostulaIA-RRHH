# Tareas — Filtro de lenguaje ofensivo para el agente

## T-001 — Crear contrato de moderación local

- **Objetivo:** introducir un contrato puro y determinista para decidir si un texto se permite o se bloquea.
- **Archivos:** `backend/moderation.py`.
- **Cubre:** FR-001, FR-003, NFR-001, NFR-002, SEC-002, SEC-004.
- **Evidencia esperada:** prueba unitaria que devuelve la misma decisión para el mismo texto y la misma configuración.

## T-002 — Bloquear entrada ofensiva antes de consultar el agente

- **Objetivo:** interceptar mensajes ofensivos en `ApplicationAgent.ask()` antes de buscar evidencia o llamar a modelos.
- **Archivos:** `backend/agent.py`.
- **Cubre:** FR-001, FR-002, SEC-001.
- **Evidencia esperada:** prueba que confirma que `search_evidence` no se invoca cuando el mensaje es ofensivo.

## T-003 — Validar y sanear la salida del agente

- **Objetivo:** revisar la respuesta generada y reemplazarla por una salida neutral si contiene lenguaje ofensivo.
- **Archivos:** `backend/agent.py`.
- **Cubre:** FR-004, NFR-004, SEC-001.
- **Evidencia esperada:** prueba con una respuesta simulada ofensiva que termina bloqueada o sustituida.

## T-004 — Mantener intacto el flujo de Streamlit

- **Objetivo:** asegurar que la interfaz de RR. HH. sigue mostrando el mensaje neutral y conserva el contexto del chat.
- **Archivos:** `frontend/streamlit_postulacion.py`.
- **Cubre:** FR-002, FR-003, FR-005.
- **Evidencia esperada:** verificación manual o prueba de integración de que el hilo no se reinicia al bloquearse un mensaje.

## T-005 — Añadir pruebas de moderación y regresión del chat

- **Objetivo:** cubrir insulto directo, falso positivo, salida ofensiva y consulta normal sin regresión.
- **Archivos:** `tests/test_moderation.py`, `tests/test_postulacion_agent.py`.
- **Cubre:** FR-001 a FR-006, NFR-001 a NFR-004, SEC-001 a SEC-004.
- **Evidencia esperada:** pytest verde sin red.

## T-006 — Confirmar que la revisión de CV no cambia

- **Objetivo:** ejecutar la regresión existente para demostrar que el ranking y la evidencia documental siguen igual.
- **Archivos:** `tests/test_cv_screening.py`.
- **Cubre:** FR-006, NFR-003.
- **Evidencia esperada:** suite completa exitosa y sin cambios en los casos de CV.

## Secuencia de ejecución

1. T-001
2. T-002
3. T-003
4. T-004
5. T-005
6. T-006

## Riesgos y mitigaciones

- Riesgo: falsos positivos en lenguaje ambiguo. Mitigación: pruebas específicas y política conservadora.
- Riesgo: bloquear texto ofensivo solo en la entrada y olvidar la salida. Mitigación: tareas separadas para entrada y salida.
- Riesgo: tocar el flujo de ranking por accidente. Mitigación: regresión explícita de `tests/test_cv_screening.py`.
- Riesgo: meter una dependencia externa prematura. Mitigación: solución local en esta versión.