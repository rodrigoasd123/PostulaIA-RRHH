# Manual de usuario de PostulaIA

## 1. Descripción

PostulaIA analiza convocatorias laborales en PDF. La aplicación identifica requisitos, fechas, condiciones, exclusiones y posibles alertas. También permite realizar preguntas y muestra las páginas utilizadas como evidencia.

El programa funciona localmente y no requiere una API de pago.

## 2. Requisitos

- Windows 10 u 11.
- Python 3.10 o superior.
- Internet durante la instalación inicial de dependencias.
- Un PDF que contenga texto seleccionable.

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
python -m pip install -r requirements-postulacion.txt
```

La instalación solo es necesaria la primera vez.

## 5. Ejecutar PostulaIA

Con el entorno virtual activado, ejecuta:

```powershell
python -m streamlit run streamlit_postulacion.py
```

Abre esta dirección si el navegador no se inicia automáticamente:

<http://localhost:8501>

Mantén la terminal abierta mientras utilizas la aplicación. Para detenerla, presiona `Ctrl+C`.

## 6. Analizar una convocatoria

1. Utiliza el panel lateral para cargar un PDF.
2. Espera a que termine el procesamiento.
3. Revisa el resumen y los contadores.
4. Consulta los requisitos, fechas, condiciones y alertas detectadas.
5. Abre la pestaña del documento fuente para comprobar el texto extraído.

El PDF debe contener texto seleccionable. Los documentos completamente escaneados todavía requieren una futura integración OCR.

## 7. Hacer preguntas

Abre la pestaña **Pregúntale al agente** y escribe preguntas como:

- ¿Cuáles son los requisitos obligatorios?
- ¿Cuál es la fecha límite?
- ¿Qué documentos debo presentar?
- ¿El contrato es permanente?
- ¿Qué puede causar mi descalificación?

Una referencia como `[p. 2]` significa que la evidencia se encuentra en la página 2 del PDF.

## 8. Modo básico sin LLM

PostulaIA funciona sin instalar un modelo de inteligencia artificial. En este modo utiliza búsqueda léxica para localizar fragmentos relevantes y devuelve la evidencia con su número de página.

Deja desactivada la opción **Respuestas con Ollama local**.

Este modo no necesita API key, cuenta, tarjeta de crédito ni conexión permanente a internet.

## 9. Modo opcional con Llama 3.2

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

## 10. Privacidad

- El PDF se procesa localmente.
- El documento no se envía a OpenAI, Google ni otros servicios externos.
- Ollama y Llama se ejecutan localmente.
- Las preguntas y respuestas pueden guardarse en una base SQLite local.
- No se recomienda utilizar datos personales reales durante demostraciones públicas.

## 11. Problemas frecuentes

### `python` no se reconoce

Instala Python y activa **Add Python to PATH**.

### `No module named streamlit`

Ejecuta:

```powershell
python -m pip install -r requirements-postulacion.txt
```

### El puerto 8501 está ocupado

Usa otro puerto:

```powershell
python -m streamlit run streamlit_postulacion.py --server.port 8502
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

El documento probablemente está escaneado como imagen. Utiliza temporalmente un PDF digital con texto seleccionable.

## 12. Inicio rápido

```powershell
cd "ruta\de\PostulaIA-main"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-postulacion.txt
python -m streamlit run streamlit_postulacion.py
```

Después abre <http://localhost:8501> y carga una convocatoria en PDF.
