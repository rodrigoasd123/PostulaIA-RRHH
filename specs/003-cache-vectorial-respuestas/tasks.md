# Tareas — SPEC-003

> Impacto del refinamiento R1: T-005, T-006, T-008 y T-010 permanecen completadas para la versión base. Las tareas T-011 a T-015 cubren exclusivamente FR-013 a FR-015 y AC-010 a AC-012 y requieren aprobación del addendum antes de implementación.

- [x] **T-001 — Declarar y validar dependencias locales**
  - Cubre: NFR-001, NFR-005; AC-001, AC-008.
  - Archivos: `requirements.txt`, `README.md`.
  - Cambio: añadir FastEmbed/NumPy directos, documentar descarga inicial y comprobar importación en Python 3.13 sin incorporar pesos al repositorio.
  - Verificación: instalación en entorno del proyecto, `python -c "from fastembed import TextEmbedding; import faiss, numpy"` y fallback probado sin modelo.
  - Dependencias: ninguna.

- [x] **T-002 — Definir contratos, identidad y versionado de caché**
  - Cubre: FR-001, FR-004, FR-008, NFR-002, NFR-004, SEC-001, SEC-003.
  - Archivos: `backend/cache_models.py` (nuevo), `backend/models.py`, `tests/test_vector_cache.py` (nuevo).
  - Cambio: dataclasses, SHA-256, claves de documento/contexto y constantes de modelo/chunker/prompt/moderación.
  - Verificación: pruebas de claves iguales/diferentes y compatibilidad de `AgentAnswer`.
  - Dependencias: T-001.

- [x] **T-003 — Implementar adaptador de embeddings local e inyectable**
  - Cubre: FR-002, NFR-001, NFR-005; AC-001, AC-002.
  - Archivos: `backend/local_embeddings.py` (nuevo), `tests/test_vector_cache.py`.
  - Cambio: FastEmbed para pasajes/consultas, normalización L2, límites de lote y doble determinista para pruebas.
  - Verificación: dimensiones/normalización con doble sin red; prueba manual separada del modelo real.
  - Dependencias: T-001, T-002.

- [x] **T-004 — Persistir y recuperar índices FAISS por documento**
  - Cubre: FR-002, FR-003, FR-004, FR-005, FR-009, FR-012, NFR-004, SEC-002, SEC-005; AC-001, AC-002, AC-003, AC-006, AC-008.
  - Archivos: `backend/vector_cache.py` (nuevo), `tests/test_vector_cache.py`, `.gitignore`.
  - Cambio: esquema `documents/chunks`, `IndexFlatIP`, escritura atómica, carga, búsqueda limitada, TTL y fallback ante corrupción.
  - Verificación: suite focalizada con directorio temporal, reloj/embeddings inyectados y sin red.
  - Dependencias: T-002, T-003.

- [x] **T-005 — Implementar caché exacta y semántica de respuestas**
  - Cubre: FR-006, FR-007, FR-008, FR-009, NFR-002, NFR-003, SEC-004, SEC-005, SEC-008; AC-004, AC-005, AC-006, AC-009.
  - Archivos: `backend/answer_cache.py` (nuevo), `tests/test_answer_cache.py` (nuevo).
  - Cambio: SQLite parametrizado, evidencia validada, pregunta normalizada/vectorizada, coseno ≥0.97, versiones/origen, TTL fijo.
  - Verificación: hits/misses, límites del umbral, aislamiento y reloj controlado; modelo generativo simulado no invocado en hit.
  - Dependencias: T-002, T-003.

- [x] **T-006 — Coordinar limpieza y borrado seguro**
  - Cubre: FR-009, FR-010, NFR-004, SEC-006, SEC-007; AC-006, AC-007.
  - Archivos: `backend/cache_service.py` (nuevo), `backend/__init__.py`, `tests/test_cache_service.py` (nuevo).
  - Cambio: fachada, limpieza al inicio/operaciones, estadísticas, cierre de conexiones y borrado limitado a `data/cache`.
  - Verificación: expiración coordinada, borrado completo, rutas fuera de alcance rechazadas y fallos parciales reportados.
  - Dependencias: T-004, T-005.

- [x] **T-007 — Integrar caché en RAG y agente sin cambiar ranking**
  - Cubre: FR-005, FR-006, FR-007, FR-008, FR-011, FR-012, SEC-004, SEC-005; AC-003, AC-004, AC-005, AC-008, AC-009.
  - Archivos: `backend/rag_engine.py`, `backend/agent.py`, `backend/models.py`, `tests/test_postulacion_agent.py`, `tests/test_cv_screening.py`.
  - Cambio: recuperador local opcional, orden de moderación/cache/modelo, almacenamiento solo permitido, origen y fallback.
  - Verificación: pruebas de integración sin red, no llamada LLM en hit y puntajes/ranking idénticos a línea base.
  - Dependencias: T-004, T-005, T-006.

