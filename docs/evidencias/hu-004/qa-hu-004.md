# Informe QA — HU-004 Agendar una cita

- **HU:** HU-004 — Spec 004 (`specs/004_agendar-cita/spec.md`, enmendada 2026-10-09)
- **Rama:** `feature/hu-004`
- **Commit:** `eb10fc3` (suite sobre esta revisión)
- **Fecha:** 2026-10-09
- **Ejecución:** `python -m pytest -q` → **101 PASS / 0 FAIL** (74 previos de
  HU-001/002/003/016 + 27 nuevos de HU-004)

## Resumen

| Total | PASS | FAIL | BLOCKED |
|---|---|---|---|
| 27 | 27 | 0 | 0 |

## Casos de prueba

| Caso | Comando | Resultado | Observación |
|---|---|---|---|
| TC-004-001 | `python -m pytest tests/test_appointment_content.py -v` | PASS | 14 slots exactos 08:00–11:30 / 14:00–16:30, ordenados, sin duplicados |
| TC-004-002 | `python -m pytest tests/test_appointment_content.py -v` | PASS | CC, TI, CE, PASSPORT, RC con etiquetas en español |
| TC-004-003 | `python -m pytest tests/test_appointment_content.py -v` | PASS | Espejo spec ↔ plan ↔ `expected_content` ↔ `appointment_content` idéntico |
| TC-004-004 | `python -m pytest tests/test_appointment_persistence.py -v` | PASS | 11 columnas + `UNIQUE (service, date, time)` verificados vía `PRAGMA` |
| TC-004-005 | `python -m pytest tests/test_appointment_persistence.py -v` | PASS | `insert` con `status='pending'`; `get_appointment_by_id` recupera los 11 campos |
| TC-004-006 | `python -m pytest tests/test_appointment_persistence.py -v` | PASS | Segunda insert idéntica → `IntegrityError`, queda 1 fila |
| TC-004-007 | `python -m pytest tests/test_appointment_persistence.py -v` | PASS | Misma hora con servicio distinto → insert permitido |
| TC-004-008 | `python -m pytest tests/test_appointment_service.py -v` | PASS | Datos válidos → `{}` |
| TC-004-009 | `python -m pytest tests/test_appointment_service.py -v` | PASS | Cada campo obligatorio vacío → su mensaje literal exacto |
| TC-004-010 | `python -m pytest tests/test_appointment_service.py -v` | PASS | Formatos inválidos (correo, celular, documento, nombre, pasada, finde, hora) → mensaje específico; celular y documento solo dígitos |
| TC-004-011 | `python -m pytest tests/test_appointment_service.py -v` | PASS | Servicio fuera de catálogo → `MSG_INVALID_SERVICE`; nunca registra |
| TC-004-012 | `python -m pytest tests/test_appointment_service.py -v` | PASS | Disponibilidad = catálogo − ocupadas; finde/pasada → `[]` |
| TC-004-013 | `python -m pytest tests/test_appointment_service.py -v` | PASS | Tras `create_booking`, la hora desaparece de la disponibilidad |
| TC-004-014 | `python -m pytest tests/test_appointment_service.py -v` | PASS | Horario ocupado → `SLOT_TAKEN`, 1 sola fila |
| TC-004-015 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | `GET /citas` 200 con h1, 8 campos, horas y «Volver al inicio» |
| TC-004-016 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | `POST` válido → 303 → confirmación 200 «Cita registrada» + «Pendiente»; 1 fila |
| TC-004-017 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | `POST` sin cada obligatorio → 200 con mensaje y 0 filas |
| TC-004-018 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | `POST` inválido → 200, mensaje visible, valores conservados, 0 filas |
| TC-004-019 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | Horario ocupado → 200 con «Ese horario ya no está disponible…», exactamente 1 fila |
| TC-004-020 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | Servicio inválido → 200 + 0 filas; `/citas/horarios?service=fantasma` → 400 |
| TC-004-021 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | JSON 200 con horas libres; tras reservar desaparece; finde → `[]`; `POST` → 405 |
| TC-004-022 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | Confirmación inexistente → 404; `PUT /citas` → 405 |
| TC-004-023 | `python -m pytest tests/test_appointment_routes.py -v` | PASS | Regresión: placeholders sin `/citas`, nav de 6 hrefs, `/`, `/nosotros`, `/servicios`, `/buscar` intactos |
| TC-004-024 | `python -m pytest tests/test_hu_004.py -v` | PASS | Viewport, `@media`, paleta ⊆ 6 hex, justify + hyphens, JS sin dependencias |
| TC-004-025 | `python -m pytest tests/test_hu_004.py -v` | PASS | Formulario estrictamente de 8 campos (sin textarea ni campos extra) |
| TC-004-026 | `python -m pytest tests/test_hu_004.py -v` | PASS | E2E: home → «Agendar cita» → submit → confirmación con «Pendiente» |
| TC-004-027 | `python -m pytest tests/test_hu_004.py -v` | PASS | Fuera de alcance: sin textos de correo/WhatsApp/cancelación/n8n; portada y `/servicios` sin `<form>` |

