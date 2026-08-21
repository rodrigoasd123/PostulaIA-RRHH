# Filtro de lenguaje ofensivo para el agente

- **ID:** SPEC-001
- **Status:** VERIFICANDO
- **Created:** 2026-08-20
- **Owner:** Product and engineering

## Problem

El agente conversacional actual responde preguntas sobre CV y perfiles de puesto, pero no tiene una capa explícita para detectar, bloquear o redirigir lenguaje ofensivo, hostil o insultante en la conversación. Eso deja dos riesgos:

1. que el sistema procese entradas abusivas como si fueran consultas normales;
2. que una respuesta del asistente termine reflejando o amplificando ese lenguaje en pantalla.

La funcionalidad debe mantener la conversación profesional, proteger al usuario y evitar que contenido ofensivo llegue innecesariamente al modelo o a otros componentes del flujo.

## Users and outcomes

- **Primary user:** analista o responsable que usa el chat del agente para revisar documentos.
- **Secondary user:** cualquier persona que interactúe con el agente y pueda escribir mensajes inadecuados por error o intención.
- **Desired outcome:** el sistema detecta lenguaje ofensivo antes de generar una respuesta, explica el motivo de forma neutral y permite reintentar con un mensaje reformulado.
- **Success signal:** mensajes ofensivos no llegan al motor de respuesta, el usuario recibe una explicación breve y el agente sigue respondiendo normalmente cuando el mensaje se corrige.

## Scope

### Included

- Detección de lenguaje ofensivo, insultante, hostil o degradante en la entrada del chat del agente.
- Bloqueo preventivo del flujo cuando el mensaje excede la política definida.
- Respuesta neutral al usuario con indicación de que debe reformular el mensaje.
- Protección equivalente para la salida del agente si una generación externa o local devuelve lenguaje ofensivo.
- Configuración de una política inicial basada en reglas locales o una capa de guardrails interna, sin requerir red por defecto.
- Pruebas automáticas para falsos positivos, falsos negativos, bloqueos y respuestas seguras.
- Aplicación al chat del flujo actual de RR. HH. que usa `ApplicationAgent` y `frontend/streamlit_postulacion.py`.

### Excluded

- Moderación de los PDFs cargados como documentos fuente, salvo que su contenido sea reenviado al chat.
- Clasificación legal o disciplinaria del usuario.
- Persistencia de incidentes de moderación, auditoría de conversaciones o revisión manual de casos.
- Integración obligatoria con un proveedor externo de moderación.
- Aplicación directa al flujo heredado de postulantes en `streamlit_postulacion.py`.
- Cambios al cálculo de ranking, extracción de requisitos o lectura de PDF que no estén relacionados con la moderación del chat.

## Requirements

### Functional

- **FR-001:** El sistema debe inspeccionar cada mensaje del usuario antes de enviarlo al recuperador, a Gemini o a Ollama.
- **FR-002:** Cuando un mensaje se clasifique como ofensivo, el sistema no debe invocarlo para respuesta documental y debe mostrar una respuesta neutral que indique que el mensaje debe reformularse.
- **FR-003:** El sistema debe devolver una decisión de moderación reutilizable por la interfaz, al menos con estado permitido o bloqueado y una razón breve.
- **FR-004:** El sistema debe bloquear también una respuesta del asistente si contiene lenguaje ofensivo detectable antes de mostrarla al usuario.
- **FR-005:** Si un mensaje bloqueado es corregido, el usuario debe poder volver a enviarlo sin perder el contexto de la conversación o del documento activo.
- **FR-006:** La moderación no debe alterar el ranking, la extracción de criterios ni la evidencia documental cuando el mensaje sea permitido.

### Non-functional

- **NFR-001:** La moderación debe producir la misma decisión para el mismo texto y la misma configuración.
- **NFR-002:** La solución debe funcionar localmente por defecto y no requerir llamadas de red para evaluar la entrada del usuario.
- **NFR-003:** La capa de moderación debe agregar una complejidad operativa mínima y no introducir dependencia obligatoria de proveedor externo en esta versión.
- **NFR-004:** La explicación al usuario debe ser breve, profesional y no reproducir el lenguaje ofensivo detectado más allá de lo necesario para identificar el problema.

### Security and privacy

- **SEC-001:** Un mensaje bloqueado no debe enviarse al proveedor LLM ni almacenarse en persistencias nuevas por la funcionalidad.
- **SEC-002:** La política de moderación debe tratar el texto del usuario como entrada no confiable y no debe ejecutar instrucciones embebidas en ese texto.
- **SEC-003:** Si se adopta una integración externa de guardrails en el futuro, debe ser optativa, minimizada y aprobada por una especificación aparte.
- **SEC-004:** La moderación no debe exponer listas completas de términos sensibles al usuario final ni en logs visibles.

## Constraints and invariants

- La solución debe integrarse en el flujo actual del chat del agente sin afectar la comparación documental cuando el mensaje es permitido.
- La política inicial debe preferir una implementación local, determinista y fácil de probar.
- El contenido de la moderación no debe introducir cambios en el ranking, el OCR ni la lectura de PDF.
- El sistema debe conservar el comportamiento actual para consultas normales, incluidas las que usan Gemini u Ollama como respaldo.

## Risks and failure modes

- **Falsos positivos:** mensajes legítimos podrían bloquearse por palabras ambiguas. Mitigación: pruebas con contexto benigno y una política conservadora.
- **Falsos negativos:** variaciones ortográficas o lenguaje codificado podrían escapar. Mitigación: ampliar reglas o capas de guardrails, pero sin cambiar el contrato del flujo.
- **Bloqueo demasiado agresivo:** la experiencia del usuario puede degradarse si la respuesta no explica bien el motivo. Mitigación: mensajes neutrales y sugerencia clara de reformulación.
- **Doble moderación inconsistente:** entrada y salida podrían aplicar criterios distintos. Mitigación: una política compartida con decisiones y razones normalizadas.
- **Dependencia externa prematura:** usar un proveedor de moderación desde el inicio podría exponer datos. Mitigación: mantener la primera versión local salvo aprobación explícita.

## Open questions

Ninguna decisión bloqueante. El alcance inicial se limita al chat actual de RR. HH. y a la salida del agente antes de renderizarse.

## References

- `frontend/streamlit_postulacion.py`: punto actual de entrada del chat del agente.
- `backend/agent.py`: orquestación de respuestas y acceso al recuperador.
- `backend/rag_engine.py`: generación con Gemini y uso de contexto recuperado.
- `docs/sdd/proyecto.md`: contexto permanente del proyecto.
- `docs/sdd/constitucion.md`: reglas obligatorias de privacidad, seguridad y trazabilidad.