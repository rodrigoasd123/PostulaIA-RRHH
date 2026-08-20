# Asistente de revisión de CV para RR. HH.

- **ID:** SPEC-000
- **Status:** VERIFIED
- **Created:** 2026-08-20
- **Owner:** Product and engineering

## Problem

PostulaIA está orientada a una persona que interpreta una convocatoria antes de postular. El nuevo usuario es un equipo de Recursos Humanos que necesita revisar varios CV frente a un mismo perfil de puesto, reducir lectura repetitiva y conservar evidencia verificable. El sistema debe asistir la preselección sin sustituir el criterio humano ni emitir decisiones laborales automáticas.

## Users and outcomes

- **Primary user:** analista o responsable de selección de personal.
- **Desired outcome:** comparar varios CV contra requisitos explícitos del puesto, priorizar la revisión y consultar el sustento documental.
- **Success signal:** el usuario obtiene una lista ordenada reproducible, puede explicar cada coincidencia con páginas del perfil y del CV y comprende que el resultado no es una decisión de contratación.

## Scope

### Included

- Carga de un perfil de puesto o convocatoria en PDF y de uno o más CV en PDF.
- Lectura normal u OCR local para todos los documentos de una ejecución.
- Extracción de requisitos explícitos desde el perfil de puesto.
- Cálculo determinista de coincidencia documental por cobertura de términos.
- Ranking orientativo y detalle por candidato con evidencia y brechas.
- Consulta conversacional sobre un candidato seleccionado usando el perfil y su CV como fuentes.
- Uso opcional de Gemini u Ollama para redactar respuestas; el puntaje no depende de un LLM.

### Excluded

- Decidir, aprobar, rechazar o contactar postulantes automáticamente.
- Inferir personalidad, emociones, salud, raza, género, religión u otros atributos sensibles.
- Analizar fotografías o biometría.
- Integración con ATS, correo, calendarios o bolsas de trabajo.
- Persistencia de CV, índices vectoriales o expedientes de candidatos.
- Autenticación, roles o operación multiempresa en este prototipo local.

## Requirements

### Functional

- **FR-001:** El sistema debe aceptar exactamente un PDF de perfil de puesto y entre uno y veinte PDF de CV por ejecución.
- **FR-002:** El usuario debe poder elegir lectura normal u OCR; un CV inválido debe mostrar su error sin impedir el análisis de los demás CV válidos.
- **FR-003:** El sistema debe extraer requisitos explícitos del perfil y conservar la página fuente de cada requisito.
- **FR-004:** El sistema debe calcular para cada CV un puntaje entero de 0 a 100 mediante una fórmula determinista de cobertura de términos, sin usar un LLM para el cálculo.
- **FR-005:** El sistema debe ordenar los CV por puntaje descendente y usar el nombre del archivo como desempate estable.
- **FR-006:** El sistema debe mostrar por candidato las coincidencias altas, parciales y sin evidencia suficiente, junto con términos encontrados y la página más relevante del CV.
- **FR-007:** El usuario debe poder seleccionar un candidato y hacer preguntas sobre su adecuación al perfil; la respuesta debe limitarse al perfil y CV seleccionados y citar páginas.
- **FR-008:** Si el perfil no contiene requisitos explícitos utilizables, el sistema debe explicar que no puede generar un ranking y no debe inventar criterios.

### Non-functional

- **NFR-001:** Los mismos textos de perfil y CV deben producir los mismos requisitos, orden y puntajes.
- **NFR-002:** Todo puntaje debe ser explicable a partir de la fórmula documentada, los requisitos y los términos mostrados.
- **NFR-003:** El código de comparación debe estar desacoplado de Streamlit y cubierto por pruebas unitarias sin llamadas de red.
- **NFR-004:** La interfaz debe identificar el ranking como orientativo y mantener visible la necesidad de revisión humana.

### Security and privacy

- **SEC-001:** La extracción normal, OCR, fragmentación y puntaje deben ejecutarse localmente y los PDF no deben guardarse en disco por la aplicación.
- **SEC-002:** Cuando Gemini esté activo, solo se deben enviar fragmentos recuperados para responder una consulta, nunca el lote completo de CV.
- **SEC-003:** Los requisitos relacionados con atributos personales sensibles deben excluirse del puntaje y mostrarse como advertencias para revisión humana.
- **SEC-004:** El flujo de RR. HH. no debe persistir PDF, texto extraído, nombres de candidatos, preguntas ni respuestas; el chat debe vivir únicamente en la sesión de Streamlit.

## Constraints and invariants

- Se reutilizan `read_pdf`, OCR local, el recuperador híbrido y la API opcional de Gemini existentes.
- La coincidencia representa presencia documental de términos; no valida autenticidad, nivel real de competencia ni idoneidad laboral.
- El orden del ranking nunca constituye una recomendación de contratación.
- Los cambios locales previos de la interfaz de chat deben preservarse.
- Cada PDF debe limitarse a 20 MB y el lote a veinte CV para reducir agotamiento de memoria.

## Risks and failure modes

- **Requisitos ambiguos:** pueden producir puntajes poco representativos. Mitigación: mostrar el texto fuente y no clasificar como apto/no apto.
- **Sinónimos o redacción distinta:** la cobertura léxica puede omitir experiencia equivalente. Mitigación: etiquetar el resultado como coincidencia documental y permitir consulta con RAG.
- **OCR deficiente:** puede reducir coincidencias. Mitigación: mostrar errores por archivo y páginas extraídas para inspección.
- **Sesgo en el perfil:** un requisito sensible podría contaminar el ranking. Mitigación: excluir patrones sensibles y mostrar advertencia.
- **Exposición a proveedor LLM:** los fragmentos pueden contener datos personales. Mitigación: Gemini es opcional, se informa el flujo y el puntaje funciona localmente.

## Open questions

No hay decisiones bloqueantes para este MVP local. Integraciones ATS, persistencia y criterios configurables quedan para futuras especificaciones.

## References

- `backend/pdf_reader.py`: lectura normal y OCR.
- `backend/rag_engine.py`: recuperación FAISS/léxica y respuestas Gemini.
- `frontend/streamlit_postulacion.py`: interfaz actual que esta especificación reemplaza.
