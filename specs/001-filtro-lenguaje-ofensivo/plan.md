# Plan de implementación — Filtro de lenguaje ofensivo para el agente

## Enfoque

Implementar una capa local y determinista de moderación en el flujo actual del chat de RR. HH. La solución más pequeña coherente es introducir un módulo puro de moderación, integrarlo antes de la recuperación/respuesta del agente y volver a validar la salida antes de mostrarla. No se agregan proveedores obligatorios, persistencia ni cambios al ranking o a la lectura de PDFs.

## Decisión técnica

- Opción elegida: moderación local por reglas, con API interna reutilizable por la interfaz.
- Opción descartada para esta versión: proveedor externo obligatorio de guardrails o moderación, porque introduce red, exposición de texto del chat y dependencia operativa innecesaria para el alcance aprobado.

## Componentes y responsabilidad

| Componente | Cambio | Responsable |
|---|---|---|
| `backend/moderation.py` | Nuevo módulo puro con decisión de moderación, normalización y reglas de detección. | Backend |
| `backend/agent.py` | Filtrar entrada antes de buscar evidencia y filtrar respuesta antes de retornar `AgentAnswer`. | Backend |
| `frontend/streamlit_postulacion.py` | Mostrar el mensaje neutral de bloqueo sin romper el hilo del chat ni el contexto seleccionado. | Frontend |
| `tests/test_moderation.py` | Pruebas unitarias de moderación local, falsos positivos y bloqueo de salida. | QA |
| `tests/test_postulacion_agent.py` | Regresión del flujo normal y del bloqueo en el agente. | QA |
| `tests/test_cv_screening.py` | Regresión para asegurar que la revisión de CV no cambia. | QA |
| `specs/001-filtro-lenguaje-ofensivo/*` | Trazabilidad, criterios y evidencia. | Documentación |

## Flujo de datos y control

1. El usuario escribe un mensaje en el chat de RR. HH.
2. `ApplicationAgent.ask()` llama primero a la función de moderación local.
3. Si la entrada se bloquea, el método devuelve una respuesta neutral sin invocar `search_evidence`, Gemini ni Ollama.
4. Si la entrada se permite, el flujo actual sigue intacto: recuperación de evidencia, Gemini opcional, Ollama opcional y fallback determinista.
5. Antes de devolver la respuesta final, el agente valida la salida generada. Si la salida contiene lenguaje ofensivo, la reemplaza por un mensaje neutral.
6. La interfaz de Streamlit sigue usando el mismo hilo de chat y conserva el contexto activo del candidato y del perfil.

## Cambios de API y modelo de datos

- Se agrega un contrato interno de moderación con estado permitido/bloqueado y razón corta.
- No se requieren migraciones de datos.
- No se modifica la interfaz de ranking ni el contrato de `screen_candidates`.
- `AgentAnswer` puede seguir siendo el contenedor de salida del chat; la moderación se encapsula para no romper el flujo existente.

## Seguridad y privacidad

- La moderación se ejecuta localmente por defecto.
- Un mensaje bloqueado no se envía al recuperador, Gemini ni Ollama.
- No se agregan persistencias nuevas ni logs obligatorios de incidentes.
- La salida del agente se revisa antes de renderizarla para evitar mostrar lenguaje ofensivo.
- Si en el futuro se desea usar un guardrail externo, eso se tratará como una nueva especificación.

## Observabilidad y manejo de fallos

- La razón de bloqueo debe ser neutral y breve, sin reproducir el insulto completo.
- Si la moderación falla de forma inesperada, el comportamiento por defecto debe ser conservador y no bloquear el flujo normal sin justificación.
- Las pruebas deben dejar claro cuándo la moderación intervino y cuándo el flujo normal continuó sin cambios.

## Despliegue y reversión

- Orden de entrega: módulo de moderación → agente → interfaz → pruebas → documentación.
- No hay banderas de despliegue ni migraciones.
- La reversión consiste en retirar la llamada a moderación y volver al comportamiento previo del agente; no hay datos que migrar.

## Verificación

- Unitarias: insulto directo, frase ambigua, salida ofensiva, motivo de bloqueo y decisión determinista.
- Regresión: una consulta normal sobre CV sigue respondiendo como antes.
- Integración: un mensaje bloqueado no llega a recuperación ni a modelos externos.
- Evidencia manual: probar el chat de RR. HH. con una entrada ofensiva y otra respetuosa.