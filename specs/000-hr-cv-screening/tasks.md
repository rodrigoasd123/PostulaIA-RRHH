# Tasks — Asistente de revisión de CV para RR. HH.

## Preparation

- [x] **T-001** Inspeccionar arquitectura, pruebas y flujo actual. `[FR-001, NFR-003]`
- [x] **T-002** Confirmar que no existen preguntas bloqueantes para el MVP local. `[FR-001, FR-008]`

## Implementation

- [x] **T-010** Agregar modelos y servicio determinista de comparación. `[FR-003, FR-004, FR-005, FR-006, SEC-003]`
- [x] **T-011** Adaptar la interfaz a perfil + múltiples CV y errores aislados. `[FR-001, FR-002, FR-008, NFR-004]`
- [x] **T-012** Conservar consulta RAG para el candidato seleccionado. `[FR-007, SEC-002, SEC-004]`
- [x] **T-013** Actualizar documentación de arquitectura y uso. `[NFR-002, SEC-001]`

## Verification

- [x] **T-020** Añadir cobertura automatizada de los escenarios AC-001 a AC-008. `[AC-001, AC-002, AC-003, AC-004, AC-005, AC-006, AC-007, AC-008]`
- [x] **T-021** Ejecutar regresión completa y registrar resultados. `[NFR-001, NFR-003]`
- [x] **T-022** Verificar manualmente la aplicación local. `[FR-001, FR-006, FR-007, NFR-004]`

## Release

- [x] **T-030** Revisar el diff para evitar secretos, PDF o datos personales persistidos. `[SEC-001, SEC-004]`
- [x] **T-031** Confirmar estado y rollback; la publicación a GitHub queda fuera de este cambio hasta autorización explícita.
