---
id: SPEC-003
titulo: Caché vectorial y reutilización segura de respuestas
estado: VERIFICANDO
responsable_producto: Product and engineering
creado: 2026-08-20
actualizado: 2026-08-21
---

# SPEC-003 — Caché vectorial y reutilización segura de respuestas

## Problema y resultado esperado

El flujo principal vuelve a fragmentar y buscar los mismos documentos en cada uso y llama nuevamente al modelo ante preguntas documentales repetidas. Esto aumenta latencia y consumo del proveedor. Se necesita una caché local persistente que reutilice embeddings del mismo perfil o CV y, cuando sea seguro, respuestas ya generadas para exactamente el mismo contexto documental.

El resultado esperado es que un PDF idéntico, identificado por una huella criptográfica, reutilice sus vectores durante un máximo de 24 horas, y que una pregunta repetida o semánticamente equivalente sobre el mismo perfil y CV pueda responderse sin una nueva llamada al modelo. La persona de RR. HH. podrá borrar la caché antes de que expire.

## Usuarios y necesidades

- **Usuario principal:** analista de RR. HH. que consulta repetidamente uno o varios CV frente al mismo perfil.
- **Necesidad:** reducir tiempos y consumo de tokens sin mezclar candidatos, perder citas ni conservar datos indefinidamente.

## Alcance

### Incluido

- Generación local de embeddings multilingües para fragmentos del perfil y de cada CV.
- Índice vectorial local persistente asociado a la huella SHA-256 del contenido del PDF, versión del modelo y versión del fragmentador.
- Reutilización de embeddings mientras el registro no haya vencido y siga siendo compatible.
- Caché local de respuestas documentales exitosas, aislada por huellas del perfil y CV seleccionado, pregunta, modelo de respuesta y versión del prompt.
- Coincidencia exacta normalizada y coincidencia semántica conservadora de preguntas únicamente dentro del mismo contexto documental.
- TTL fijo de 24 horas desde la creación de cada entrada.
- Eliminación automática de entradas vencidas y control visible para borrar manualmente toda la caché vectorial y de respuestas.
- Indicador en la interfaz que diferencie una respuesta generada de una respuesta recuperada de caché.
- Visualización local de las respuestas reutilizables del perfil y CV activos, con pregunta truncada, ruta, creación, expiración y contador de reutilizaciones.
- Métricas locales agregadas de aciertos exactos, aciertos semánticos, misses, tasa de reutilización y llamadas generativas evitadas.
- Eliminación individual de una respuesta reutilizable sin borrar los índices documentales ni otras respuestas.
- Fallback a recuperación léxica si la base vectorial está ausente, corrupta, vencida o no puede inicializarse.
- Pruebas sin red para aislamiento, expiración, invalidación, borrado, recuperación y no regresión.

### Fuera de alcance

- Guardar los archivos PDF originales.
- Compartir caché entre equipos, máquinas, usuarios o despliegues.
- Autenticación, autorización, multiempresa o despliegue compartido.
- Usar embeddings remotos de Gemini para los CV en el flujo principal.
- Modificar el ranking, puntaje documental, criterios sensibles o decisión humana obligatoria.
- Persistencia indefinida, copias de seguridad o restauración de la caché.
- Reutilizar respuestas entre CV diferentes aunque la pregunta sea igual.
- Integración con LangSmith u otro servicio externo de trazas, telemetría o evaluación.

## Requisitos funcionales

