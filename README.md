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
- Los PDF cargados no se guardan en disco por la aplicación.
- El chat de RR. HH. no persiste preguntas, respuestas ni nombres de candidatos.
- Sin API key, el chat usa recuperación léxica local con citas.
- Con Gemini, la recuperación es local y solo se envían los fragmentos recuperados del perfil y del CV seleccionado al hacer una pregunta.
- La clave pegada en la interfaz vive solo en la sesión. `.env` permanece excluido de Git.
- Ollama permite redactar respuestas localmente con `llama3.2:3b`.

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

La trazabilidad de requisitos y evidencia se encuentra en `specs/000-hr-cv-screening/`.
