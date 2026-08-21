# Plan — SPEC-003

> Impacto del refinamiento R1: el plan original sigue siendo evidencia de la implementación base. El addendum técnico al final de este documento reemplaza únicamente el diseño afectado de `backend/cache_models.py`, `backend/answer_cache.py`, `backend/cache_service.py`, `backend/agent.py`, `frontend/streamlit_postulacion.py` y sus pruebas para FR-013 a FR-015 y AC-010 a AC-012.

## Resumen técnico

Implementar una capa local y opcional de recuperación/caché bajo `data/cache/` con dos responsabilidades separadas:

1. **Caché documental vectorial:** embeddings multilingües generados localmente con FastEmbed y persistidos en índices FAISS por documento. Cada índice se identifica por SHA-256 del PDF, modelo y versión del fragmentador.
2. **Caché de respuestas:** SQLite conserva respuestas documentales exitosas y el embedding local de la pregunta, aislados por huellas del perfil y CV, proveedor/modelo real, prompt y moderación. Un acierto exacto o semántico seguro evita la llamada generativa.

El ranking no consumirá esta capa. El chat conservará recuperación léxica como fallback. El TTL será fijo de 24 horas desde creación, sin renovación por lectura.

Línea base observada antes del plan: `python -m pytest -q` → **27 passed en 1.27 s** con `GEMINI_API_KEY` vacío.

## Arquitectura y límites afectados

| Componente | Estado | Responsabilidad planificada |
|---|---|---|
| `backend/cache_models.py` | Nuevo | Contratos inmutables: identidad documental, fragmento persistido, contexto de caché, respuesta cacheada, estadísticas y origen. |
| `backend/local_embeddings.py` | Nuevo | Adaptador estrecho de FastEmbed; embeddings normalizados para pasajes y consultas; interfaz inyectable para pruebas. |
| `backend/vector_cache.py` | Nuevo | SHA-256, fragmentación/versionado, FAISS `IndexFlatIP`, metadatos SQLite, persistencia/carga, búsqueda por documento, TTL y reconstrucción ante corrupción. |
| `backend/answer_cache.py` | Nuevo | SQLite para preguntas/respuestas/citas; coincidencia exacta y coseno semántico dentro del mismo contexto; TTL y borrado. |
| `backend/cache_service.py` | Nuevo | Fachada que coordina limpieza, dos índices documentales, respuesta cacheada, almacenamiento y borrado seguro. |
| `backend/rag_engine.py` | Existente | Aceptar un recuperador vectorial local opcional; eliminar del flujo principal la construcción remota de embeddings y conservar Gemini solo para redactar con fragmentos recuperados. |
| `backend/agent.py` | Existente | Orden: moderación → conversación básica → caché de respuesta → recuperación → modelo/fallback → moderación de salida → guardado. Exponer origen sin romper consumidores. |
| `backend/models.py` | Existente | Añadir a `AgentAnswer` un campo opcional `origin` con valor predeterminado compatible (`generated`, `cache`, `local`). |
| `backend/__init__.py` | Existente | Exportar únicamente contratos/fachada necesarios por la UI y pruebas. |
| `frontend/streamlit_postulacion.py` | Existente | Calcular huellas desde bytes, inicializar caché una vez, limpiar al arrancar, pasar contexto perfil/CV, mostrar origen y añadir borrado manual confirmado. Ajustar el aviso de privacidad. |
| `requirements.txt` | Existente | Declarar `fastembed>=0.8.0,<0.9.0` y `numpy>=2.0,<3.0`; conservar `faiss-cpu` existente. |
| `.gitignore` | Existente | Excluir `data/cache/` de forma explícita, además de la exclusión existente para bases `.db`. |
| `README.md` y `docs/sdd/proyecto.md` | Existentes | Documentar descarga inicial del modelo, ubicación, TTL, borrado, fallback, privacidad y operación local. |
| `tests/test_vector_cache.py` | Nuevo | Identidad, reutilización, incompatibilidad, aislamiento, persistencia, corrupción y TTL con embeddings falsos. |
| `tests/test_answer_cache.py` | Nuevo | Coincidencia exacta/semántica, umbral, aislamiento, versiones, expiración, moderación y no llamada LLM. |
| `tests/test_cache_service.py` | Nuevo | Borrado coordinado, rutas seguras, estadísticas y fallos parciales. |
| `tests/test_postulacion_agent.py` | Existente | Integración de orden, origen, guardado permitido y fallbacks sin red. |

