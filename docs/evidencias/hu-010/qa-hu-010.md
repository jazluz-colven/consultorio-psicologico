# QA HU-010 — Notificar la cancelación de una cita

> HU: HU-010 · Spec 010 (enmendada 2026-10-13) · Rama: `feature/hu-010`
> Commit de docs: `9b6a850` (spec+plan+task) · Implementación y tests: sin
> commit aún (T14 pendiente de la usuaria).
> Fecha: 2026-10-13 · Suite: `python -m pytest -q` → **204 passed / 0 FAIL**
> (187 previos intactos + 17 nuevos TC-010-001…017; TC-010-018 es la corrida
> de suite).

## Resumen

- Total TC de la HU: **18** (17 funciones + corrida de suite; TC-010-018 =
  corrida completa)
- PASS: **18** · FAIL: **0** · BLOCKED: **0**
- Regresión: **187/187 previos intactos** (HU-001/002/003/016/004/005/006/007/
  008/015/contraste); TC-004-004 y TC-006-013 **adaptados** (spec-backed) al
  índice único parcial de la enmienda, sin relajar garantías.

## Casos de prueba

| Caso | Comando | Resultado | Observación |
|------|---------|-----------|-------------|
| TC-010-001 | `python -m pytest tests/test_cancellation_service.py -v` | PASS | 2xx → cita `cancelled` + evento `appointment.cancellation_email` `sent` con `sent_at` + 1 POST (`recipient`/`message` completos, `appointment.status='cancelled'`) |
| TC-010-002 | ídem | PASS | Asunto «Cita cancelada — …», texto con servicio, fecha legible, hora, «Cancelada» y `#{id}`; HTML ⊆ 6 hex de paleta, sin remotos; sin documento/teléfono |
| TC-010-003 | ídem | PASS | URL vacía → `cancelled` + evento `skipped` «Envío de correo no configurado.» + 0 POST |
| TC-010-004 | ídem | PASS | `URLError` → evento `failed` «Servicio de automatización no disponible.», sin excepción, cita sigue `cancelled` |
| TC-010-005 | ídem | PASS | `TimeoutError` → evento `failed` «Tiempo de espera agotado (timeout).», cita sigue `cancelled` |
| TC-010-006 | ídem | PASS | Reproceso → `ALREADY_CANCELLED`, **1 evento** total y **1 POST** acumulado |
| TC-010-007 | ídem | PASS | Email vacía (defensivo) → cita `cancelled` + 0 POST + evento `failed` «Dirección de correo del paciente ausente o no válida.» |
| TC-010-008 | ídem | PASS | Datos incompletos → 0 POST + evento `failed` «Datos de la cita incompletos.» |
| TC-010-009 | ídem | PASS | Repositorio caído (`RuntimeError`) → `cancel_appointment()` devuelve la `Appointment` `cancelled` (cambio no se revierte) |
| TC-010-010 | ídem | PASS | Allowlist: `event_id` determinista `appointment.cancellation_email:{id}:v1`, `event_version=1`; sin `document_*`/`phone` (raíz y `appointment`) |
| TC-010-011 | ídem | PASS | Cancelar → `is_slot_taken()` = `False` y la hora vuelve a estar **libre** en `get_hours_with_status()` |
| TC-010-012 | ídem | PASS | Slot `confirmed` → `create_booking()` → `SLOT_TAKEN`, 0 filas nuevas (índice parcial intacto) |
| TC-010-013 | `python -m pytest tests/test_hu_010.py -v` | PASS | Tras cancelar se puede re-reservar el mismo `service+date+time` (fila nueva; la cancelada permanece) |
| TC-010-014 | ídem | PASS | BD con SCHEMA antiguo → `init_db()` migra (índice parcial, datos conservados, 1 backup `.bak-*`), idempotente; duplicados activos → aborta (`RuntimeError`) sin tocar filas |
| TC-010-015 | ídem | PASS | HTTP: 303 → cancelar → `/citas/horarios` hora `available` → `/citas/disponibilidad` reabre el día → `POST /citas` 303 con fila nueva |
| TC-010-016 | ídem | PASS | Espejo `expected_content` == módulos de contenido (6 literales); config solo `AUTOMATION_WEBHOOK_URL`/`_TIMEOUT_SECONDS`/`_WEBHOOK_AUTH_HEADER` (sin variables nuevas) |
| TC-010-017 | ídem | PASS | Regresión funcional HU-004/005/006/007/008 (reserva, disponibilidad, doble reserva, eventos `confirmed` y `confirmation_email` intactos) + constitución #1 (AST: stdlib-only en los 4 módulos tocados) |
| TC-010-018 | `python -m pytest -q` | PASS | **204 passed / 0 FAIL** (corrida de suite, no una función) |

