# Criterios de aceptación — SPEC-003

**Característica:** caché vectorial local y reutilización segura de respuestas documentales.

## AC-001 — Reutilizar embeddings del mismo PDF

**Cubre:** FR-001, FR-002, FR-003, NFR-001

```gherkin
Escenario: Cargar nuevamente un CV idéntico dentro del TTL
  Dado que existe un índice vigente para la huella, modelo y fragmentador del CV
  Cuando la persona carga exactamente el mismo PDF
  Entonces el sistema reutiliza el índice persistido
  Y no vuelve a generar embeddings para sus fragmentos
```

**Evidencia requerida:** prueba automatizada con generador de embeddings simulado y contador de llamadas.

## AC-002 — Invalidar documentos o versiones diferentes

**Cubre:** FR-004

```gherkin
Escenario: Evitar vectores incompatibles
  Dado que existe un índice para una versión anterior
  Cuando cambia el contenido del PDF, el modelo o el fragmentador
  Entonces el sistema no reutiliza ese índice
  Y crea una entrada independiente o reconstruye la correspondiente
```

**Evidencia requerida:** pruebas parametrizadas de huella y versiones distintas.

## AC-003 — Aislar la búsqueda por candidato

**Cubre:** FR-005, SEC-005

```gherkin
Escenario: Consultar el CV seleccionado
  Dado un perfil y dos CV con índices vigentes
  Cuando se consulta el segundo CV
  Entonces la evidencia recuperada pertenece solo al perfil y al segundo CV
  Y no contiene fragmentos del primer CV
```

**Evidencia requerida:** prueba de aislamiento con fragmentos distinguibles y citas por página.

## AC-004 — Reutilizar una respuesta segura

**Cubre:** FR-006, FR-007, FR-008, NFR-003

```gherkin
Escenario: Repetir una pregunta sobre los mismos documentos
  Dado una respuesta exitosa y vigente para el mismo perfil, CV, modelo y prompt
  Cuando se realiza la misma pregunta o una variante que supera el umbral aprobado
  Entonces el sistema devuelve la respuesta y citas guardadas
  Y identifica su origen como caché
  Y no llama al modelo generativo
```

**Evidencia requerida:** prueba con modelo simulado que falla si se invoca por segunda vez.

## AC-005 — No cruzar respuestas entre CV

**Cubre:** FR-008, SEC-005

```gherkin
Escenario: Repetir una pregunta con otro candidato
  Dado una respuesta guardada para el CV de un candidato
  Cuando se hace la misma pregunta con un CV de huella diferente
  Entonces el sistema no reutiliza la respuesta anterior
  Y ejecuta el flujo normal para el nuevo contexto
```

**Evidencia requerida:** prueba de aislamiento por huellas documentales.

## AC-006 — Expirar después de 24 horas

**Cubre:** FR-009

```gherkin
Escenario: Acceder a una entrada vencida
  Dado una entrada creada hace 24 horas o más
  Cuando el sistema inicia o consulta la caché
  Entonces elimina o ignora la entrada y sus artefactos asociados
  Y vuelve a generar lo necesario mediante el flujo normal
```

**Evidencia requerida:** prueba con reloj controlado en el límite anterior, exacto y posterior a 24 horas.

## AC-007 — Borrado manual completo

**Cubre:** FR-010, SEC-006

```gherkin
Escenario: RR. HH. borra los datos persistidos
  Dado que existen vectores, fragmentos y respuestas en caché
  Cuando la persona confirma la acción de borrar caché
  Entonces se eliminan todos los artefactos creados por la funcionalidad
  Y la interfaz confirma el resultado
  Y una consulta posterior reconstruye los datos necesarios
```

**Evidencia requerida:** prueba de servicio de borrado y verificación manual reproducible de la interfaz.

## AC-008 — Continuar ante fallo de la base vectorial

**Cubre:** FR-012

```gherkin
Escenario: El índice local no puede abrirse
  Dado un índice ausente, corrupto o incompatible
  Cuando el agente intenta recuperar evidencia
  Entonces continúa con búsqueda léxica local
  Y no modifica el ranking ni bloquea la consulta
```

**Evidencia requerida:** prueba con carga de índice fallida y verificación del fallback.

## AC-009 — Proteger contenido moderado y secretos

**Cubre:** SEC-003, SEC-004, SEC-008

```gherkin
Escenario: Procesar una entrada bloqueada
  Dado un mensaje ofensivo o una configuración con una clave API
  Cuando el agente procesa la interacción
  Entonces no guarda el mensaje bloqueado ni la clave en la caché o logs
  Y no devuelve una respuesta cacheada que evada la moderación vigente
```

**Evidencia requerida:** pruebas de precedencia de moderación e inspección de persistencia y logs de prueba.

## AC-010 — Visualizar respuestas del contexto activo

**Cubre:** FR-013, NFR-006, SEC-009

```gherkin
Escenario: Revisar qué respuestas pueden reutilizarse
  Dado un perfil y CV activos con respuestas vigentes y respuestas de otros contextos
  Cuando la persona abre el detalle de respuestas reutilizables
  Entonces ve únicamente las entradas del perfil y CV activos
  Y cada entrada muestra la pregunta truncada, ruta, creación, expiración y reutilizaciones
  Y no muestra respuestas completas ni nombres persistidos como identificadores
```

**Evidencia requerida:** prueba de consulta filtrada por huellas y recorrido manual de la interfaz con dos CV distinguibles.

## AC-011 — Medir reutilización sin telemetría externa

**Cubre:** FR-015, NFR-003, NFR-006, SEC-009

```gherkin
Escenario: Registrar hits y misses de respuestas
  Dado un contexto activo con una respuesta cacheada
  Cuando ocurre un hit exacto, un hit semántico y un miss
  Entonces se incrementan por separado los contadores locales correspondientes
  Y la tasa de reutilización y las llamadas generativas evitadas son consistentes
  Y no se realiza ninguna llamada de red para producir las métricas
```

**Evidencia requerida:** prueba con reloj y embeddings inyectados que verifique contadores, tasa y ausencia de proveedor externo.

## AC-012 — Borrar una sola respuesta reutilizable

**Cubre:** FR-014, SEC-006, SEC-009

```gherkin
Escenario: Eliminar una entrada del contexto activo
  Dado que existen dos respuestas reutilizables y un índice documental vigente
  Cuando RR. HH. elimina y confirma una de las respuestas
  Entonces solo esa respuesta deja de estar disponible
  Y la otra respuesta y los índices documentales permanecen vigentes
  Y la interfaz confirma el resultado
```

**Evidencia requerida:** prueba de servicio con dos respuestas y verificación manual del control individual.