No se modificará `backend/history.py`, `data/agente_postulacion.db` ni el flujo heredado `streamlit_postulacion.py`.

## Diseño de almacenamiento

### Ubicación

```text
data/cache/
├── cache.db
└── vectors/
    └── <document_cache_key>/
        └── index.faiss
```

Los pesos del modelo descargado por FastEmbed no son datos de candidatos y quedan en la caché de modelos de la biblioteca, fuera del borrado funcional. La UI lo indicará para no confundir “borrar datos de candidatos” con “desinstalar el modelo”.

### SQLite `cache.db`

- `documents`: `cache_key`, `document_hash`, `source_type`, `embedding_model`, `chunker_version`, `index_path`, `created_at`, `expires_at`.
- `chunks`: `document_cache_key`, posición, página original, tipo de fuente y fragmento textual. No almacena nombre de persona ni PDF.
- `answers`: huellas de perfil/CV, pregunta normalizada, vector de pregunta serializado, respuesta, evidencia JSON validada, proveedor/modelo real, versiones de prompt/moderación, origen, `created_at`, `expires_at`.

Se usarán consultas parametrizadas, claves y restricciones únicas. Las marcas de tiempo serán UTC. `expires_at = created_at + 24 h` y no cambiará al leer.

### FAISS

- `faiss.IndexFlatIP` con vectores L2-normalizados para similitud coseno.
- Un índice por PDF para reutilizar un perfil entre candidatos y cada CV de forma independiente.
- Búsqueda separada en el perfil activo y CV seleccionado; combinación estable de los mejores resultados con fuente/página preservadas.
- Escritura a ruta temporal validada y reemplazo atómico; lectura con `faiss.read_index`, sin pickle ni deserialización arbitraria de LangChain.

## Flujo de datos

### Ingesta/reutilización documental

```text
PDF bytes
  → SHA-256
  → cleanup_expired(now)
  → cache_key = hash + modelo + chunker_version
      → índice vigente: cargar FAISS + metadatos
      → ausente/incompatible/corrupto:
          texto PageText → fragmentos con fuente/página
          → FastEmbed local → normalizar
          → FAISS + SQLite → persistir
      → si cualquier paso falla: registrar solo código de error y usar LexicalRetriever
```

### Consulta y caché de respuesta

```text
pregunta
  → moderación de entrada
  → interacción conversacional básica
  → identidad exacta: perfil_hash + cv_hash + response_route + versiones
  → respuesta exacta vigente
      → sí: moderar salida → AgentAnswer(origin="cache")
      → no: embedding local de pregunta
          → respuesta semántica del mismo contexto con coseno >= 0.97
              → sí: moderar salida → AgentAnswer(origin="cache")
              → no: búsqueda FAISS perfil + CV; fallback léxico
                  → Gemini / Ollama / respuesta extractiva
                  → moderación de salida
                  → guardar solo respuesta encontrada y permitida
                  → AgentAnswer(origin="generated" o "local")
```

El umbral inicial será `0.97`; se centralizará como configuración validada en `[0.90, 1.00]`. Una similitud inferior nunca se redondeará ni se tratará como acierto.

## Decisiones y alternativas

### Modelo local elegido

- **Biblioteca:** FastEmbed `>=0.8.0,<0.9.0`, que declara compatibilidad con Python 3.13 y usa ONNX Runtime sin PyTorch.
- **Modelo:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, multilingüe, 384 dimensiones, aproximadamente 0.22 GB y licencia Apache-2.0 según el catálogo de FastEmbed.
- **Razón:** el proyecto trabaja en español, ya dispone de ONNX Runtime y no debe enviar CV completos a un proveedor.
- **Primera ejecución:** descargará los pesos; si no hay red o el modelo no está disponible, la aplicación informará recuperación léxica y seguirá operativa.

### Alternativas descartadas

- **Embeddings de Gemini:** ya existe código parcial, pero transmite contenido completo y contradice el procesamiento local aprobado.
- **SentenceTransformers con PyTorch:** válida, pero añade una dependencia y descarga considerablemente mayores para este prototipo Windows/Python 3.13.
- **Qdrant/Chroma:** aportarían servidor o dependencia de base adicional sin necesidad para una sola persona y un TTL corto.
- **LangChain FAISS persistido:** se evita para controlar metadatos/TTL y no depender de deserialización pickle; se usará la API nativa de FAISS.
- **Solo caché exacta:** segura pero no cubre variantes semánticas aprobadas. Se implementará primero exacta y luego semántica tras pruebas negativas.
- **Un índice único para todos los CV:** simplifica búsqueda, pero incrementa el riesgo de cruces. Se mantienen índices por documento y filtros previos a similitud.

