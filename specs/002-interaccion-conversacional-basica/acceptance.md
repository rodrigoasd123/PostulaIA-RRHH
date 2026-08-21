# Criterios de aceptación — Interacción conversacional básica del agente

**Característica:** respuestas útiles para interacciones sociales simples en el chat de RR. HH.

## AC-001 — Saludo orientador

**Cubre:** FR-001, FR-002, NFR-001, NFR-002

```gherkin
Escenario: Saludar al agente
  Dado un CV y un perfil cargados en el chat
  Cuando la persona escribe un saludo breve como "hola"
  Entonces el sistema responde cordialmente
  Y explica que puede ayudar a consultar el CV frente al perfil
  Y incluye al menos un ejemplo de pregunta documental
  Y no ejecuta recuperación de evidencia ni un modelo externo
```

**Evidencia requerida:** prueba unitaria que verifica respuesta y ausencia de llamada al recuperador.

## AC-002 — Ayuda de uso

**Cubre:** FR-003, SEC-002

```gherkin
Escenario: Pedir ayuda sobre el chat
  Dado un CV y un perfil cargados en el chat
  Cuando la persona pregunta "¿qué puedes hacer?"
  Entonces el sistema describe consultas documentales soportadas
  Y no afirma hallazgos sobre el CV ni el perfil
  Y no invoca Gemini ni Ollama
```

**Evidencia requerida:** prueba unitaria de respuesta orientadora sin llamadas remotas.

## AC-003 — Cierre cordial

**Cubre:** FR-004

```gherkin
Escenario: Agradecer al agente
  Dado una conversación activa
  Cuando la persona escribe un agradecimiento breve
  Entonces el sistema responde de forma breve y profesional
  Y no recupera evidencia documental
```

**Evidencia requerida:** prueba unitaria de intención de agradecimiento.

## AC-004 — Precedencia de moderación

**Cubre:** SEC-001

```gherkin
Escenario: Bloquear un saludo ofensivo
  Dado un mensaje que incluye lenguaje ofensivo
  Cuando el texto también contiene un saludo
  Entonces el sistema aplica la respuesta de moderación vigente
  Y no devuelve una respuesta de bienvenida
```

**Evidencia requerida:** prueba de regresión que verifica el mensaje de bloqueo.

## AC-005 — No regresión documental

**Cubre:** FR-005, FR-006

```gherkin
Escenario: Consultar evidencia del CV o perfil
  Dado una pregunta respetuosa sobre un requisito documental
  Cuando la persona la envía al agente
  Entonces el sistema conserva el flujo actual de recuperación y respuesta
  Y devuelve evidencia asociada al documento cuando la encuentra
  Y no altera el ranking ni el contexto activo
```

**Evidencia requerida:** pruebas existentes del agente más una prueba focalizada si corresponde.