## Regresión

| Suite | Resultado |
|---|---|
| HU-001/002/003/016 (74 tests previos) | PASS (0 FAIL, sin relajar aserciones) |
| `python -m pytest -q` (101 tests) | **101 PASS / 0 FAIL** |

## Demo manual (servidor `python app.py`, 2026-10-09)

Recorrido del flujo completo contra `http://127.0.0.1:5000`:

1. `GET /citas` → **200** con formulario de 8 campos y horas cargadas. ✔
2. `POST /citas` sin correo ni celular → **200** con ambos mensajes literales. ✔
3. `POST /citas` completo (Psiconutrición, 2026-10-12 08:00) → **303** →
   `GET /citas/confirmada/1` → **200** «Cita registrada», servicio, fecha, hora y
   estado «Pendiente». ✔
4. Segundo `POST` idéntico → **200** con «Ese horario ya no está disponible.
   Selecciona otro horario.»; sigue habiendo exactamente 1 fila. ✔
5. `GET /citas/horarios?service=nutrition&date=2026-10-12` → la hora `08:00`
   ya **no** aparece en `available`. ✔
6. `GET /citas/confirmada/999999` → **404**; `PUT /citas` → **405**. ✔
7. Verificación de disponibilidad al cambiar de servicio: el endpoint responde
   por `(service, date)`; Psicología Integral conserva sus 14 horas mientras
   Psiconutrición muestra 13. ✔

## Evidencia visual

| Fichero | Medidas programáticas | Verificación |
|---|---|---|
| `docs/evidencias/hu-004/escritorio-1280.png` | 1280×1488 | CDP `Emulation.setDeviceMetricsOverride`; `scrollWidth` = 1280 (sin desborde) |
| `docs/evidencias/hu-004/movil-375.png` | 375×1728 | CDP; `scrollWidth` = 375 (sin desborde) |

## Defectos encontrados

Ninguno.

## Trazabilidad

| Elemento | Estado |
|---|---|
| Spec 004 enmendada (dudas Q1/Q2 cerradas, literales fijados) | ✔ commit `f68b765` |
| Plan 004 (Q1–Q10 decididas) | ✔ commit `f68b765` |
| `task.md` T1–T18 | ✔ |
| Commits por fase (docs, contenido, persistencia, servicio, web, tests) | ✔ `f68b765`…`eb10fc3` |
| Servidor de revisión | `python app.py` → http://127.0.0.1:5000/citas |

## Veredicto

**PASS** — 27/27 TC en verde, 101/101 de la suite, regresión intacta y demo
manual del flujo completo verificada.

## Aceptación de la HU

- [ ] **ACEPTADA por la usuaria** (fecha: ____-__-__)
