# Criterios de aceptación — Asistente de revisión de CV para RR. HH.

**Característica:** revisión asistida de CV para Recursos Humanos.

## AC-001 — Comparación principal

**Cubre:** FR-001, FR-003, FR-004, FR-005

```gherkin
Escenario: Comparar y ordenar varios CV
  Dado un perfil con requisitos explícitos y dos CV válidos
  Cuando RR. HH. ejecuta la revisión
  Entonces obtiene ambos candidatos ordenados por un puntaje entero determinista de 0 a 100
```

**Evidencia:** `tests/test_cv_screening.py` (puntaje y ranking) y prueba manual en `http://127.0.0.1:8522`: dos CV OCR procesados, orden estable y puntajes 100/35.

## AC-002 — Explicación del puntaje

**Cubre:** FR-006, NFR-002

```gherkin
Escenario: Explicar el puntaje de un candidato
  Dado un candidato revisado
  Cuando el usuario abre su detalle
  Entonces cada requisito muestra estado, términos encontrados, página del perfil y página relevante del CV cuando existe
```

**Evidencia:** `test_candidate_score_and_evidence_are_explainable_and_deterministic` y navegador: C-001 mostró requisito, términos y páginas 1/1.

## AC-003 — Error aislado por CV

**Cubre:** FR-002

```gherkin
Escenario: Aislar el error de un CV ilegible
  Dado un lote con un CV válido y otro ilegible
  Cuando se procesa el lote
  Entonces el CV válido se analiza y el ilegible muestra un error asociado a su nombre
```

**Evidencia:** `test_invalid_cv_is_isolated_without_blocking_valid_candidates`.

## AC-004 — Perfil sin criterios

**Cubre:** FR-008

```gherkin
Escenario: Impedir un ranking sin criterios verificables
  Dado un perfil sin requisitos explícitos utilizables
  Cuando se intenta comparar CV
  Entonces no se genera ranking y se informa que faltan criterios verificables
```

**Evidencia:** `test_profile_without_requirements_does_not_invent_criteria` y estado de interfaz implementado.

## AC-005 — Criterio sensible

**Cubre:** SEC-003

```gherkin
Escenario: Excluir un criterio sensible
  Dado un perfil que incluye edad, género u otro atributo sensible como requisito
  Cuando se extraen los criterios
  Entonces ese requisito no participa del puntaje y aparece como advertencia de revisión humana
```

**Evidencia:** `test_sensitive_requirement_is_excluded_from_score_and_reported` y navegador: criterio de edad excluido con advertencia visible.

## AC-006 — Consulta limitada a fuentes

**Cubre:** FR-007, SEC-002

```gherkin
Escenario: Consultar solamente las fuentes seleccionadas
  Dado un candidato seleccionado
  Cuando el usuario hace una pregunta sobre su CV frente al perfil
  Entonces el agente responde solo con fragmentos del perfil y ese CV y cita páginas
```

**Evidencia:** `test_review_context_labels_profile_and_selected_cv_without_persistence`, `test_local_agent_answers_from_labeled_profile_and_cv_context` y `test_hr_mode_does_not_create_remote_embeddings`.

## AC-007 — Reproducibilidad y desempate

**Cubre:** FR-005, NFR-001

```gherkin
Escenario: Repetir la comparación con resultados estables
  Dado los mismos textos y candidatos con igual puntaje
  Cuando se ejecuta la comparación más de una vez
  Entonces los puntajes no cambian y el orden se resuelve por nombre de archivo
```

**Evidencia:** `test_ranking_uses_score_then_filename_as_stable_tiebreaker` y doble ejecución determinista en pruebas.

## AC-008 — Privacidad y decisión humana

**Cubre:** NFR-004, SEC-001, SEC-004

```gherkin
Escenario: Informar la privacidad y la decisión humana
  Dado la pantalla de resultados
  Cuando RR. HH. revisa el ranking
  Entonces ve que es orientativo, que requiere revisión humana y que los PDF no se almacenan
```

**Evidencia:** inspección de código sin persistencia del chat; navegador de escritorio y 390×844 mostró avisos de procesamiento local y decisión humana; consola sin errores.

## Registro de verificación

Regresión automatizada: `python -m pytest -q` → **17 pruebas aprobadas** el 2026-08-20.

| Criterio | Evidencia | Resultado |
|---|---|---|
| AC-001 | Pytest + lote OCR manual | APROBADO |
| AC-002 | Pytest + detalle visual | APROBADO |
| AC-003 | Pytest | APROBADO |
| AC-004 | Pytest + estado de interfaz | APROBADO |
| AC-005 | Pytest + advertencia visual | APROBADO |
| AC-006 | Pytest sin red | APROBADO |
| AC-007 | Pytest | APROBADO |
| AC-008 | Revisión de seguridad + navegador de escritorio/móvil | APROBADO |
