# Implementation plan — Asistente de revisión de CV para RR. HH.

## Approach

Implementar un único flujo vertical local: perfil de puesto → requisitos con fuente → lectura de CV → comparación determinista → ranking explicable → consulta RAG opcional sobre un candidato. El primer corte no agrega persistencia ni servicios externos nuevos.

## Components and ownership

| Component | Change | Owner |
|---|---|---|
| `backend/cv_screening.py` | Modelos de revisión, extracción de criterios, filtro sensible y fórmula de coincidencia | Backend |
| `backend/models.py` | Tipos de criterio, coincidencia y revisión de candidato | Backend |
| `backend/agent.py` | Construcción de un agente de consulta con fuentes perfil/CV etiquetadas | AI workflow |
| `frontend/streamlit_postulacion.py` | Flujo de carga múltiple, ranking, detalle, advertencias y chat por candidato | Frontend |
| `tests/test_cv_screening.py` | Pruebas de fórmula, orden, evidencia, sensibilidad y ausencia de criterios | QA |
| README y manual | Nuevo propósito, arquitectura y uso | Documentation |

## Data and control flow

1. El usuario elige lectura normal u OCR y carga un perfil y hasta veinte CV.
2. Streamlit conserva los bytes en memoria y llama a `read_pdf` por archivo.
3. `extract_criteria` usa el analizador existente, deduplica requisitos y excluye criterios sensibles.
4. `screen_candidates` normaliza términos, calcula cobertura por requisito y ordena resultados.
5. La interfaz muestra puntaje y evidencia. Un error de CV queda asociado solo a ese archivo.
6. Para una consulta, el agente recibe copias en memoria de las páginas del perfil y del CV seleccionado con etiquetas de fuente dentro del texto.
7. La recuperación del flujo de RR. HH. es local; solo los fragmentos recuperados llegan a Gemini si el usuario configuró una clave.

## Data model and API changes

- **Migrations:** ninguna.
- **Compatibility:** `ApplicationAgent`, `read_pdf` y las pruebas actuales permanecen disponibles.
- **API contracts:** se agregan funciones Python puras `extract_criteria`, `review_candidate` y `screen_candidates`.
- **Persistence:** ninguna para PDF, ranking o chat de RR. HH.; el historial heredado queda fuera de este flujo.

## Security and privacy

- No se escriben archivos cargados ni texto extraído.
- El puntaje se ejecuta localmente y no usa Gemini/Ollama.
- Los embeddings remotos se desactivan para CV; la recuperación previa a una consulta es léxica y local.
- Una lista explícita de patrones sensibles excluye esos criterios del puntaje y genera advertencias.
- La interfaz muestra que el usuario debe revisar evidencia y aplicar su política legal de selección.

## Observability and failure handling

- Los errores de lectura se muestran por nombre de archivo sin abortar el lote.
- La ausencia de requisitos detiene el ranking con un mensaje accionable.
- Las fallas de FAISS/Gemini mantienen el fallback léxico existente.
- No se registran textos completos ni claves API.

## Rollout and rollback

- **Deployment order:** modelos/servicio → pruebas → interfaz → documentación.
- **Feature flags:** no se requieren en el prototipo local.
- **Rollback behavior:** revertir el cambio de interfaz y eliminar el módulo nuevo restaura el analizador de convocatorias; no hay datos que migrar.

## Verification strategy

- **Unit:** puntaje determinista, ranking, desempate, evidencia, filtro sensible y perfil sin criterios.
- **Integration:** lectura simulada de varios CV y agente combinado sin red.
- **Regression:** ejecutar todas las pruebas existentes.
- **Manual evidence:** iniciar Streamlit, cargar un perfil y dos CV ficticios y revisar ranking, detalle y advertencias.
