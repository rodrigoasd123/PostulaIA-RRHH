# Acceptance — Asistente de revisión de CV para RR. HH.

## AC-001 — Comparación principal

**Covers:** FR-001, FR-003, FR-004, FR-005

```gherkin
Given un perfil con requisitos explícitos y dos CV válidos
When RR. HH. ejecuta la revisión
Then obtiene ambos candidatos ordenados por un puntaje entero determinista de 0 a 100
```

**Evidence:** `tests/test_cv_screening.py` (puntaje y ranking) y prueba manual en `http://127.0.0.1:8522`: dos CV OCR procesados, orden estable y puntajes 100/35.

## AC-002 — Explicación del puntaje

**Covers:** FR-006, NFR-002

```gherkin
Given un candidato revisado
When el usuario abre su detalle
Then cada requisito muestra estado, términos encontrados, página del perfil y página relevante del CV cuando existe
```

**Evidence:** `test_candidate_score_and_evidence_are_explainable_and_deterministic` y navegador: C-001 mostró requisito, términos y páginas 1/1.

## AC-003 — Error aislado por CV

**Covers:** FR-002

```gherkin
Given un lote con un CV válido y otro ilegible
When se procesa el lote
Then el CV válido se analiza y el ilegible muestra un error asociado a su nombre
```

**Evidence:** `test_invalid_cv_is_isolated_without_blocking_valid_candidates`.

## AC-004 — Perfil sin criterios

**Covers:** FR-008

```gherkin
Given un perfil sin requisitos explícitos utilizables
When se intenta comparar CV
Then no se genera ranking y se informa que faltan criterios verificables
```

**Evidence:** `test_profile_without_requirements_does_not_invent_criteria` y estado de interfaz implementado.

## AC-005 — Criterio sensible

**Covers:** SEC-003

```gherkin
Given un perfil que incluye edad, género u otro atributo sensible como requisito
When se extraen los criterios
Then ese requisito no participa del puntaje y aparece como advertencia de revisión humana
```

**Evidence:** `test_sensitive_requirement_is_excluded_from_score_and_reported` y navegador: criterio de edad excluido con advertencia visible.

## AC-006 — Consulta limitada a fuentes

**Covers:** FR-007, SEC-002

```gherkin
Given un candidato seleccionado
When el usuario hace una pregunta sobre su CV frente al perfil
Then el agente responde solo con fragmentos del perfil y ese CV y cita páginas
```

**Evidence:** `test_review_context_labels_profile_and_selected_cv_without_persistence`, `test_local_agent_answers_from_labeled_profile_and_cv_context` y `test_hr_mode_does_not_create_remote_embeddings`.

## AC-007 — Reproducibilidad y desempate

**Covers:** FR-005, NFR-001

```gherkin
Given los mismos textos y candidatos con igual puntaje
When se ejecuta la comparación más de una vez
Then los puntajes no cambian y el orden se resuelve por nombre de archivo
```

**Evidence:** `test_ranking_uses_score_then_filename_as_stable_tiebreaker` y doble ejecución determinista en pruebas.

## AC-008 — Privacidad y decisión humana

**Covers:** NFR-004, SEC-001, SEC-004

```gherkin
Given la pantalla de resultados
When RR. HH. revisa el ranking
Then ve que es orientativo, que requiere revisión humana y que los PDF no se almacenan
```

**Evidence:** inspección de código sin persistencia del chat; navegador de escritorio y 390×844 mostró avisos de procesamiento local y decisión humana; consola sin errores.

## Verification record

Automated regression: `python -m pytest -q` → **17 passed** on 2026-08-20.

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | Pytest + lote OCR manual | PASS |
| AC-002 | Pytest + detalle visual | PASS |
| AC-003 | Pytest | PASS |
| AC-004 | Pytest + estado de interfaz | PASS |
| AC-005 | Pytest + advertencia visual | PASS |
| AC-006 | Pytest sin red | PASS |
| AC-007 | Pytest | PASS |
| AC-008 | Revisión de seguridad + navegador desktop/móvil | PASS |