- **FR-001:** El sistema debe calcular una huella SHA-256 del contenido de cada perfil y CV sin utilizar el nombre de la persona como identificador primario.
- **FR-002:** El sistema debe dividir el texto extraído en fragmentos con página y tipo de fuente, generar embeddings localmente y persistir el índice bajo una clave que incluya huella, modelo y versión del fragmentador.
- **FR-003:** Cuando exista un índice compatible y vigente para el mismo PDF, el sistema debe reutilizarlo sin regenerar embeddings.
- **FR-004:** Cuando cambie el PDF, el modelo de embeddings o la versión del fragmentador, el sistema debe crear una entrada diferente y no reutilizar vectores incompatibles.
- **FR-005:** La búsqueda documental del chat debe limitarse al perfil activo y al CV seleccionado, conservando fuente y página en la evidencia.
- **FR-006:** Después de generar una respuesta documental exitosa, el sistema debe poder guardar pregunta, respuesta, citas y metadatos técnicos necesarios para una reutilización segura.
- **FR-007:** Antes de llamar a Gemini u Ollama, el sistema debe buscar una respuesta vigente dentro del mismo par perfil-CV y reutilizarla solo si la pregunta coincide exactamente o supera un umbral semántico conservador definido y probado.
- **FR-008:** El sistema nunca debe reutilizar respuestas si cambian el perfil, el CV, el modelo de respuesta, la versión del prompt o la política de moderación relevante.
- **FR-009:** El sistema debe eliminar entradas con más de 24 horas antes de leer o escribir la caché y durante el arranque de la aplicación.
- **FR-010:** La interfaz debe proporcionar una acción explícita para borrar inmediatamente todos los vectores, fragmentos, preguntas y respuestas persistidos por esta funcionalidad.
- **FR-011:** La interfaz debe informar si una respuesta provino de caché o fue generada en la consulta actual.
- **FR-012:** Si la caché falla, el agente debe continuar con recuperación léxica y el flujo de respuesta existente sin alterar el ranking.
- **FR-013:** La interfaz debe listar las respuestas reutilizables vigentes únicamente para el perfil y CV activos, mostrando una vista truncada de la pregunta, ruta de respuesta, fecha de creación, tiempo restante y cantidad de reutilizaciones, sin persistir nombres nuevos para construir la vista.
- **FR-014:** La persona de RR. HH. debe poder eliminar una respuesta reutilizable individual y recibir confirmación, sin eliminar vectores, fragmentos ni otras respuestas.
- **FR-015:** El sistema debe mantener y mostrar contadores locales agregados de aciertos exactos, aciertos semánticos, misses de respuesta, tasa de reutilización y llamadas generativas evitadas.

## Requisitos no funcionales

- **NFR-001:** La generación y comparación de embeddings debe funcionar localmente después de instalar el modelo requerido y no enviar texto de CV al proveedor de embeddings.
- **NFR-002:** La caché debe producir decisiones deterministas para coincidencias exactas y usar un umbral configurable y conservador para coincidencias semánticas.
- **NFR-003:** Una reutilización válida debe evitar una nueva llamada al modelo generativo y hacer observable el ahorro mediante el origen de la respuesta.
- **NFR-004:** La ubicación, esquema y versiones de la caché deben estar documentados y ser reversibles mediante eliminación de sus artefactos.
- **NFR-005:** Las pruebas automatizadas no deben descargar modelos ni efectuar llamadas de red; usarán dobles deterministas de embeddings y del modelo generativo.
- **NFR-006:** La visualización y sus métricas deben funcionar sin red, no añadir llamadas al modelo y conservar la compatibilidad con las entradas de caché creadas antes del refinamiento.

## Seguridad y privacidad

- **SEC-001:** Los embeddings, fragmentos, preguntas, respuestas y citas deben tratarse como datos personales derivados de los CV.
- **SEC-002:** La persistencia debe ubicarse exclusivamente bajo `data/` en el equipo local y permanecer excluida del control de versiones.
- **SEC-003:** El sistema no debe persistir PDFs originales, claves API ni nombres personales como claves primarias de la caché.
- **SEC-004:** La moderación de entrada debe ejecutarse antes de consultar o escribir la caché, y la moderación de salida debe aplicarse también a respuestas recuperadas.
- **SEC-005:** Toda búsqueda y reutilización debe filtrar primero por las huellas exactas del perfil activo y CV seleccionado para impedir cruces entre candidatos.
- **SEC-006:** La acción manual de borrado debe eliminar tanto el índice vectorial como sus fragmentos y las respuestas asociadas, y mostrar confirmación del resultado.
- **SEC-007:** Esta versión local no añadirá cifrado de aplicación en reposo; dependerá de los permisos del sistema operativo y no podrá considerarse apta para despliegue compartido.
- **SEC-008:** Los registros de ejecución no deben incluir texto de CV, preguntas completas, respuestas completas, embeddings ni claves.
- **SEC-009:** El detalle visible debe filtrarse por las huellas exactas del perfil y CV activos; la pregunta se mostrará truncada, no se mostrará la respuesta completa y no se persistirán nombres de candidatos como parte de las métricas.