## Demo manual (plan §6.2)

Receptor stdlib local (puerto 8766) capturando JSON sobre el webhook y app de
demo (`TestConfig` con `AUTOMATION_WEBHOOK_URL` apuntando al receptor). Script
efímero fuera del repo; evidencia en `docs/evidencias/hu-010/`:

| Paso | Escenario | Resultado | Evidencia |
|------|-----------|-----------|-----------|
| a | Reserva `POST /citas` → `cancel_appointment()` con receptor arriba | Cita **`cancelled`** + **1 POST** cancellation con subject/text/html de §2.2 | `demo-step1-cancelacion.json`, `webhook_payloads.jsonl` |
| b | Evento `appointment.cancellation_email` | **`sent`** con `sent_at` | `demo-step2-evento-sent.json` |
| c | Segunda cancelación de la misma cita | **`already_cancelled`** y **0 POST** nuevos | `demo-step3-reproceso.json` |
| d | Receptor apagado: nueva reserva y cancelación | Cancelación **intacta** (`cancelled`) + evento **`failed`** «Servicio de automatización no disponible.» | `demo-step4-receptor-caido.json` |
| e | Tras cancelar (paso a): `/citas/horarios` y re-reserva | Hora **`available`**; `POST /citas` → **303** con fila nueva | `demo-step5-re-reserva.json` |
| — | Dump de `automation_events` | Eventos `confirmed`/`confirmation_email` (HU-007/008) y `cancellation_email` coexistentes con sus estados | `automation_events_dump.json` |

## Defectos encontrados

- Ninguno.

## Regresión

- HU-004 (agendamiento): intacta (validación 200, 303/200).
- HU-005 (disponibilidad): intacta (`/citas/horarios`, `/citas/disponibilidad`).
- HU-006 (doble reserva): intacta (índice parcial + `SLOT_TAKEN`); TC-006-013
  y TC-004-004 adaptados al nuevo esquema según la enmienda de la spec 010
  (aserción sobre `sqlite_master`: `UNIQUE` ausente de la tabla + índice
  parcial con `status <> 'cancelled'`), sin relajar la garantía de unicidad.
- HU-007/008 (automatización y correo): intactas; los eventos conviven con
  `appointment.cancellation_email` y los POST se filtran por `event_type`.
- Suite completa: **204/204**.

## Criterios de aceptación (spec 010 enmendada)

- [x] RF-1: cita que cambia a Cancelada (commit confirmado) → notificación de cancelación enviada (TC-010-001/003/004/005/009, demo pasos a–b).
- [x] RF-2: la notificación indica claramente que la cita fue cancelada («Cita cancelada», estado «Cancelada») (TC-010-002/016, demo paso a).
- [x] RF-3 («cuando corresponda»): correo vía webhook de HU-007/008; sin URL → `skipped` y el sistema opera igual; sin variables nuevas; WhatsApp fuera de alcance (Spec 009) (TC-010-003/016, demo pasos a–d).
- [x] RF-4: sin duplicados ante reprocesos/cancelación repetida (transición condicional + `UNIQUE(event_id)`) (TC-010-006/010, demo paso c).
- [x] RNF-1: payload con PII mínima (`recipient` + `message`); sin documento/teléfono (TC-010-002/010).
- [x] RNF-2: trazabilidad en `appointments.status` + `automation_events` (sin tabla nueva); migración con respaldo `.bak-<timestamp>` y aborto ante duplicados (TC-010-014, `automation_events_dump.json`).
- [x] RNF-3: claridad (asunto/cabecera/estado «Cancelada»; literales contractuales espejados) (TC-010-002/016).
- [x] CL-1 (cita ya cancelada) / CL-4 (cancelación repetida): sin cambio y sin notificación (TC-010-006, demo paso c).
- [x] CL-2 (fallo de canal): `failed` con motivo en español; la cancelación permanece confirmada (TC-010-004/005/009, demo paso d).
- [x] CL-3 (datos de contacto incompletos): `failed` sin POST (TC-010-007/008).
- [x] Q4 (liberación del horario): disponibilidad sin `cancelled`, índice parcial, re-reserva posible y doble reserva activa intacta (TC-010-011/012/013/015, demo paso e).
- [x] Finalización: tests en verde (204/204) + demo manual con receptor local.

## Veredicto

**PASS** (18/18 TC; suite 204/204; demo manual completa con receptor stdlib).

- [ ] **Aceptación de la HU** por la usuaria (pendiente: T15).
- [ ] Commits por fase + Push (T14, requiere aprobación explícita).
