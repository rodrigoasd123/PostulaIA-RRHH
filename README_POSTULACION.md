# PostulaIA - Agente de Postulación

MVP local que analiza bases y convocatorias laborales en PDF. Extrae requisitos,
fechas, condiciones, exclusiones y posibles alertas; además responde preguntas con
fragmentos verificables y número de página.

## Ejecutar en Windows

```powershell
python -m venv .venv-postulacion
.\.venv-postulacion\Scripts\Activate.ps1
pip install -r requirements-postulacion.txt
streamlit run streamlit_postulacion.py
```

La aplicación abre normalmente en `http://localhost:8501`.

## IA gratuita opcional

El modo predeterminado es completamente local y determinístico. Para generar
respuestas más naturales sin enviar el PDF a la nube:

```powershell
ollama pull llama3.2:3b
ollama serve
```

Luego activa **Mejorar respuestas con Ollama local** en la barra lateral. Se puede
cambiar el modelo mediante `OLLAMA_MODEL` y la URL mediante `OLLAMA_URL`.

## Privacidad y límites

- El PDF se procesa en memoria y no se guarda.
- El historial de preguntas se guarda localmente en `data/agente_postulacion.db`.
- No se requieren API keys ni servicios de pago.
- Los PDFs escaneados sin capa de texto necesitan OCR; el MVP informa ese caso.
- Las alertas son apoyo de lectura, no asesoría legal ni laboral.

## Pruebas

```powershell
pytest -q tests/test_postulacion_agent.py
```

## Arquitectura

```text
PDF -> extracción por página -> análisis de requisitos/alertas
                            -> índice léxico -> pregunta -> evidencia citada
                                                   -> Ollama opcional
```
