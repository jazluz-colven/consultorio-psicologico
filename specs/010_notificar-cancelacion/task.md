# Tareas HU-010 — Notificar la cancelación de una cita

> Trazabilidad: HU-010 → Spec 010 (pendiente de enmienda, plan D16) → `plan.md`
> (aprobado 2026-10-13) → **este task.md** → código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su
> `Hecho cuando:` es verificable con un comando o una observación concreta. Sin
> marcar una tarea, no se empieza la siguiente. RF indicados por tarea (matriz
> completa en `plan.md` §0). Baseline previo: **187 PASS / 0 FAIL**.

## Tareas

- [x] **T1 — Aprobación del plan y de las decisiones Q1–Q6 (plan §7.1)** `[trazabilidad]`
  La usuaria aprueba el plan: Q1 (trigger servicio mínimo sin UI), Q2 (solo
  correo; WhatsApp pendiente Spec 009), Q3 (literales §2.2), Q4 (liberar el
  horario + índice parcial), Q5 (rama `feature/hu-010`), Q6 (reutiliza
  HU-007/008) y D16 (enmienda de la spec previa).
  Hecho cuando: las filas Q1–Q6 de `plan.md` §7.1 están fechadas y §7.2 tiene
  marcada la aprobación. **Cumplido 2026-10-13.**

- [x] **T2 — Spec 010: enmienda con trigger, canales, contenido y liberación (plan §8.1, D16)** `[RF-1][RF-2][RF-3][RF-4][RNF-1][RNF-2][RNF-3]`
  Petición explícita de la usuaria: cerrar las dos dudas
  `[NECESITA ACLARACIÓN]` con Q2/Q3, fijar la transición `confirmed → cancelled`
  sin UI (Q1), «cuando corresponda» = canal implementado y configurado con
  WhatsApp pendiente de Spec 009, el contenido literal del aviso (§2.2) y la
  liberación del horario con su migración a índice único parcial (Q4).
  Hecho cuando: `specs/010_notificar-cancelacion/spec.md` contiene
  «[RESUELTA]» en sus dos dudas, fija «confirmed → cancelled», «índice único
  parcial» y el asunto «Cita cancelada», y `python -m pytest -q` sigue en
  **187 PASS / 0 FAIL**. **Cumplido 2026-10-13** (suite 187/187 verificada).

- [x] **T3 — Git: rama `feature/hu-010` desde `main` + commit de spec/plan/task (plan §8.0, Q5/D12)** `[base][regresión]`
  Crear la rama desde `main` (limpia, 187 PASS); commitear `spec.md`,
  `plan.md` y `task.md`; verificar el baseline antes de tocar código.
  Hecho cuando: `git branch --show-current` → `feature/hu-010`,
  `git merge-base --is-ancestor main feature/hu-010` → exit 0, `git status`
  limpio y `python -m pytest -q` → **187 PASS / 0 FAIL**.
  **Cumplido 2026-10-13 (commit `9b6a850`, suite 187/187).**

- [x] **T4 — Espejo: literales de cancelación en `tests/expected_content.py` (plan §8.3, D3)** `[RF-2]`
  Añadir `CANCELLATION_EMAIL_SUBJECT_TEMPLATE`,
  `CANCELLATION_EMAIL_BODY_HEADER`, `CANCELLATION_EMAIL_FOOTER`,
  `DETAIL_CANCELLATION_NOT_CONFIGURED`, `STATUS_CANCELLED` y
  `STATUS_CANCELLED_LABEL`; sin lógica.
  Hecho cuando: `python -c "import tests.expected_content as e; assert e.CANCELLATION_EMAIL_SUBJECT_TEMPLATE.startswith('Cita cancelada') and e.STATUS_CANCELLED_LABEL == 'Cancelada' and e.DETAIL_CANCELLATION_NOT_CONFIGURED"` → exit 0.
  **Cumplido 2026-10-13 (commit de docs `9b6a850` + espejo).**

- [x] **T5 — Contenido: `appointment_content.py` + `email_content.py` (plan §8.4, §2.2, D3/D13)** `[RF-1][RF-2][RNF-3]`
  `STATUS_CANCELLED='cancelled'`, `STATUS_CANCELLED_LABEL='Cancelada'`;
  y en `email_content` el asunto, cabecera, pie de reagendado y motivo
  `DETAIL_CANCELLATION_NOT_CONFIGURED` (reutilizando `EMAIL_HTML_TEMPLATE`,
  etiquetas y fechas legibles de HU-008); sin lógica ni BD. (`MSG_APPOINTMENT_NOT_FOUND`
  descartado: los sentinels de la operación viven en el servicio en inglés, D13.)
  Hecho cuando: `python -c "from consultorio.content.appointment_content import STATUS_CANCELLED as s, STATUS_CANCELLED_LABEL as l; from consultorio.content.email_content import CANCELLATION_EMAIL_SUBJECT_TEMPLATE as t; import tests.expected_content as e; assert s == 'cancelled' and l == 'Cancelada' and 'Cita cancelada' in t and t == e.CANCELLATION_EMAIL_SUBJECT_TEMPLATE"` → exit 0.
  **Cumplido 2026-10-13 (suite 187/187).**

