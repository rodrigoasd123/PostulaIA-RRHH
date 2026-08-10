# PostulaIA - Asistente Inteligente de Convocatorias Laborales

Agente Inteligente desarrollado en Python que analiza bases de postulación y convocatorias laborales en PDF. Extrae requisitos obligatorios, fechas límite, condiciones contractuales, exclusiones y posibles alertas; además responde preguntas en lenguaje natural citando la página exacta como evidencia.

## Estructura del Repositorio

```text
PostulaIA/
├── backend/                  → Agente, RAG (LangChain + FAISS), lectura normal/OCR y SQLite
│   ├── agent.py
│   ├── analyzer.py
│   ├── history.py
│   ├── llm.py
│   ├── models.py
│   ├── pdf_reader.py
│   ├── rag_engine.py
│   └── retrieval.py
├── frontend/                 → Interfaz de usuario web profesional en Streamlit
│   └── streamlit_postulacion.py
├── data/                     → PDFs de prueba de convocatorias laborales
├── entregables/              → Materiales de demostración y presentación
├── tests/                    → Pruebas unitarias automatizadas
├── .env                      → Variables de entorno locales (GEMINI_API_KEY)
├── .gitignore                → Archivos ignorados por Git
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

## Lectura de documentos

En la barra lateral puedes elegir el método antes de cargar el PDF:

- **Normal:** recomendado para PDFs digitales con texto seleccionable. Usa `pdfplumber` y conserva la extracción de tablas.
- **OCR:** recomendado para PDFs escaneados o creados a partir de fotografías. Renderiza cada página y reconoce el texto localmente con RapidOCR; no requiere API key y puede tardar más.

Los dos métodos entregan texto numerado por página al mismo agente. LangChain, FAISS, Gemini, Ollama y las citas funcionan igual después de la lectura.

Para probar el modo OCR usa `data/convocatoria_administrativo_escaneada_ocr.pdf`. Sus páginas son imágenes y no contienen una capa de texto extraíble.

## Configuración de Inteligencia Artificial (Modo Híbrido)

1. **Modo Google Gemini (LangChain + FAISS):**
   - Configura tu clave en el archivo `.env` local: `GEMINI_API_KEY=tu_clave_aqui`.
   - El agente detectará la clave de forma transparente sin mostrar casillas en la interfaz del usuario final.

2. **Modo Ollama Local (Llama 3.2):**
   - Ejecuta `ollama pull llama3.2:3b` y `ollama serve`.
   - Activa el interruptor **Modo Offline (Ollama Local)** en la barra lateral para procesamiento 100% local.

3. **Modo Léxico Local (Sin Costo / Offline):**
   - Funciona de forma predeterminada sin necesidad de conexión a internet mediante análisis léxico TF-IDF con solapamiento y citas por página.

## Pruebas Unitarias

```powershell
python -m pytest -q
```
