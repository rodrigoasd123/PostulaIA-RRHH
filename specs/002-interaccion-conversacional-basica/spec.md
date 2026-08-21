---
id: SPEC-002
titulo: Interacción conversacional básica del agente
estado: VERIFICANDO
responsable_producto: Product and engineering
creado: 2026-08-20
actualizado: 2026-08-20
---

# SPEC-002 — Interacción conversacional básica del agente

## Problema y resultado esperado

El chat del flujo de RR. HH. trata los saludos y consultas de ayuda como preguntas documentales. Al no recuperar evidencia, responde que no hay información suficiente, una respuesta técnicamente consistente pero poco natural para iniciar una conversación.

El agente debe reconocer interacciones conversacionales simples y responder de forma cordial, explicando brevemente qué puede consultar la persona usuaria sin simular que respondió sobre un CV o una convocatoria.

## Usuarios y necesidades

- **Usuario principal:** analista o responsable de selección que inicia una consulta sobre un CV frente a un perfil.
- **Necesidad:** entender rápidamente el propósito y ejemplos de uso del chat, aun antes de formular una pregunta documental.

## Alcance

### Incluido

- Reconocer localmente saludos, despedidas, agradecimientos y solicitudes de ayuda breves en español.
- Devolver una respuesta profesional y breve para esas interacciones.
- Indicar que el agente puede responder sobre la relación entre el CV seleccionado y el perfil o convocatoria, con ejemplos de preguntas.
- Evitar la búsqueda de evidencia y las llamadas a Gemini u Ollama para dichas interacciones.
- Mantener la moderación vigente antes de clasificar la intención conversacional.
- Añadir pruebas unitarias de los casos conversacionales y de no regresión de preguntas documentales.

### Fuera de alcance

- Conversación abierta de propósito general.
- Modificar el ranking, el puntaje documental, la extracción de requisitos o las citas.
- Cambiar el flujo heredado de postulantes en `streamlit_postulacion.py`.
- Persistir historial, intención o telemetría adicionales.
- Añadir proveedores, modelos, dependencias o llamadas de red.

## Requisitos funcionales

- **FR-001:** El sistema debe clasificar localmente las interacciones conversacionales básicas permitidas después de la moderación y antes de recuperar evidencia.
- **FR-002:** Ante un saludo, el sistema debe responder cordialmente e indicar el propósito documental del agente y al menos un ejemplo de consulta válida.
- **FR-003:** Ante una solicitud breve de ayuda, el sistema debe explicar qué consultas documentales puede responder y dar ejemplos concretos.
- **FR-004:** Ante un agradecimiento o despedida, el sistema debe responder de forma breve y profesional sin afirmar hallazgos documentales.
- **FR-005:** Las preguntas documentales normales deben seguir usando el flujo actual de recuperación, Gemini opcional, Ollama opcional o fallback local.
- **FR-006:** Una interacción conversacional básica no debe modificar el ranking ni el contexto activo de documentos.

## Requisitos no funcionales

- **NFR-001:** La clasificación debe ser determinista y local, sin depender de red ni de un modelo externo.
- **NFR-002:** Las respuestas conversacionales deben ser breves, en español y no incluir datos del CV ni del perfil que no hayan sido consultados.

## Seguridad y privacidad

- **SEC-001:** La moderación de lenguaje ofensivo debe aplicarse antes de la clasificación conversacional; un mensaje bloqueado no debe recibir una respuesta de cortesía alternativa.
- **SEC-002:** Las interacciones conversacionales reconocidas no deben enviar texto a Gemini, Ollama ni a un proveedor adicional.

## Reglas y fuentes de verdad

- `backend/agent.py` es el punto de orquestación del chat del flujo principal.
- La política de moderación de `backend/moderation.py` conserva precedencia.
- Las respuestas documentales requieren evidencia recuperada; las conversacionales no deben presentarse como evidencia.

## Supuestos confirmados

- El idioma objetivo inicial es español.
- Se implementará con reglas locales conservadoras y solo para frases breves de intención clara.

## Riesgos y fallos esperados

- Una frase ambigua podría clasificarse como saludo cuando pretendía ser una consulta documental. Mitigación: reglas conservadoras y mantener el flujo documental para textos con términos de consulta.
- Respuestas demasiado amplias podrían hacer creer que el chat es un asistente general. Mitigación: orientar siempre hacia el análisis documental disponible.

## Preguntas abiertas

Ninguna decisión bloqueante.

## Historial de decisiones

| Fecha | Decisión | Responsable | Motivo |
|---|---|---|---|
| 2026-08-20 | Priorizar moderación sobre cortesía y no invocar LLM para frases conversacionales. | Product and engineering | Mantener el chat profesional, privado y predecible. |
