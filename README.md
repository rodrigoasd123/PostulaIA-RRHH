# PostulaIA RR. HH. — Revisión asistida de CV

PostulaIA ayuda a un equipo de Recursos Humanos a comparar varios CV en PDF frente a un perfil de puesto. Extrae requisitos verificables, calcula una coincidencia documental reproducible y muestra la evidencia por página. El resultado sirve para priorizar la revisión; **no aprueba, rechaza ni recomienda contratar candidatos**.

## Flujo del producto

```text
Perfil del puesto ─┐
                   ├─ lectura normal/OCR ─ criterios verificables ─ comparador local ─ ranking + evidencia
CV 1..20 ──────────┘                                                        │
                                                                            └─ RAG opcional Gemini/Ollama
```

El puntaje no depende de Gemini ni de Ollama. Para cada requisito, el comparador calcula la proporción de términos presentes en el CV y promedia las coberturas. Los criterios sensibles, como edad, género, estado civil, religión o fotografía, se excluyen automáticamente del puntaje y se muestran como advertencia.

## Estructura

```text
PostulaIA/
├── backend/
│   ├── cv_screening.py       → criterios, filtro sensible, puntaje y ranking
│   ├── pdf_reader.py         → lectura PDF normal y OCR local
│   ├── rag_engine.py         → recuperación FAISS/léxica y Gemini opcional
│   ├── agent.py              → agente de consulta con evidencia
│   ├── vector_cache.py       → índices FAISS persistentes por documento
│   ├── answer_cache.py       → respuestas exactas/semánticas en SQLite
│   ├── cache_service.py      → TTL, estadísticas y borrado seguro
│   └── history.py            → componente heredado; no se usa en el flujo de RR. HH.
├── frontend/
│   └── streamlit_postulacion.py
├── specs/000-hr-cv-screening/ → especificación SDD, plan, tareas y aceptación
├── tests/
├── requirements.txt
└── MANUAL_USUARIO.md
```

## Instalación y ejecución en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run frontend/streamlit_postulacion.py
```

Abre `http://localhost:8501` si el navegador no se inicia automáticamente.

## Uso

1. Elige **Normal** para PDF con texto seleccionable u **OCR** para escaneos.
2. Carga un PDF con el perfil del puesto o la convocatoria.
3. Carga entre uno y veinte CV en PDF.
4. Revisa el ranking orientativo y abre el detalle de cada requisito.
5. Selecciona un candidato y consulta al agente para contrastar el perfil con ese CV.
6. Valida siempre el documento fuente antes de tomar una decisión laboral.

Un CV ilegible no detiene el resto del lote. Si el perfil no contiene requisitos explícitos, la aplicación no inventa criterios ni genera un ranking.

## IA y privacidad

- La lectura, OCR, fragmentación, criterios y puntaje se ejecutan localmente.
- Los PDF originales y las API keys no se guardan en la caché.
- Bajo `data/cache/` se conservan localmente fragmentos, embeddings FAISS y respuestas reutilizables durante un TTL fijo de 24 horas. Son datos derivados potencialmente personales.
- La caché se aísla por SHA-256 del perfil y CV, versiones del modelo, prompt y moderación; nunca reutiliza respuestas entre CV distintos.
- La pestaña **Caché local** muestra, solo para el perfil y CV activos, la pregunta normalizada y truncada, ruta, creación, vencimiento y cantidad de reutilizaciones; no expone la respuesta ni su evidencia.
- Las métricas locales distinguen aciertos exactos, aciertos semánticos y fallos; la tasa se calcula sobre esos eventos y las llamadas evitadas equivalen a los aciertos. Se conservan hasta el borrado total.
- RR. HH. puede borrar una respuesta concreta con confirmación sin afectar documentos, índices ni métricas históricas, o borrar toda la caché desde **Caché vectorial local · 24 h**. Después del borrado total queda desactivada hasta pulsar **Reactivar caché local**.
- Sin API key, el chat usa recuperación vectorial local cuando está disponible y conserva el fallback léxico con citas.
- Con Gemini, la recuperación es local y solo se envían los fragmentos recuperados del perfil y del CV seleccionado al hacer una pregunta.
- La clave pegada en la interfaz vive solo en la sesión. `.env` permanece excluido de Git.
- Ollama permite redactar respuestas localmente con `llama3.2:3b`.

La búsqueda vectorial usa FastEmbed con `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones). La primera consulta descarga el modelo local, aproximadamente 200–250 MB. Si el modelo, SQLite o FAISS fallan, el chat continúa con recuperación léxica y el ranking no cambia. Esta versión depende de los permisos del sistema operativo, no cifra la caché a nivel de aplicación y está limitada a uso local por una sola persona; no debe desplegarse como servicio compartido.

## Configuración opcional

Copia `.env.example` a `.env` y configura una clave personal solo para desarrollo local:

```text
GEMINI_API_KEY=tu_clave
```

No publiques una clave personal. Cada usuario debe usar la suya.

## Pruebas

```powershell
python -m pytest -q
```

La trazabilidad de requisitos y evidencia se encuentra en `specs/000-hr-cv-screening/` y `specs/003-cache-vectorial-respuestas/`.
