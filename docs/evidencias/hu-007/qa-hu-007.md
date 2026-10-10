# QA HU-007 — Automatización de reservas mediante n8n

> HU: HU-007 · Spec 007 (enmendada 2026-10-10) · Rama: `feature/hu-007`
> Commits de implementación: `d1a1bd5` (config+persistencia+contenido),
> `31367d0` (servicio+disparo+web), `138b547` (tests)
> Fecha: 2026-10-10 · Suite: `python -m pytest -q` → **146 passed / 0 FAIL**
> (134 previos intactos + 12 nuevos TC-007-001…012; TC-007-013 es la corrida de
> la suite).

## Resumen

- Total TC de la HU: **12**
- PASS: **12** · FAIL: **0** · BLOCKED: **0**
- Regresión: **134/134 previos intactos** (HU-001/002/003/016/004/005/006)

## Casos de prueba

| Caso | Comando | Resultado | Observación |
|------|---------|-----------|-------------|
| TC-007-001 | `python -m pytest tests/test_automation_service.py -v` | PASS | Payload con allowlist exacta; 0 campos de PII |
| TC-007-002 | ídem | PASS | 2xx → evento `sent` + exactamente 1 POST |
| TC-007-003 | ídem | PASS | URL vacía → `skipped` «Automatización no configurada.», 0 POST |
| TC-007-004 | ídem | PASS | `URLError` → `failed` «Servicio de automatización no disponible.», reserva intacta |
| TC-007-005 | ídem | PASS | `TimeoutError` → `failed` «Tiempo de espera agotado (timeout).» |
| TC-007-006 | ídem | PASS | HTTP 500 → `failed` «Respuesta no válida del servicio (HTTP 500).» |
| TC-007-007 | ídem | PASS | Reproceso → 1 evento (`UNIQUE event_id`) y 1 POST |
| TC-007-008 | ídem | PASS | Fallo del repositorio → `create_booking()` devuelve la cita (RF-7) |
| TC-007-009 | ídem | PASS | Timeout a nivel `urllib` → `failed`, sin bloquear la reserva |
| TC-007-010 | `python -m pytest tests/test_hu_007.py -v` | PASS | Esquema con `UNIQUE(event_id)`; dedup = 1 fila |
| TC-007-011 | ídem | PASS | Defaults `Config` (URL vacía, 3.0) + parse defensivo |
| TC-007-012 | ídem | PASS | Regresión funcional `/citas`, `/horarios`, `/disponibilidad`, `/confirmada`, doble reserva |
| TC-007-013 | `python -m pytest -q` | PASS | 146 passed / 0 FAIL (corrida de suite, no una función) |

## Demo manual (plan §6.2)

Servidor de demo en `http://127.0.0.1:5001` con `AUTOMATION_WEBHOOK_URL`
apuntando a un receptor stdlib local (puerto 8765). Evidencia en
`docs/evidencias/hu-007/`:

| Paso | Escenario | Resultado | Evidencia |
|------|-----------|-----------|-----------|
| a | Webhook arriba: POST `/citas` (cita 38, 2026-10-23 09:30) | **303** → `/citas/confirmada/38` | `demo-step1.json` |
| b | Receptor recibe 1 POST con el payload de plan §2.2 (sin PII) | **OK** | `webhook_payloads.jsonl`, `demo-step1.json` |
| c | Evento `appointment.confirmed:38:v1` con estado `sent` | **OK** (`sent_at` rellenado) | `automation_events_dump.json` |
| d | Webhook apagado: POST `/citas` (cita 40, 2026-10-23 11:30) | **303** y página de confirmación; evento `failed` «Servicio de automatización no disponible.»; cita `pending` intacta | `demo-step2.json` |
| e | Reproceso del evento de la cita 38 | **0 POST añadidos**, 1 sola fila en `automation_events` | `demo-step2.json` |

## Defectos encontrados

- Ninguno.

## Regresión

- HU-004 (agendamiento): intacta (303/200, `/citas/confirmada/<id>`).
- HU-005 (disponibilidad): intacta (`/citas/horarios`, `/citas/disponibilidad`).
- HU-006 (doble reserva): intacta (`UNIQUE` + `SLOT_TAKEN`; reintento → 200).
- Suite completa: **146/146**.

## Criterios de aceptación (spec 007)

- [x] RF-1: evento estructurado al confirmar la reserva.
- [x] RF-2: automatización no disponible → reserva válida (demo paso d).
- [x] RF-3: payload mínimo con `event_version` (TC-007-001, demo paso b).
- [x] RF-4: error/timeout/no-2xx → incidencia registrada sin invalidar (TC-007-004/005/006/009, demo paso d).
- [x] RF-5: reproceso → sin automatizaciones duplicadas (TC-007-007/010, demo paso e).
- [x] RF-6: evento válido → ejecución del webhook configurado (TC-007-002, demo pasos a–c).
- [x] RF-7: agendamiento/disponibilidad/doble reserva operativos en independencia (TC-007-008/012, regresión total).
- [x] Finalización: tests en verde + demo manual.

## Veredicto

**PASS** (12/12 TC; suite 146/146; demo manual completa).

- [x] **Aceptación de la HU** por la usuaria: **aceptada el 2026-10-10**.