- [x] **T-008 — Añadir controles y transparencia en Streamlit**
  - Cubre: FR-009, FR-010, FR-011, SEC-006, SEC-007; AC-007.
  - Archivos: `frontend/streamlit_postulacion.py`.
  - Cambio: hashes por bytes, recurso de caché, limpieza inicial, contexto perfil/CV, etiqueta de origen, confirmación y botón de borrado, aviso de retención.
  - Verificación: recorrido manual con documentos ficticios y prueba de funciones UI extraídas cuando sea viable.
  - Dependencias: T-006, T-007.

- [x] **T-009 — Documentar operación, privacidad y reversión**
  - Cubre: NFR-004, SEC-001, SEC-002, SEC-007, SEC-008; AC-006, AC-007, AC-008.
  - Archivos: `README.md`, `docs/sdd/proyecto.md`, `specs/003-cache-vectorial-respuestas/tasks.md`.
  - Cambio: datos guardados/no guardados, TTL, modelo, primera descarga, borrado, logs, fallback y restricción de despliegue.
  - Verificación: revisión de afirmaciones contra rutas/configuración implementadas.
  - Dependencias: T-001, T-006, T-008.

- [x] **T-010 — Ejecutar regresión y registrar evidencia de aceptación**
  - Cubre: todos los requisitos y AC-001 a AC-009.
  - Archivos: pruebas anteriores y nuevas; `specs/003-cache-vectorial-respuestas/tasks.md`, `specs/003-cache-vectorial-respuestas/spec.md`.
  - Cambio: ejecutar pruebas focalizadas/completas, completar checklist y pasar la SPEC a `VERIFICANDO` solo si todo aprueba.
  - Verificación: `python -m pytest -q` sin red más recorrido manual documentado; cualquier fallo detiene entrega.
  - Dependencias: T-001 a T-009.

- [x] **T-011 — Migrar contratos y subesquema de respuestas de forma compatible**
  - Cubre: FR-013, FR-015, NFR-006, SEC-009; AC-010, AC-011.
  - Archivos: `backend/cache_models.py`, `backend/answer_cache.py`, `tests/test_answer_cache.py`.
  - Cambio: contratos de resumen/métricas, `CachedResponse.entry_id`, `answer_schema_version=2`, columnas de hits, tabla agregada e índice de contexto sin cambiar `CACHE_SCHEMA_VERSION=1`.
  - Verificación: crear manualmente una base v1 en `tmp_path`, migrarla dos veces, conservar la respuesta/TTL y comprobar valores cero; ejecutar `python -m pytest -q tests/test_answer_cache.py --basetemp=.pytest-tmp/spec003-r1-answer`.
  - Dependencias: T-005 completada.

- [x] **T-012 — Implementar listado, métricas y borrado individual con aislamiento**
  - Cubre: FR-013, FR-014, FR-015, NFR-006, SEC-005, SEC-006, SEC-009; AC-010, AC-011, AC-012.
  - Archivos: `backend/answer_cache.py`, `backend/cache_service.py`, `tests/test_answer_cache.py`, `tests/test_cache_service.py`.
  - Cambio: listado vigente/truncado por contexto y versiones, registro atómico de hit/miss, métricas derivadas y `DELETE` por ID + hashes; el borrado total reinicia métricas.
  - Verificación: contextos distintos, expiración, pregunta de más de 96 caracteres, hit exacto/semántico, miss, fórmulas, borrado válido/adversarial y preservación de FAISS.
  - Dependencias: T-011.

- [x] **T-013 — Integrar medición una vez por interacción en el agente**
  - Cubre: FR-015, NFR-003, NFR-006, SEC-004, SEC-009; AC-011.
  - Archivos: `backend/agent.py`, `tests/test_postulacion_agent.py`.
  - Cambio: acreditar hit tras moderación aprobada; registrar un solo miss al agotar rutas; omitir métricas en conversación, moderación bloqueada y fallo operativo.
  - Verificación: stubs con varias rutas, salida cacheada bloqueada, saludo y entrada ofensiva; `python -m pytest -q tests/test_postulacion_agent.py --basetemp=.pytest-tmp/spec003-r1-agent`.
  - Dependencias: T-012.

