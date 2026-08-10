# Manual de usuario de PostulaIA

## 1. Descripción

PostulaIA analiza convocatorias laborales en PDF. La aplicación identifica requisitos, fechas, condiciones, exclusiones y posibles alertas. También permite realizar preguntas y muestra las páginas utilizadas como evidencia.

La lectura normal y el OCR funcionan localmente. El agente puede usar Gemini Flash-Lite mediante una API key gratuita, Ollama local o el modo léxico sin LLM. PostulaIA no usa modelos Gemini Pro.

## 2. Requisitos

- Windows 10 u 11.
- Python 3.10 o superior.
- Internet durante la instalación inicial de dependencias.
- Un PDF digital o escaneado.

Comprueba que Python esté instalado:

```powershell
python --version
```

Si el comando no funciona, instala Python desde <https://www.python.org/downloads/> y activa **Add Python to PATH** durante la instalación.

## 3. Descargar el proyecto

Descarga el ZIP desde:

<https://github.com/rodrigoasd123/PostulaIA/archive/refs/heads/main.zip>

Después:

1. Busca `PostulaIA-main.zip` en Descargas.
2. Haz clic derecho y selecciona **Extraer todo**.
3. Abre la carpeta extraída `PostulaIA-main`.

No ejecutes el programa directamente dentro del ZIP.

## 4. Instalación

Abre PowerShell dentro de `PostulaIA-main` y ejecuta:

```powershell
python -m venv .venv
```

Activa el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación, ejecuta primero:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

La instalación solo es necesaria la primera vez.

## 5. Ejecutar PostulaIA

Con el entorno virtual activado, ejecuta:

```powershell
python -m streamlit run frontend/streamlit_postulacion.py
```

Abre esta dirección si el navegador no se inicia automáticamente:

<http://localhost:8501>

Mantén la terminal abierta mientras utilizas la aplicación. Para detenerla, presiona `Ctrl+C`.

## 6. Analizar una convocatoria

1. En **Método de lectura**, elige **Normal** para un PDF con texto seleccionable u **OCR** para un documento escaneado o fotografiado.
2. Utiliza el panel lateral para cargar el PDF.
3. Espera a que termine el procesamiento. El OCR puede tardar más porque analiza visualmente cada página.
4. Revisa el resumen y los contadores.
5. Consulta los requisitos, fechas, condiciones y alertas detectadas.
6. Abre la pestaña del documento fuente para comprobar el texto extraído.

El OCR se ejecuta localmente con RapidOCR y no requiere una API key. Después de extraer el texto, el mismo agente procesa ambos tipos de documento.

## 7. Hacer preguntas

Abre la pestaña **Pregúntale al agente** y escribe preguntas como:

- ¿Cuáles son los requisitos obligatorios?
- ¿Cuál es la fecha límite?
- ¿Qué documentos debo presentar?
- ¿El contrato es permanente?
- ¿Qué puede causar mi descalificación?

Una referencia como `[p. 2]` significa que la evidencia se encuentra en la página 2 del PDF.

## 8. Gemini gratuito opcional

PostulaIA puede utilizar Gemini sin compartir la clave del creador de la aplicación:

1. Crea una clave gratuita en Google AI Studio.
2. Pégala en **API key gratuita de Gemini (opcional)**, en la barra lateral.
3. Comprueba que aparezca el estado **Gemini gratuito listo**.

La clave introducida no se escribe en archivos y permanece únicamente en la sesión de Streamlit. Si no añades una clave, PostulaIA sigue funcionando con búsqueda local y evidencia por página.

## 9. Modo básico sin LLM

PostulaIA funciona sin instalar un modelo de inteligencia artificial. En este modo utiliza búsqueda léxica para localizar fragmentos relevantes y devuelve la evidencia con su número de página.

Deja desactivada la opción **Respuestas con Ollama local**.

Este modo no necesita API key, cuenta, tarjeta de crédito ni conexión permanente a internet.

## 10. Modo opcional con Llama 3.2

Para obtener respuestas mejor redactadas, instala Ollama desde:

<https://ollama.com/download>

Descarga el modelo local:

```powershell
ollama pull llama3.2:3b
```

Comprueba que funciona:

```powershell
ollama run llama3.2:3b
```

Después ejecuta PostulaIA y activa **Respuestas con Ollama local**.

No se utiliza una API key. PostulaIA se comunica con Ollama dentro de la computadora mediante:

```text
http://127.0.0.1:11434
```

## 11. Privacidad

- La extracción de texto y el OCR se procesan localmente.
- Si Gemini está configurado, el texto relevante se envía a la API de Gemini para generar respuestas. No se envía a OpenAI.
- Las claves introducidas en la interfaz no se guardan en el proyecto ni se suben a GitHub.
- Ollama y Llama se ejecutan localmente.
- Las preguntas y respuestas pueden guardarse en una base SQLite local.
- No se recomienda utilizar datos personales reales durante demostraciones públicas.

## 12. Problemas frecuentes

### `python` no se reconoce

Instala Python y activa **Add Python to PATH**.

### `No module named streamlit`

Ejecuta:

```powershell
python -m pip install -r requirements.txt
```

### El puerto 8501 está ocupado

Usa otro puerto:

```powershell
python -m streamlit run frontend/streamlit_postulacion.py --server.port 8502
```

Luego abre <http://localhost:8502>.

### Ollama no responde

Comprueba los modelos instalados:

```powershell
ollama list
```

Inicia el servicio si es necesario:

```powershell
ollama serve
```

### El PDF no contiene texto extraíble

El documento probablemente está escaneado como imagen. Selecciona **OCR** en **Método de lectura** y vuelve a cargarlo.

## 13. Inicio rápido

```powershell
cd "ruta\de\PostulaIA-main"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run frontend/streamlit_postulacion.py
```

Después abre <http://localhost:8501> y carga una convocatoria en PDF.