- [ ] **T6 — Persistencia: SCHEMA/migración + `update_appointment_status()` + disponibilidad sin `cancelled` (plan §8.5, §2.1, D4/D5)** `[RF-1][RF-4][RNF-2]`
  `appointments` sin `UNIQUE` inline + índice parcial
  `ux_appointments_slot_open … WHERE status <> 'cancelled'`; migración
  idempotente con respaldo `.bak-<timestamp>` y aborto si hay duplicados entre
  no-canceladas; `update_appointment_status()` (UPDATE condicional);
  `is_slot_taken`/`list_booked_times*` excluyen `cancelled`. `web/` intacto.
  Hecho cuando: `python -c "import inspect; from consultorio.persistence import appointments_repository as r, database as d; src = inspect.getsource(r); assert \"status <> 'cancelled'\" in src and 'ux_appointments_slot_open' in inspect.getsource(d) and 'bak-' in inspect.getsource(d)"` → exit 0
  y `python -m pytest tests/test_appointment_persistence.py tests/test_availability_service.py tests/test_double_booking_service.py -q` → **0 FAIL** (los tests de HU-004/005/006 siguen verdes con el índice parcial).
  **Cumplido 2026-10-13 (verificado con los 5 ficheros de regresión de
  reservas, 30/30; suite completa 187/187). Adaptación spec-backed de dos
  aserciones de esquema ajenas a esta HU que asertaban el `UNIQUE` inline
  eliminado por la enmienda de la spec 010: TC-004-004
  (`test_appointment_persistence.py`) y TC-006-013 (`test_hu_006.py`) → ahora
  verifican `UNIQUE` ausente de la tabla + índice parcial con
  `status <> 'cancelled'`.**

- [x] **T7 — Tests de migración: TC-010-014 (plan §6.1, §8.5)** `[RF-4][RNF-2]`
  `test_hu_010.py`: BD con SCHEMA antiguo creada a mano → `init_db()` migra
  (índice parcial presente, datos conservados, backup creado), segunda
  ejecución sin cambios (idempotente) y aborto con duplicados entre
  no-canceladas.
  Hecho cuando: `python -m pytest tests/test_hu_010.py -v` → **1 PASS / 0 FAIL**
  (suite **188**).
  **Cumplido 2026-10-13 (1 PASS; suite completa 188/188).**

- [ ] **T8 — Servicio: `send_cancellation()` en `email_service.py` (plan §8.6, §3, D2/D7/D10/D14)** `[RF-1][RF-2][RF-3][RF-4][CL-1][CL-2][CL-3][RNF-1]`
  `CANCELLATION_EVENT_TYPE`/`EVENT_VERSION`, `build_cancellation_message()`
  («Cita cancelada», «Estado: Cancelada», fecha legible), `build_cancellation_event()`
  (allowlist `recipient`/`message`, `appointment.status='cancelled'`, sin
  documento/teléfono) y `send_cancellation()` espejo de `send_confirmation`
  (defensivos → dedup por `UNIQUE(event_id)` → URL vacía `skipped` →
  `_post_webhook` por referencia de módulo → `sent`/`failed`; **nunca
  propaga**).
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/email_service.py').read_text(encoding='utf-8'); assert 'appointment.cancellation_email' in src and 'automation_service._post_webhook' in src and 'document_number' not in src"` → exit 0
  y `python -m pytest -q` → **0 FAIL**.
  **Cumplido 2026-10-13 (verificación fuente OK; suite 188/188).**