## Compatibilidad, transición y reversión

### Transición

1. Añadir dependencias y adaptadores sin activar persistencia en el ranking.
2. Crear esquema idempotente `schema_version=1`; no migrar ni reutilizar `agente_postulacion.db`.
3. Activar caché solo en la interfaz principal RR. HH. mediante dependencias opcionales del agente.
4. Al primer uso no existirán entradas; el comportamiento será un miss y seguirá el flujo normal.
5. Las instancias existentes de `ApplicationAgent(pages, ...)` continuarán válidas porque los parámetros nuevos serán opcionales y `AgentAnswer.origin` tendrá valor predeterminado.

### Reversión

- Desactivar la inyección de `CacheService` restaura el flujo actual sin migrar datos.
- Borrar únicamente la ruta resuelta `<workspace>/data/cache` elimina esquema, respuestas e índices. Antes de borrar se comprobará que la ruta final sea descendiente exacta de `data/cache`.
- Retirar módulos nuevos y dependencia FastEmbed no afecta `agente_postulacion.db`, PDFs ni ranking.
- Un `schema_version` desconocido se tratará como caché incompatible: no se abrirá ni migrará implícitamente.

## Seguridad, privacidad y fallos

- Persistencia solo local y de un único operador; no se habilita para despliegue compartido.
- Los artefactos contienen datos personales derivados y carecen de cifrado de aplicación. La UI y documentación declararán el riesgo y TTL.
- La clave API, bytes PDF, nombres de candidatos y texto completo de consultas/respuestas no aparecerán en logs. Solo códigos, conteos, origen, latencia y hit/miss.
- Las búsquedas filtran por hashes exactos antes de similitud; no existe consulta global de respuestas ni vectores.
- La moderación precede toda lectura/escritura de respuestas y vuelve a validar la salida cacheada.
- La evidencia deserializada desde SQLite se validará en tipos y límites antes de construir `AgentAnswer`.
- Archivos corruptos, base bloqueada, modelo ausente, disco lleno y permisos insuficientes generan miss/fallback, no error fatal del ranking.
- El borrado manual será una acción explícita confirmada; tras completarse se cerrarán conexiones, eliminarán solo rutas verificadas y se mostrarán conteos.

## Observabilidad

Sin registrar contenido personal:

- `vector_cache_hit` / `vector_cache_miss` / `vector_cache_rebuilt`.
- `answer_cache_exact_hit` / `answer_cache_semantic_hit` / `answer_cache_miss`.
- modelo/versiones, conteo de fragmentos, latencia, entradas eliminadas y código de fallo.
- La UI mostrará únicamente “Respuesta desde caché”, “Respuesta generada” o “Respuesta local”, sin métricas técnicas sensibles.

## Estrategia de pruebas y evidencia

| AC | Tipo | Prueba o evidencia prevista |
|---|---|---|
| AC-001 | Automatizada | `tests/test_vector_cache.py`: mismo hash/modelo/chunker carga índice y el embedding falso no recibe segunda llamada. |
| AC-002 | Automatizada | `tests/test_vector_cache.py`: cambios de bytes, modelo y versión producen claves/índices distintos. |
| AC-003 | Automatizada | `tests/test_vector_cache.py` + `tests/test_postulacion_agent.py`: búsqueda en perfil+CV seleccionado sin fragmentos de otro CV. |
| AC-004 | Automatizada | `tests/test_answer_cache.py`: exact hit y similitud ≥0.97 evitan doble de Gemini/Ollama; origen `cache`. |
| AC-005 | Automatizada | `tests/test_answer_cache.py`: mismo texto con `cv_hash` distinto produce miss. |
| AC-006 | Automatizada | `tests/test_vector_cache.py` y `tests/test_answer_cache.py`: reloj inyectado a 23:59:59, 24:00:00 y posterior. |
| AC-007 | Automatizada/manual | `tests/test_cache_service.py` borra DB/índices; verificación manual del botón y confirmación en Streamlit. |
| AC-008 | Automatizada | `tests/test_vector_cache.py`: índice corrupto/permiso simulado devuelve miss; prueba del agente confirma fallback léxico y ranking intacto. |
| AC-009 | Automatizada | `tests/test_postulacion_agent.py`: entrada ofensiva no consulta caché; salida cacheada ofensiva se bloquea; inspección de DB/log falso excluye clave y texto. |