- [x] **T-014 — Añadir visualización y borrado individual en Streamlit**
  - Cubre: FR-013, FR-014, FR-015, NFR-006, SEC-006, SEC-009; AC-010, AC-011, AC-012.
  - Archivos: `frontend/streamlit_postulacion.py`.
  - Cambio: quinta pestaña “Caché local”, métricas desde último borrado total, lista del perfil/CV activos, pregunta truncada, ruta/tiempos/reutilizaciones y confirmación de borrado individual; conservar controles laterales.
  - Verificación: compilación, salud HTTP y recorrido manual con dos CV ficticios, incluyendo cambio de candidato, eliminación individual y borrado total.
  - Dependencias: T-012, T-013.

- [x] **T-015 — Documentar y verificar el refinamiento R1**
  - Cubre: FR-013, FR-014, FR-015, NFR-006, SEC-009; AC-010, AC-011, AC-012.
  - Archivos: `README.md`, `docs/sdd/proyecto.md`, `specs/003-cache-vectorial-respuestas/tasks.md`, `specs/003-cache-vectorial-respuestas/spec.md` y pruebas anteriores.
  - Cambio: documentar semántica/retención de métricas, privacidad, migración y reversión; ejecutar pruebas focalizadas/completas y pasar la SPEC a `VERIFICANDO` solo con evidencia aprobada.
  - Verificación: comandos del addendum, `git diff --check`, salud Streamlit y checklist manual; cualquier fallo detiene entrega.
  - Dependencias: T-011 a T-014.
## Puertas de salida

- [x] Todos los requisitos obligatorios están cubiertos por al menos una tarea.
- [x] Todos los criterios AC-001 a AC-009 tienen prueba o evidencia prevista.
- [x] No quedan decisiones técnicas bloqueantes para iniciar tras aprobación.
- [x] Existe estrategia explícita de transición, fallback y reversión.
- [x] Plan aprobado por la persona responsable.
## Puertas de salida del refinamiento R1

- [x] FR-013 a FR-015 y AC-010 a AC-012 tienen tareas y evidencia prevista.
- [x] La migración y el rollback preservan respuestas/índices existentes.
- [x] LangSmith y cualquier telemetría externa permanecen fuera de alcance.
- [x] No quedan decisiones técnicas bloqueantes.
- [x] Addendum R1 aprobado por la persona responsable el 2026-08-20.

## Evidencia de implementación base

> Esta evidencia no valida todavía el refinamiento R1 de visualización, métricas y borrado individual.

- Suite focalizada de persistencia y respuestas: `11 passed`.
- Integración del agente, moderación, caché y no regresión del ranking: `21 passed`.
- Regresión completa: `41 passed in 1.63s` con `GEMINI_API_KEY` vacía.
- FastEmbed real: modelo multilingüe cargado localmente; vector finito de 384 dimensiones.
- Recorrido real del servicio: identidad del mismo PDF reutilizada, dos fragmentos recuperados por FAISS y borrado de un documento/dos archivos confirmado.
- Streamlit actualizado en `http://localhost:8501`: salud HTTP `200 ok`, sin errores de arranque.
- La prueba manual de RR. HH. mostró 3 documentos vectorizados y 1 respuesta reutilizable; esto confirma persistencia de documentos y escritura de respuestas.
- Se corrigió el contraste de botones y desplegables de la barra lateral tras la prueba manual; regresión posterior: `41 passed` y salud HTTP `200 ok`.
- Revisión visual interactiva pendiente de aceptación por la persona responsable; el controlador automatizado del navegador no pudo iniciarse por un fallo del aislador de Windows.

## Evidencia de implementación del refinamiento R1

- Migración y contratos de respuestas: `8 passed`.
- Servicio coordinado de caché: `12 passed` junto con la caché de respuestas.
- Integración del agente y medición por interacción: `14 passed`.
- Suite focalizada R1: `26 passed in 1.69s`.
- Regresión completa: `48 passed in 2.08s`.
- Compilación de módulos modificados sin errores; `git diff --check` sin errores de whitespace.
- Streamlit disponible en `http://localhost:8501` con salud HTTP `200 ok`.
- Queda pendiente la aceptación visual/manual de la persona responsable con sus documentos de prueba.

## Desviaciones y decisiones durante la implementación

- Pytest necesitó `--basetemp=.pytest-tmp/full` porque el directorio temporal global de Windows no era accesible desde el entorno; no cambia el producto.
- La primera validación de FastEmbed descargó el modelo a la caché local del usuario y mostró advertencias informativas sobre pooling/symlinks; el modelo produjo vectores válidos.
- Tras el borrado manual, la caché queda desactivada para impedir su recreación en la misma ejecución. RR. HH. debe pulsar **Reactivar caché local** para volver a construirla.
- No se añadieron logs con texto documental; el origen de la respuesta se muestra en la interfaz.