- [ ] **T9 — Disparo: `cancel_appointment()` en `appointment_service.py` (plan §8.7, §3, D1/D6/D7)** `[RF-1][RF-3][RF-4][CL-1]`
  `APPOINTMENT_NOT_FOUND`/`ALREADY_CANCELLED`, transición atómica
  `confirmed → cancelled` y, solo si cambió, `send_cancellation()`
  best-effort; `create_booking()` y `web/` sin cambios de firma ni contrato.
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/appointment_service.py').read_text(encoding='utf-8'); assert 'def cancel_appointment' in src and 'ALREADY_CANCELLED' in src and 'def create_booking(' in src"` → exit 0
  y `python -m pytest tests/test_appointment_routes.py tests/test_double_booking_routes.py -q` → **0 FAIL**.
  **Cumplido 2026-10-13 (fuente OK; rutas 14/14; suite 188/188).**

- [ ] **T10 — Tests de servicio: TC-010-001..012 (plan §6.1, §8.6–8.7)** `[RF-1..RF-4][CL-1..CL-4][RNF-1][Q4]`
  `test_cancellation_service.py` con `_post_webhook` parcheado: envío 2xx →
  `sent` + 1 POST; mensaje (paleta, sin remotos, sin PII extra); URL vacía →
  `skipped` 0 POST; `URLError`/`TimeoutError` → `failed` + cita intacta;
  reproceso → `ALREADY_CANCELLED`, 1 evento y 1 POST; email inválido y datos
  incompletos → `failed` sin POST; aislamiento; allowlist del payload;
  liberación del horario (TC-011) y regresión HU-006 slot confirmado →
  `SLOT_TAKEN` (TC-012).
  Hecho cuando: `python -m pytest tests/test_cancellation_service.py -v` → **12 PASS / 0 FAIL**
  (suite **200**). Nota: TC-011 se escribe aquí, no en T7, porque requiere
  `cancel_appointment()` (plan §6.1 manda sobre §8.5).
  **Cumplido 2026-10-13 (12/12; suite 200/200).**

- [ ] **T11 — Tests de HU: TC-010-013/015/016/017 (plan §6.1, §8.8)** `[RF-2][RF-3][RF-4][regresión]`
  Re-reserva del slot cancelado → 303 + fila nueva (TC-013); HTTP
  `/citas/horarios` y `/citas/disponibilidad` reabren la hora tras cancelar
  (TC-015); espejo + sin variables de entorno nuevas (TC-016); regresión
  funcional HU-004/005/006/007/008/015/016/contraste + constitución #1
  (TC-017).
  Hecho cuando: `python -m pytest tests/test_hu_010.py -v` → **5 PASS / 0 FAIL**
  (suite **204**).
  **Cumplido 2026-10-13 (5/5 en el fichero; suite 204/204).**

- [x] **T12 — Regresión y suite completa (plan §6.1 TC-010-018, §6.2)** `[todos]`
  Ejecutar la suite completa sin tocar ni relajar tests previos.
  Hecho cuando: `python -m pytest -q` → **0 FAIL** con los **187 previos**
  intactos más los **17 nuevos** (**204 en total**).
  **Cumplido 2026-10-13 (204 passed / 0 failed).**

- [ ] **T13 — Evidencia QA y demo manual (plan §6.2/§6.3)** `[RF-1][RF-2][RF-3][RF-4][CL-2][Q4][finalización]`
  Servidor + **receptor local stdlib** (JSON sobre el webhook) y
  `cancel_appointment()` desde un REPL/script: (a) cancelar → `cancelled` y
  **1 POST** con subject/text/html de §2.2; (b) evento `sent`; (c) repetir →
  `already_cancelled` y **0 POST** nuevos; (d) receptor apagado → cancelación
  intacta + `failed` con motivo; (e) la hora vuelve a estar libre en
  `/citas/horarios` y se re-reserva en `/citas` (303). Demo live opcional con
  el webhook n8n de HU-007/008 (token solo en entorno). Sin cambios visuales →
  sin capturas 1280/375. Informe `docs/evidencias/hu-010/qa-hu-010.md` con
  PASS/FAIL por TC y checkbox de aceptación (skill `pytest-qa`).
  Hecho cuando: existe `qa-hu-010.md` con veredicto **PASS** (17 TC, suite
  204/204), la evidencia en `docs/evidencias/hu-010/` y el servidor en marcha
  con la URL comunicada.
  **Cumplido 2026-10-13** (`docs/evidencias/hu-010/qa-hu-010.md` PASS 18/18;
  demo pasos a–e con receptor stdlib local; servidor en
  http://127.0.0.1:5000).

- [x] **T14 — Commits por fase, Push y `MEMORY.md` (plan §8.11)** `[trazabilidad]`
  Commits por fase (spec+plan+task+espejo → contenido → persistencia+migración
  → servicio+disparo → tests → evidencia+MEMORY) citando HU-010/Spec 010;
  nunca claves, tokens ni PII en repo o memoria.
  Hecho cuando: `git status` limpio, `git rev-parse HEAD` =
  `git rev-parse origin/feature/hu-010` y `MEMORY.md` registra HU-010
  (estado `cancelled`, liberación de horario con índice parcial, evento
  `appointment.cancellation_email`, WhatsApp pendiente de Spec 009).
  **Cumplido 2026-10-13**: `6eac5c6` contenido, `8926931` persistencia,
  `d419d1e` servicio, `b2b31ee` tests, `9010825` evidencia; push con upstream
  (`origin/feature/hu-010`); MEMORY actualizada con el estado de HU-010.

- [ ] **T15 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `qa-hu-010.md` está marcado con
  fecha y la §7.2 del plan queda íntegramente en `[x]`.
