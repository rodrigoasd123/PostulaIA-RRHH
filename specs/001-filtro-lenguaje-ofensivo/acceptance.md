# Criterios de aceptación — Filtro de lenguaje ofensivo para el agente

**Característica:** moderación de lenguaje ofensivo en el chat del agente.

## AC-001 — Bloqueo de insulto directo

**Cubre:** FR-001, FR-002, NFR-001

```gherkin
Escenario: Bloquear un insulto directo antes de responder
  Dado un usuario en el chat del agente
  Cuando escribe un mensaje claramente ofensivo o insultante
  Entonces el sistema no envía ese mensaje al recuperador ni al modelo
  Y muestra una respuesta neutral que pide reformular el texto
```

**Evidencia prevista:** prueba unitaria de moderación con mensaje ofensivo y verificación de que no se invoca el flujo de respuesta.

## AC-002 — Falso positivo evitado

**Cubre:** FR-001, NFR-001

```gherkin
Escenario: No bloquear una consulta legítima con palabras ambiguas
  Dado un usuario que hace una pregunta profesional sin intención ofensiva
  Cuando el texto contiene una palabra que podría ser sensible fuera de contexto
  Entonces el mensaje se permite si no supera la política definida
```

**Evidencia prevista:** prueba con contexto benigno y palabra ambigua que no dispara el bloqueo.

## AC-003 — Salida segura del asistente

**Cubre:** FR-004, SEC-001

```gherkin
Escenario: Evitar mostrar una respuesta ofensiva generada por el asistente
  Dado que una respuesta interna contiene lenguaje ofensivo detectado
  Cuando el sistema va a mostrarla al usuario
  Entonces la respuesta se bloquea o se reemplaza por una alternativa neutral
```

**Evidencia prevista:** prueba con respuesta simulada ofensiva y verificación de sustitución segura.

## AC-004 — Continuidad tras reformulación

**Cubre:** FR-003, FR-005

```gherkin
Escenario: Reenviar una pregunta corregida después de un bloqueo
  Dado que un mensaje fue bloqueado por ofensivo
  Cuando el usuario lo reformula de manera respetuosa
  Entonces el agente acepta el nuevo mensaje
  Y conserva el contexto del chat y del documento activo
```

**Evidencia prevista:** prueba de estado de sesión o flujo de interfaz que confirma que el contexto no se pierde.

## AC-005 — No regresión del flujo normal

**Cubre:** FR-006, NFR-002

```gherkin
Escenario: Mantener intacta una consulta normal
  Dado un mensaje respetuoso sobre el perfil o un CV
  Cuando el sistema evalúa la moderación
  Entonces la consulta sigue el flujo actual de recuperación y respuesta
```

**Evidencia prevista:** prueba de regresión del chat existente con un mensaje no ofensivo.

## AC-006 — Política local por defecto

**Cubre:** NFR-002, SEC-003

```gherkin
Escenario: Operar sin proveedor externo para moderación
  Dado el agente configurado en su modo normal
  Cuando llega un mensaje para moderar
  Entonces la decisión se toma localmente sin llamar a un servicio externo obligatorio
```

**Evidencia prevista:** prueba sin red o con doble de dependencia que verifica que la moderación no depende de un endpoint remoto.