Verificación total prevista:

```powershell
$env:GEMINI_API_KEY=''
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q
```

Prueba manual, con PDFs ficticios:

1. Cargar perfil y CV; confirmar creación de caché y origen generado/local.
2. Reiniciar Streamlit y cargar los mismos bytes; confirmar reutilización vectorial.
3. Repetir pregunta; confirmar “Respuesta desde caché” y ausencia de llamada generativa en logs sanitizados.
4. Cambiar de CV; confirmar que no se reutiliza la respuesta.
5. Pulsar borrado, confirmar y verificar cero entradas bajo `data/cache/`.
6. Simular fecha posterior a 24 horas en prueba automatizada; no se alterará el reloj del sistema para la prueba manual.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Falso positivo semántico | Umbral 0.97, mismo contexto/versiones, pruebas de preguntas cercanas con intención distinta y fallback a modelo. |
| Descarga inicial lenta o sin red | Estado visible, timeout/error controlado y fallback léxico; no descargar durante pruebas. |
| Cruce entre candidatos | Índices por documento y filtro hash previo obligatorio; pruebas adversariales. |
| Datos personales en disco | TTL fijo, borrado manual, `.gitignore`, uso local y aviso explícito sin promesa de cifrado. |
| Corrupción o escritura parcial | SQLite transaccional, índice temporal + reemplazo atómico, invalidación/reconstrucción. |
| Incompatibilidad Python/dependencias | FastEmbed 0.8 declara Python 3.13; prueba de instalación/importación antes de activar la tarea de integración. |
| Caché evita mejoras de prompt/modelo | Claves incluyen versiones; cualquier cambio produce miss automático. |

## Aprobación

- [x] Plan aprobado por la persona responsable mediante `$sdd-implement-es` el 2026-08-20.
## Addendum técnico R1 — Visualización y control local de respuestas

### Resumen técnico

Extender la caché existente sin cambiar FAISS, el ranking ni las rutas generativas. SQLite conservará las respuestas actuales y añadirá contadores de reutilización por entrada y métricas agregadas sin contenido personal. La interfaz incorporará una quinta pestaña, **Caché local**, limitada al perfil y CV seleccionados. LangSmith y cualquier telemetría externa quedan excluidos.

Línea base confirmada antes del addendum: `python -m pytest -q --basetemp=.pytest-tmp/plan-r1-baseline` → **41 passed en 5.09 s** con `GEMINI_API_KEY` vacío.

### Arquitectura y límites afectados

| Componente | Cambio R1 |
|---|---|
| `backend/cache_models.py` | Añadir contratos inmutables y compatibles para resumen visible y métricas; extender `CachedResponse` con un identificador opcional de entrada. |
| `backend/answer_cache.py` | Migración aditiva del subesquema de respuestas, listado filtrado, registro atómico de hit/miss y borrado individual con alcance documental. |
| `backend/cache_service.py` | Exponer fachada para listar, medir, registrar resultados y borrar una respuesta; mantener `clear_all()` como borrado total y reinicio de métricas. |
| `backend/agent.py` | Registrar un único miss después de agotar rutas y un hit solo después de que la salida cacheada supere moderación. |
| `frontend/streamlit_postulacion.py` | Añadir pestaña de caché del contexto activo, tarjetas de métricas, lista truncada y confirmación de borrado individual; conservar el resumen/borrado total lateral. |
| `tests/test_answer_cache.py` | Migración, aislamiento del listado, contadores, TTL y borrado por alcance. |
| `tests/test_cache_service.py` | Contratos de fachada, preservación de índices y reinicio por borrado total. |
| `tests/test_postulacion_agent.py` | Un hit/miss por interacción válida, precedencia de moderación y ausencia de conteo conversacional/ofensivo. |
| `README.md`, `docs/sdd/proyecto.md` | Semántica de métricas, visualización, borrado individual, privacidad y reversión. |

No se modificarán `backend/vector_cache.py`, los archivos `index.faiss`, `backend/cv_screening.py`, el puntaje, el ranking, `backend/history.py` ni el flujo heredado.

### Diseño de datos y migración

- Mantener `CACHE_SCHEMA_VERSION=1`: el formato documental/FAISS no cambia y `VectorCache` debe seguir abriendo la base existente.
- Añadir en `cache_meta` una versión independiente `answer_schema_version=2`.
- Migrar dentro de una transacción mediante `PRAGMA table_info(answers)` y `ALTER TABLE ... ADD COLUMN` únicamente cuando falten:
  - `exact_hit_count INTEGER NOT NULL DEFAULT 0`.
  - `semantic_hit_count INTEGER NOT NULL DEFAULT 0`.
  - `last_hit_at REAL NULL`.
  - `last_match_type TEXT NULL`, limitado por código a `exact` o `semantic`.
