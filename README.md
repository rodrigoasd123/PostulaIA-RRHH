# PostulaIA - Agente de Postulación (TCS Project)

Agente Inteligente en Python que analiza bases de postulación y convocatorias laborales en PDF. Extrae requisitos obligatorios, fechas límite, condiciones contractuales, exclusiones y posibles alertas; además responde preguntas en lenguaje natural citando el número de página como evidencia.

## Estructura del Repositorio (Estándar TCS)

```text
PostulaIA/
├── backend/                  → Agente, RAG (LangChain + FAISS), parser pdfplumber y SQLite
│   ├── agent.py
│   ├── analyzer.py
│   ├── history.py
│   ├── llm.py
│   ├── models.py
│   ├── pdf_reader.py
│   ├── rag_engine.py
│   └── retrieval.py
├── frontend/                 → Interfaz de usuario web en Streamlit
│   └── streamlit_postulacion.py
├── data/                     → PDFs de prueba creados por el equipo (sin datos reales)
├── entregables/              → Video demo (1 min sin voz) y presentación PPT (5 diapositivas)
├── tests/                    → Pruebas unitarias automatizadas
├── requirements.txt          → Dependencias de Python del proyecto
└── README.md                 → Documentación principal del proyecto
```

## Guía de Instalación y Ejecución (Windows)

```powershell
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
python -m pip install -r requirements.txt

# 4. Ejecutar la aplicación web Streamlit
python -m streamlit run frontend/streamlit_postulacion.py
```

La aplicación abrirá automáticamente en `http://localhost:8501`.

## Modos de Inteligencia Artificial (Modo Híbrido)

1. **Modo Google Gemini 1.5 Flash (Recomendado - LangChain + FAISS):**
   - Ingresa una clave gratuita de Google AI Studio en el campo seguro de la barra lateral (o configura la variable de entorno `GEMINI_API_KEY`).
   - Habilita RAG semántico con vectores en memoria (FAISS) y respuestas en lenguaje natural muy fluido.

2. **Modo Ollama Local (Llama 3.2):**
   - Ejecuta `ollama pull llama3.2:3b` y `ollama serve`.
   - Activa **Usar Ollama Local** en la barra lateral para procesamiento 100% offline.

3. **Modo Léxico Local (Por Defecto - Sin Costo / Offline):**
   - Funciona sin necesidad de API keys ni conexión a internet mediante análisis léxico TF-IDF con citas de página.

## Pruebas Unitarias

```powershell
python -m pytest -q tests/test_postulacion_agent.py
```