## Reglas y fuentes de verdad

- El PDF cargado es la fuente de verdad; su SHA-256 determina identidad de contenido.
- Las citas válidas deben conservar fuente y página originales.
- El ranking determinista permanece independiente de la base vectorial y de la caché de respuestas.
- Una entrada expirada, incompatible o corrupta equivale a una ausencia de caché.
- Saludos, ayuda, despedidas, mensajes bloqueados y respuestas sin evidencia suficiente no se almacenan como respuestas reutilizables.

## Supuestos confirmados

- La aplicación seguirá ejecutándose localmente para una sola persona operadora a la vez.
- El TTL aprobado es de 24 horas y no será prorrogado por cada lectura.
- La persona de RR. HH. podrá borrar toda la caché antes del vencimiento.
- Los embeddings serán locales; una descarga inicial del modelo y su impacto de instalación se definirán en el plan técnico.
- Se conservarán fragmentos de texto derivados del PDF porque son necesarios para reconstruir citas; no se conservará el PDF original.

## Riesgos y fallos esperados

- **Respuesta equivocada por similitud:** una pregunta parecida puede tener intención distinta. Mitigación: aislamiento documental, umbral alto, pruebas negativas y fallback a generación.
- **Exposición local de datos derivados:** los fragmentos y respuestas quedan en disco hasta 24 horas. Mitigación: ubicación local excluida de Git, TTL, borrado manual y restricción a uso no compartido.
- **Modelo local pesado o incompatible:** la instalación puede aumentar tamaño y tiempo inicial. Mitigación: validar compatibilidad en el plan y conservar fallback léxico.
- **Índice corrupto o versión incompatible:** FAISS puede no cargar. Mitigación: invalidar y reconstruir sin interrumpir el chat.
- **Crecimiento de almacenamiento:** cargas repetidas generan múltiples versiones. Mitigación: limpieza automática y métricas visibles de entradas y espacio utilizado.

## Preguntas abiertas

Ninguna decisión de producto bloqueante. El addendum R1 está implementado y pendiente de aceptación manual.

## Historial de decisiones

| Fecha | Decisión | Responsable | Motivo |
|---|---|---|---|
| 2026-08-20 | Persistencia local con TTL fijo de 24 horas y borrado manual. | Product and engineering | Reducir recomputación sin conservación indefinida. |
| 2026-08-20 | Aislar vectores y respuestas por huellas del perfil y CV. | Product and engineering | Evitar reutilización entre candidatos. |
| 2026-08-20 | No guardar PDFs originales ni usar embeddings remotos por defecto. | Product and engineering | Minimización y privacidad de datos. |
| 2026-08-20 | Alcance y criterios de aceptación aprobados. | Responsable de producto | Autoriza avanzar a planificación técnica. |
| 2026-08-20 | Plan técnico aprobado e implementación iniciada. | Responsable de producto | Invocación explícita de `$sdd-implement-es`. |
| 2026-08-20 | Refinamiento R1: visualización local, métricas y borrado individual; LangSmith excluido. | Responsable de producto | Hacer observable la reutilización sin enviar datos de candidatos a servicios externos. |
| 2026-08-20 | Refinamiento R1 aprobado. | Responsable de producto | Autoriza regenerar parcialmente el plan para FR-013 a FR-015 y AC-010 a AC-012. |
| 2026-08-20 | Addendum técnico R1 aprobado. | Responsable de producto | Autoriza implementar T-011 a T-015 mediante `$sdd-implement-es`. |
| 2026-08-20 | Implementación del addendum R1 iniciada. | Responsable de producto | Invocación explícita de `$sdd-implement-es`. |
| 2026-08-21 | Implementación R1 completada y pasada a verificación. | Equipo de implementación | Pruebas automatizadas aprobadas; queda pendiente el recorrido manual de RR. HH. |