- Crear un índice de consulta sobre `profile_hash`, `cv_hash`, `prompt_version`, `moderation_version` y `expires_at`.
- Crear `answer_cache_metrics` con una única fila (`id=1`) y contadores no negativos `exact_hits`, `semantic_hits`, `misses`.
- Las filas existentes conservarán pregunta, respuesta, evidencia, creación y expiración; los contadores nuevos empezarán en cero y el TTL no se renovará.
- Métricas derivadas, no persistidas: `hits = exact_hits + semantic_hits`, `calls_avoided = hits` y `hit_rate = hits / (hits + misses)`, o `0` cuando no haya consultas medidas.
- Las métricas agregadas representan actividad desde el último borrado total; borrar una respuesta individual no reescribe el historial agregado.

### Contratos internos

- `CachedResponse.entry_id: int | None = None` preservará consumidores existentes y permitirá acreditar un hit después de moderar la salida.
- Nuevo `CachedAnswerSummary`: `entry_id`, `question_preview`, `response_route`, `created_at`, `expires_at`, `exact_hit_count`, `semantic_hit_count`; no incluirá respuesta, evidencia, vector ni pregunta completa.
- Nuevo `AnswerCacheMetrics`: conteos base y propiedades derivadas para hits, tasa y llamadas evitadas.
- `AnswerCache.list_active(profile_hash, cv_hash, prompt_version, moderation_version, limit=50)` limpiará expirados, filtrará antes de ordenar y truncará la pregunta a 96 caracteres en la capa backend.
- `AnswerCache.record_hit(entry_id, context, match_type)` actualizará la fila y las métricas en la misma transacción, sin extender `expires_at`.
- `AnswerCache.record_miss()` actualizará solo el agregado.
- `AnswerCache.delete_entry(entry_id, profile_hash, cv_hash)` eliminará mediante consulta parametrizada y devolverá `True` solo si borró una fila del contexto indicado.
- `CacheService` expondrá equivalentes estrechos; ninguna API aceptará nombres de candidatos ni devolverá texto de respuesta.

### Flujo de datos

#### Consulta y medición

```text
pregunta permitida y no conversacional
  → probar rutas de caché del contexto activo
      → hit exacto/semántico
          → moderación de salida aprobada
          → record_hit(entry_id, contexto, tipo)
          → devolver respuesta cacheada
      → salida bloqueada: no registrar reutilización
      → todas las rutas devuelven miss
          → record_miss() una sola vez
          → recuperación/modelo/fallback existente
```

Un error operativo de caché no contará como hit ni miss. Saludos, ayuda, despedidas y entradas bloqueadas no producirán métricas. Probar varias rutas Gemini/Ollama en una misma pregunta nunca multiplicará el contador de misses.

#### Visualización y borrado individual

```text
perfil_hash + cv_hash activos + versiones vigentes
  → cleanup_expired(now)
  → list_active(...)
  → pestaña Caché local
      → métricas agregadas desde último borrado total
      → pregunta previa de máximo 96 caracteres
      → ruta, creación, tiempo restante y reutilizaciones
      → Eliminar → estado de confirmación → delete_entry(id, hashes)
          → éxito: refrescar lista, conservar FAISS y otras respuestas
```

### Decisiones y alternativas

- **Pestaña dedicada, no listado completo en la barra lateral:** hay espacio para explicar métricas y confirmar borrados sin empeorar la navegación lateral.
- **Solo contexto activo:** se descarta una tabla global porque podría revelar preguntas de otro candidato y no representa lo reutilizable para la consulta actual.
- **Contadores agregados, no registro de eventos:** evita una nueva tabla con historial por pregunta/fecha y minimiza datos personales; se pierde análisis temporal detallado, fuera de alcance.
- **Pregunta truncada en backend:** evita que la UI reciba respuesta/evidencia o tenga que aplicar la política de minimización por su cuenta.
- **Sin nombres persistidos:** la interfaz puede indicar “perfil y CV activos”; los nombres de archivo existentes en memoria no se escriben en la caché.
- **Sin LangSmith:** no se añaden dependencias, claves, red, costes ni retención externa.

### Compatibilidad, transición y reversión

