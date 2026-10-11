# QA HU-008 — Enviar confirmación por correo electrónico (vía n8n)

> HU: HU-008 · Spec 008 (enmendada 2026-10-10) · Rama: `feature/hu-008`
> Commits de implementación: `7a3d9df` (spec+plan+task), `e2040fa`
> (contenido+espejo), `da18850` (servicio+disparo), `62f06cd` (tests+D15)
> Fecha: 2026-10-10 · Suite: `python -m pytest -q` → **163 passed / 0 FAIL**
> (147 previos intactos — TC-007-002/007 adaptados por D15 sin relajar
> garantías — + 16 nuevos TC-008-001…016; TC-008-017 es la corrida de suite).

## Resumen

- Total TC de la HU: **17** (16 funciones + corrida de suite)
- PASS: **17** · FAIL: **0** · BLOCKED: **0**
- Regresión: **147/147 previos intactos** (HU-001/002/003/016/004/005/006/007)

## Casos de prueba

| Caso | Comando | Resultado | Observación |
|------|---------|-----------|-------------|
| TC-008-001 | `python -m pytest tests/test_email_service.py -v` | PASS | subject/text/html con servicio, fecha legible, hora, «Pendiente» y `#{id}`; HTML ⊆ 6 hex de paleta, sin `<img>`/CSS remoto; sin documento/teléfono |
| TC-008-002 | ídem | PASS | 2xx → evento `sent` con `sent_at` + 1 POST del tipo con `recipient`/`message` completos |
| TC-008-003 | ídem | PASS | URL vacía → `skipped` «Envío de correo no configurado.», 0 POST, reserva `pending` |
| TC-008-004 | ídem | PASS | `URLError` → `failed` «Servicio de automatización no disponible.», 0 excepción, cita intacta |
| TC-008-005 | ídem | PASS | `TimeoutError` → `failed` «Tiempo de espera agotado (timeout).», cita intacta |
| TC-008-006 | ídem | PASS | Reproceso → 1 evento (`UNIQUE event_id`) y 1 POST acumulado del tipo |
| TC-008-007 | ídem | PASS | Repositorio caído (`RuntimeError`) → `create_booking()` devuelve la `Appointment` |
| TC-008-008 | ídem | PASS | Datos incompletos → 0 POST y `failed` «Datos de la cita incompletos.» |
| TC-008-009 | ídem | PASS | Email vacío/sin `@` → 0 POST y `failed` «Dirección de correo del paciente ausente o no válida.» (3 casos) |
| TC-008-010 | ídem | PASS | Allowlist: `event_id` determinista, `recipient`/`message`; sin `document_*`/`phone` |
| TC-008-011 | `python -m pytest tests/test_hu_008.py -v` | PASS | 2 filas por reserva (`confirmed` + `confirmation_email`), `COUNT(*)=1` por `event_id`, 1 POST por tipo tras reproceso |
| TC-008-012 | ídem | PASS | Sin `SMTP_*`; defaults de HU-007 intactos (URL vacía, 3.0, auth `""`) |
| TC-008-013 | ídem | PASS | Espejo `expected_content` == `email_content`; `STATUS_PENDING_LABEL` = «Pendiente» |
| TC-008-014 | ídem | PASS | Constitución #1: sin `smtplib` ni terceros (AST sobre imports); usa `automation_service._post_webhook` |
| TC-008-015 | ídem | PASS | HTTP end-to-end: 303 → `/citas/confirmada/<id>` 200 + evento `confirmation_email` `sent` |
| TC-008-016 | ídem | PASS | Regresión HU-004/005/006/007; `appointment.confirmed` sin PII; email inválido → 200 + 0 eventos de correo nuevos |
| TC-008-017 | `python -m pytest -q` | PASS | **163 passed / 0 FAIL** (corrida de suite, no una función) |

## Demo manual (plan §6.2)

Receptor stdlib local (puerto 8765) capturando JSON sobre el webhook y app de
demo con `AUTOMATION_WEBHOOK_URL` apuntando a él. Evidencia en
`docs/evidencias/hu-008/`:

| Paso | Escenario | Resultado | Evidencia |
|------|-----------|-----------|-----------|
| a | Receptor arriba: POST `/citas` | **303** → `/citas/confirmada/<id>` **200** | `demo-step1.json` |
| b | Receptor captura **2 POST**: `appointment.confirmed` y `appointment.confirmation_email` (con subject/text/html de §2.2) | **OK** | `webhook_payloads.jsonl`, `demo-step1.json` |
| c | Ambos eventos `sent` con `sent_at` | **OK** | `demo-step2.json`, `automation_events_dump.json` |
| d | Receptor apagado: nueva POST `/citas` | **303** (reserva intacta) + ambos eventos `failed` con motivo en español | `demo-step3-receptor-caido.json` |
| e | Reproceso de la misma reserva | **0 POST añadidos** (`UNIQUE(event_id)`) | `demo-step4-reproceso.json` |

## Defectos encontrados

- Ninguno.

## Regresión

- HU-004 (agendamiento): intacta (validación 200, 303/200).
- HU-005 (disponibilidad): intacta (`/citas/horarios`, `/citas/disponibilidad`).
- HU-006 (doble reserva): intacta (`UNIQUE` + `SLOT_TAKEN`).
- HU-007 (automatización): intacta; TC-007-002/007 adaptados por **D15**
  (filtro por `event_type`, sin relajar aserciones: 1 POST `confirmed` +
  dedup).
- Suite completa: **163/163**.

## Criterios de aceptación (spec 008)

- [x] RF-1: cita registrada correctamente → confirmación por correo (evento a n8n) (TC-008-002/003/015, demo pasos a–c).
- [x] RF-2: la confirmación incluye fecha, hora, servicio y estado (TC-008-001/013).
- [x] RF-3: sin registro correcto → sin confirmación que represente la reserva como válida (TC-008-004/007/008/009/016, demo paso d).
- [x] RF-4: la confirmación se asocia a la cita que originó el envío (TC-008-002/006/011, demo paso e).
- [x] RNF-1: protección de datos personales (payload sin documento/teléfono; auth header de HU-007) (TC-008-001/010/014).
- [x] RNF-2: entrega clara y legible (asunto + multipart con fecha en español) (TC-008-001).
- [x] CL-1: correo inválido/ausente → sin envío (TC-008-009/016).
- [x] CL-2: error de envío → `failed`, nunca propaga (TC-008-004/005, demo paso d).
- [x] CL-3: envío duplicado → 1 evento y 1 POST (TC-008-006/011, demo paso e).
- [x] CL-4: datos incompletos → `failed` (TC-008-008).
- [x] Finalización: tests en verde (163/163) + demo manual.

## Veredicto

**PASS** (17/17 TC; suite 163/163; demo manual completa).

- [x] **Aceptación de la HU** por la usuaria: **aceptada el 2026-10-11**
  (prueba live E2E: correo recibido en su bandeja).

## Live E2E contra n8n (2026-10-11)

Workflow de la usuaria ampliado con **Google Calendar** además del nodo de
correo; URL de producción `webhook/hu-007-cita-creada` (workflow **Active**) y
cabecera `x-hu007-token` (token solo en entorno de la prueba, nunca en el repo).

| Intento | Escenario | Resultado |
|---|---|---|
| 1 | URL producción sin activar (404) | Reserva **44** intacta; ambos eventos `failed` «Servicio de automatización no disponible.» (best-effort OK) |
| 2 | `webhook-test` en modo Listen (1 sola escucha) | Reserva **45** intacta; `appointment.confirmed` **`sent`**, `confirmation_email` `failed` (segundo POST tras cerrarse la escucha) |
| 3 | Workflow **Active** (producción) | Reserva **46** (2026-10-12 15:00, `jazluz@gmail.com`) → 303; **ambos eventos `sent`** (`17:35:49` / `17:35:50`); **correo recibido por la usuaria** («Sí, llegó») |

Estado de la cita: `pending` («Pendiente») **por diseño** (spec 004: la cita
nace pendiente; ninguna HU aceptada transiciona el estado todavía; la
cancelación queda para Spec 010).