1. `VectorCache` abrirá primero `schema_version=1`; `AnswerCache` ejecutará después la migración R1 aditiva.
2. La migración será idempotente y transaccional. Un fallo abortará la inicialización opcional de caché y la UI conservará el fallback léxico; ranking y carga de PDF seguirán operativos.
3. Las respuestas v1 permanecerán reutilizables y visibles con contadores en cero.
4. El código anterior puede volver a ejecutarse sobre la base ampliada porque ignora columnas y tabla adicionales y la versión documental permanece en 1.
5. `clear_all()` continuará siendo la reversión de datos: elimina `data/cache/`, incluidos métricas, respuestas e índices, y recrea un almacén vacío.
6. No se añaden dependencias ni variables de entorno.

### Seguridad, privacidad y fallos

- Todo listado y borrado filtra por huellas exactas antes de usar el identificador de entrada.
- La vista no devuelve respuestas, evidencia, embeddings, claves, nombres persistidos ni preguntas completas.
- Los IDs son internos y no autorizan una operación por sí solos; el `DELETE` exige también `profile_hash` y `cv_hash`.
- Las métricas contienen solo enteros agregados. No se envían por red y se reinician con el borrado total.
- SQLite bloqueada, migración incompleta o fila corrupta producen una vista no disponible/fallback, nunca un cambio en el ranking.
- El borrado individual tendrá confirmación y resultado visible; una fila ya expirada o de otro contexto responderá “no encontrada” sin afectar otros datos.

### Estrategia de pruebas y evidencia R1

| AC | Tipo | Prueba o evidencia prevista |
|---|---|---|
| AC-010 | Automatizada + manual | `tests/test_answer_cache.py`: dos contextos y una entrada expirada; `list_active` solo devuelve el activo, truncado y sin respuesta. Recorrido de la quinta pestaña con dos CV ficticios. |
| AC-011 | Automatizada | `tests/test_answer_cache.py` y `tests/test_postulacion_agent.py`: exact hit, semantic hit y un miss por interacción; fórmulas consistentes, TTL inmutable, sin conteo bloqueado/conversacional ni red. |
| AC-012 | Automatizada + manual | `tests/test_answer_cache.py`/`tests/test_cache_service.py`: borrar una de dos respuestas con hashes correctos, rechazar otro contexto y conservar documentos/FAISS; confirmación visible en Streamlit. |
| AC-004, AC-005, AC-006 | Regresión | Pruebas existentes de reutilización, aislamiento y TTL siguen aprobando después de la migración. |
| AC-007, AC-009 | Regresión | Borrado total y precedencia de moderación siguen aprobando; el borrado total reinicia métricas. |

Verificación prevista:

```powershell
$env:GEMINI_API_KEY=''
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q tests/test_answer_cache.py tests/test_cache_service.py tests/test_postulacion_agent.py --basetemp=.pytest-tmp/spec003-r1-focused
python -m pytest -q --basetemp=.pytest-tmp/spec003-r1-full
```

Prueba manual con PDFs ficticios:

1. Generar dos respuestas para el mismo perfil/CV y confirmar que aparecen sin mostrar su contenido completo.
2. Repetir una pregunta exacta y una equivalente; comprobar contadores exacto/semántico, reutilizaciones y llamadas evitadas.
3. Hacer una pregunta documental nueva; comprobar un único miss.
4. Cambiar de CV y confirmar que la lista anterior no aparece.
5. Eliminar una respuesta con confirmación; comprobar que la otra y los documentos vectorizados permanecen.
6. Ejecutar borrado total; comprobar lista vacía y métricas reiniciadas.

### Riesgos y mitigaciones R1

| Riesgo | Mitigación |
|---|---|
| Migración parcial o repetida | Transacción, inspección de columnas, clave `answer_schema_version` e idempotencia probada. |
| Misses inflados por múltiples rutas | Registrar una vez en el agente después de agotar rutas, no dentro de cada consulta SQL. |
| Contar una respuesta bloqueada como reutilizada | Registrar el hit únicamente después de la moderación de salida. |
| Exposición de otro candidato | Filtro obligatorio por ambos hashes y versiones; pruebas con contextos distinguibles. |
| Borrado de la fila equivocada | `DELETE` parametrizado por ID + hashes y confirmación de UI. |
| Confusión sobre métricas históricas | Etiqueta “desde el último borrado total”; borrado individual no altera agregados. |

### Aprobación del addendum R1

- [x] Addendum R1 aprobado por la persona responsable el 2026-08-20.
