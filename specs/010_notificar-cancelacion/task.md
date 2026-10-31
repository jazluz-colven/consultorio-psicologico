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

- [x] **T6 — Persistencia: SCHEMA/migración + `update_appointment_status()` + disponibilidad sin `cancelled` (plan §8.5, §2.1, D4/D5)** `[RF-1][RF-4][RNF-2]`
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

- [x] **T8 — Servicio: `send_cancellation()` en `email_service.py` (plan §8.6, §3, D2/D7/D10/D14)** `[RF-1][RF-2][RF-3][RF-4][CL-1][CL-2][CL-3][RNF-1]`
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

- [x] **T9 — Disparo: `cancel_appointment()` en `appointment_service.py` (plan §8.7, §3, D1/D6/D7)** `[RF-1][RF-3][RF-4][CL-1]`
  `APPOINTMENT_NOT_FOUND`/`ALREADY_CANCELLED`, transición atómica
  `confirmed → cancelled` y, solo si cambió, `send_cancellation()`
  best-effort; `create_booking()` y `web/` sin cambios de firma ni contrato.
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/appointment_service.py').read_text(encoding='utf-8'); assert 'def cancel_appointment' in src and 'ALREADY_CANCELLED' in src and 'def create_booking(' in src"` → exit 0
  y `python -m pytest tests/test_appointment_routes.py tests/test_double_booking_routes.py -q` → **0 FAIL**.
  **Cumplido 2026-10-13 (fuente OK; rutas 14/14; suite 188/188).**

- [x] **T10 — Tests de servicio: TC-010-001..012 (plan §6.1, §8.6–8.7)** `[RF-1..RF-4][CL-1..CL-4][RNF-1][Q4]`
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

- [x] **T11 — Tests de HU: TC-010-013/015/016/017 (plan §6.1, §8.8)** `[RF-2][RF-3][RF-4][regresión]`
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

- [x] **T13 — Evidencia QA y demo manual (plan §6.2/§6.3)** `[RF-1][RF-2][RF-3][RF-4][CL-2][Q4][finalización]`
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

- [x] **T15 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `qa-hu-010.md` está marcado con
  fecha y la §7.2 del plan queda íntegramente en `[x]`.
  **Cumplido 2026-10-13** (aceptación registrada en `qa-hu-010.md`).

---

## Fase 2 — Tareas RF-8..RF-15: evento de negocio `appointment.cancelled` y reproceso

> **Estado: APROBADA por la usuaria el 2026-10-23.** La usuaria aprobó la
> enmienda 2 de la spec 010 el 2026-10-23; `plan.md` §9 fue reescrito contra
> ese texto (F2-D1..F2-D13) y **reaprobado por la usuaria el 2026-10-23**
> («Apruebo»), junto con estas tareas T21–T27 y con la **división de la fase
> en 2A (T21–T25) y 2B (T26–T27)** («Divide la fase»). Trazabilidad:
> HU-010 (enmienda 2, aprobada 2026-10-23) → Spec 010 RF-8..RF-15 → `plan.md`
> §9 (reescrito y reaprobado 2026-10-23) → estas tareas → código → tests
> TC-010-101..119 → evidencia `qa-hu-010-rf8-10.md` → commit.
> Las tareas T1–T20 anteriores quedan **cerradas y sin reabrir**. Cada tarea
> dura **20–30 min**, se ejecuta **en orden** y su `Hecho cuando:` es
> verificable con un comando o una comprobación concreta. **Sin marcar una
> tarea no se empieza la siguiente.** La fase 2B solo se inicia cuando la
> 2A (T21–T25) esté cerrada.
> Baselines: `main` **204 PASS / 0 FAIL**; rama `feature/hu-010-rf8-10`
> **210 PASS / 0 FAIL** (tras T18–T20).

> **Criterio de redefinición de IDs (decisión del planificador, ratificada
> por la usuaria el 2026-10-23 al aprobar las tareas T21–T27)**: T21–T25 **nunca se ejecutaron** (quedaron en pausa) y
> estaban redactadas contra el texto anterior de la spec → **se redefinen en
> su lugar** contra el plan nuevo, incluyendo la corrección del diseño de
> T19/T20 (la corrección NO reabre T19/T20: esas tareas permanecen `[x]`;
> el trabajo corrector se ejecuta como T22–T24, con IDs y objetivos nuevos).
> T26–T27 son tareas nuevas (concurrencia/suite, evidencia y cierre)
> heredadas del alcance previo. **Aviso AGENTS.md**: la fase 2 suma **12
> tareas (T16–T27)**, más de 10 → se propuso dividir la fase en **2A
> (T21–T25: reaprobación, motor transaccional y reproceso)** y **2B
> (T26–T27: validación y cierre)**; la usuaria **aprobó la división el
> 2026-10-23** («Divide la fase»).

- [x] **T16 — Aprobación del plan §9 (F2-D1..F2-D10) y de estas tareas, en su versión previa (usuaria)** `[trazabilidad]`
  La usuaria aprobó el alcance de la fase 2 según el plan previo: orden de
  emisión (F2-D1), mecanismo en `automation_service` (F2-D2), limitación de
  reproceso (F2-D3, hoy superada), riesgo para 018/017 (F2-D4), sin env vars
  ni esquema nuevos (F2-D5/D6), rama (F2-D7), numeración TC-010-101+
  (F2-D8/D9) y literales reutilizados (F2-D10).
  Hecho cuando: `plan.md` §9.10 tenía marcada la aprobación con fecha.
  **Cumplido 2026-10-23. Queda superada por la reaprobación del §9 reescrito
  (ver encabezado de esta fase y T21).**

- [x] **T17 — Git: rama `feature/hu-010-rf8-10` desde `main` + commit de plan/task (plan §9.9, F2-D7)** `[base][regresión]`
  Crear la rama desde `main` (limpia, 204 PASS); commitear el `plan.md` y el
  `task.md` ampliados; verificar el baseline antes de tocar código.
  Hecho cuando: `git branch --show-current` → `feature/hu-010-rf8-10`,
  `git merge-base --is-ancestor main feature/hu-010-rf8-10` → exit 0,
  `git status` limpio y `python -m pytest -q` → **204 PASS / 0 FAIL**.
  **Cumplido 2026-10-23** (rama creada, commit `5fad34b`, baseline
  verificado). La rama se conserva para la fase corregida; el commit del
  plan/task reescritos se hace al reanudar (T21).

- [x] **T18 — Constantes: `CANCELLED_EVENT_TYPE`/`_VERSION` en `automation_content.py` (plan §9.3, RF-8/RF-9)** `[RF-8][RF-9]`
  Añadir `CANCELLED_EVENT_TYPE = "appointment.cancelled"` y
  `CANCELLED_EVENT_VERSION = 1` junto a los de HU-007, sin tocar
  `EVENT_TYPE`/`EVENT_VERSION` ni los `DETAIL_*`; sin lógica.
  Hecho cuando: `python -c "from consultorio.content.automation_content import CANCELLED_EVENT_TYPE as t, CANCELLED_EVENT_VERSION as v, EVENT_TYPE; assert t == 'appointment.cancelled' and v == 1 and EVENT_TYPE == 'appointment.confirmed'"` → exit 0
  y `python -m pytest -q` → **0 FAIL** (204).
  **Cumplido 2026-10-23. Sin afectar por la enmienda 2** (las constantes no
  cambian; RF-8/RF-9 siguen iguales).

- [x] **T19 — Servicio: `_build_automation_event()` + `build_cancelled_event()` + `on_appointment_cancelled()` en `automation_service.py` (plan §9.3/§9.6 previo, F2-D2/D10)** `[RF-8][RF-9][RF-10]`
  Helper privado con el allowlist único; `build_event()` delega **sin cambiar
  su firma pública**; `on_appointment_cancelled()` espejo de
  `on_appointment_confirmed` (dedup por `UNIQUE(event_id)` → URL vacía
  `skipped` «Automatización no configurada.» → `_post_webhook` →
  `sent`/`failed` con los `DETAIL_*` reutilizados; **nunca propaga**).
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/automation_service.py').read_text(encoding='utf-8'); assert 'def on_appointment_cancelled' in src and 'def build_cancelled_event' in src and 'def _build_automation_event' in src"` → exit 0
  y `python -m pytest tests/test_automation_service.py tests/test_hu_007.py tests/test_hu_008.py -q` → **0 FAIL** (HU-007/008 intactas).
  **Cumplido 2026-10-23. Parcialmente afectada por la enmienda 2 (no se
  reabre)**: `_build_automation_event()`/`build_cancelled_event()` son
  conformes (RF-9 intacto); `on_appointment_cancelled()` registra
  **post-commit** con `insert_event` en conexión separada, incompatible con
  RF-11/RF-12 → la corrección es trabajo nuevo en T22 (la función se
  sustituye por `publish_cancelled_event()`, solo publicación).

- [x] **T20 — Disparo: `cancel_appointment()` emite el evento de negocio antes que el correo (plan §9.6 previo, F2-D1)** `[RF-8]`
  En `appointment_service.cancel_appointment()`, tras la transición
  confirmada, llamar `automation_service.on_appointment_cancelled(...)` y
  después `email_service.send_cancellation(...)` (ambas best-effort, firma
  intacta; sin cambios en `create_booking()` ni en `web/`).
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/appointment_service.py').read_text(encoding='utf-8'); body = src.split('def cancel_appointment', 1)[1]; assert body.index('on_appointment_cancelled') < body.index('send_cancellation')"` → exit 0
  y `python -m pytest -q` → **0 FAIL** (los TC-010 cerrados filtran por
  `event_id`/`event_type` y no se rompen).
  **Cumplido 2026-10-23** (verificación fuente OK; suite **210 PASS / 0
  FAIL**: 204 previos intactos + TC-010-101/102/103/104/108/109 creados en
  T19/T20). **Parcialmente afectada por la enmienda 2 (no se reabre)**: el
  **orden** F2-D1 (negocio → correo) sigue vigente y verificado, pero el
  registro del evento debe pasar a la transacción de la cancelación →
  corrección en T22.

### Fase 2A — T21–T25: reaprobación, motor transaccional y reproceso (**APROBADA por la usuaria el 2026-10-23**)

- [x] **T21 — Reaprobación del plan §9 reescrito (F2-D1..F2-D13) y de las tareas T21–T27 (usuaria)** `[trazabilidad]`
  **Bloqueante: no se toca código antes.** La usuaria revisa y aprueba el §9
  alineado con la enmienda 2: corrección de F2-D3 (vía de reproceso =
  `reprocess_automation_event()`), F2-D11 (atomicidad transaccional +
  limitación del `pending` huérfano explícita), F2-D12 (exclusión de
  concurrencia por transición condicionada), F2-D13 (`expected_content.py`
  sin cambios; límite al evento `appointment.cancelled`), matriz RF-8..RF-15 →
  CA-1..CA-8 y tests TC-010-101..119; y decide sobre la división 2A/2B
  señalada en este encabezado.
  Hecho cuando: `plan.md` §9.10 tiene marcada la reaprobación con fecha, el
  encabezado de §9 deja de decir «PENDIENTE DE REAPROBACIÓN» y este
  encabezado de fase queda aprobado (con la decisión sobre la división, si
  procede).
  **Cumplido 2026-10-23** («Apruebo» el plan §9 reescrito y el conjunto de
  tareas T21–T27; «Divide la fase»: 2A = T21–T25, 2B = T26–T27).

- [x] **T22 — Corrección transaccional: `update_appointment_status_with_pending_event()` + `publish_cancelled_event()` (plan §9.3/§9.6, F2-D11)** `[RF-8][RF-10][RF-11][RF-12]`
  En `appointments_repository`: operación transaccional que hace el `UPDATE
  … AND status='confirmed'` y el `INSERT` del evento `pending` en **la misma
  conexión**; `rowcount = 0` → rollback y `None`; fallo del INSERT → rollback
  y el error propaga (la cita **no** queda Cancelada). En
  `automation_service`: sustituir `on_appointment_cancelled()` por
  `publish_cancelled_event()` (solo publicación post-commit: URL vacía →
  `skipped`; POST → `sent`/`failed`; nunca propaga). En
  `cancel_appointment()`: usar la operación transaccional y, tras el commit,
  publicar negocio antes que correo (F2-D1 intacto); firmas públicas y
  `create_booking()`/`web/` sin cambios.
  Hecho cuando: `python -c "import pathlib; r = pathlib.Path('consultorio/persistence/appointments_repository.py').read_text(encoding='utf-8'); a = pathlib.Path('consultorio/services/appointment_service.py').read_text(encoding='utf-8'); s = pathlib.Path('consultorio/services/automation_service.py').read_text(encoding='utf-8'); assert 'update_appointment_status_with_pending_event' in r and 'update_appointment_status_with_pending_event' in a and 'publish_cancelled_event' in s and 'def on_appointment_cancelled' not in s"` → exit 0
  y `python -m pytest tests/test_cancellation_service.py -q` → los
  **TC-010-101/102/103/104/108/109 siguen verdes sin enmiendas** y
  `python -m pytest -q` → **0 FAIL**.
  **Cumplido 2026-10-24 (suite completa 211 PASS / 0 FAIL).**

- [x] **T23 — Tests de atomicidad: TC-010-110 (redefinido) y TC-010-112 (plan §9.8.1)** `[RF-11][RF-12]`
  TC-010-110 **redefinido**: parchear el punto de inserción del evento dentro
  de la transacción con `RuntimeError` → `cancel_appointment()` propaga el
  error, la cita **sigue `confirmed`**, 0 filas del evento y 0 POST (RF-12,
  CA-5). TC-010-112: `side_effect` de `_post_webhook` que verifica en el
  momento del POST que la cita es `cancelled` y el evento está `pending`,
  después 200 → `sent` (RF-11, CA-5).
  Hecho cuando: `python -m pytest tests/test_cancellation_service.py -k "tc_010_110 or tc_010_112" -v` → **2 PASS / 0 FAIL**
  y `python -m pytest -q` → **0 FAIL**.
  **Cumplido 2026-10-25 (cierre de la 2A): 2 PASS / 0 FAIL y suite completa
  278 PASS / 0 FAIL.** El script temporal `tests/test_t22_quickcheck.py` se
  eliminó al quedar cubierta su comprobación por los TC oficiales.

- [x] **T24 — Reproceso: `claim_failed_event()` + `reprocess_automation_event()` (plan §9.3/§9.6/§9.7, F2-D3/D12)** `[RF-13][RF-14][RF-15]`
      En `automation_events_repository`: `claim_failed_event(event_id, …)` —
      `UPDATE … SET status='pending', detail=NULL WHERE event_id=? AND
      status='failed' AND event_type='appointment.cancelled'`, devolviendo
      `True` solo si `rowcount = 1`. En `automation_service`:
      `reprocess_automation_event(event_id, …)`: admisión atómica → recuperar
      registro y cita → reconstruir payload con el mismo `event_id` → URL vacía
      `skipped` / POST → `sent`/`failed` con los `DETAIL_*`; no admitido → no-op
      sin POST ni modificación; nunca propaga.
      Hecho cuando: `python -c "import pathlib; r = pathlib.Path('consultorio/persistence/automation_events_repository.py').read_text(encoding='utf-8'); s = pathlib.Path('consultorio/services/automation_service.py').read_text(encoding='utf-8'); assert 'def claim_failed_event' in r and 'def reprocess_automation_event' in s"` → exit 0
      y `python -m pytest -q` → **0 FAIL**.
      **Cumplido 2026-10-24 (suite completa 211 PASS / 0 FAIL).**


- [x] **T25 — Tests de reproceso y fallo de publicación: TC-010-105/106/107/111/113/114/115/116/118 (plan §9.8.1)** `[RF-10][RF-13][RF-14][regresión]`
  Fallo de publicación (aislamiento RF-10 parcheando solo `_post_webhook`):
  URLError (105), TimeoutError (106), HTTP 500 (107); regresión/constitución
  + `expected_content.py` sin cambios (111). Reproceso: `failed` → 1 POST,
  misma fila/`event_id`, `sent` (113); URL vacía en reproceso → `skipped`
  (114); reproceso que vuelve a fallar → `failed` con detalle (115); no-op
  sobre `sent`/`skipped`/`pending` (116); ámbito solo
  `appointment.cancelled` (118).
  Hecho cuando: `python -m pytest tests/test_cancellation_service.py -k "tc_010_105 or tc_010_106 or tc_010_107 or tc_010_111 or tc_010_113 or tc_010_114 or tc_010_115 or tc_010_116 or tc_010_118" -v` → **9 PASS / 0 FAIL**.
  **Cumplido 2026-10-24 (9/9; suite completa 221/221).**

### Fase 2B — T26–T27: validación y cierre (**APROBADA por la usuaria el 2026-10-23; pendiente del cierre de la 2A**)

> La fase 2B solo se inicia cuando la 2A (T21–T25) esté cerrada: T26
> requiere los tests de T23/T25 implementados (TC-010-110/112 y
> 105/106/107/111/113–116/118) y T27 requiere los **222 PASS** de T26.

- [x] **T26 — Concurrencia y suite completa: TC-010-117 y TC-010-119 (plan §9.8.1)** `[RF-15][todos]`
  TC-010-117: re-entrancia determinista — el `side_effect` del
  `_post_webhook` del primer reproceso invoca un segundo
  `reprocess_automation_event()` sobre el mismo `event_id` → el segundo es
  no-op, total 1 POST y un único cambio de estado (CA-8). Después, corrida
  completa sin tocar ni relajar tests previos (204 + 6 de T19/T20 + 12 nuevos).
  Hecho cuando: `python -m pytest tests/test_cancellation_service.py -k tc_010_117 -v` → **1 PASS / 0 FAIL**
  y `python -m pytest -q` → **222 PASS / 0 FAIL**.
  **Cumplido 2026-10-24 (2 PASS en test_cancellation_service.py; suite completa 223/223).**

- [x] **T27 — Evidencia QA, demo del reproceso y cierre (plan §9.8.2/§9.9)** `[RF-8..RF-15][finalización][trazabilidad]`
  Servidor + **receptor local stdlib** y
  `cancel_appointment()`/`reprocess_automation_event()` desde un
  REPL/script: (a) cancelar → **2 POST** (`appointment.cancelled` +
  `appointment.cancellation_email`), ambos `sent`; (b) URL vacía → ambos
  `skipped`, 0 POST; (c) receptor apagado → ambos `failed` con motivo y cita
  `cancelled` intacta; (d) `cancel_appointment()` repetida →
  `already_cancelled` y 0 POST nuevos; (e) **`reprocess_automation_event()`
  sobre el evento `failed` con el receptor encendido → 1 POST nuevo, misma
  fila, `sent`**; (f) fila `appointment.cancelled:{id}:v1` verificada en
  `automation_events`. Sin cambios visuales → sin capturas 1280/375. Informe
  `docs/evidencias/hu-010/qa-hu-010-rf8-10.md` con PASS/FAIL por TC,
  checkboxes de aceptación y trazabilidad **RF-8..RF-15 / CA-1..CA-8** (skill
  `pytest-qa`); no se toca `qa-hu-010.md`. Cierre: commits por fase
  citando HU-010 fase 2 / Spec 010 RF-8..RF-15, push sincronizado,
  `MEMORY.md` (evento emitido, motor transaccional, reproceso sobre
  `failed`, limitación del `pending` huérfano) y registro del pendiente
  F2-D4 (plan 018).
  Hecho cuando: existe `qa-hu-010-rf8-10.md` con veredicto **PASS** (suite
  222/222), la evidencia en `docs/evidencias/hu-010/`, el servidor en marcha
  con la URL comunicada, `git status` limpio, `git rev-parse HEAD` =
  `git rev-parse origin/feature/hu-010-rf8-10` y `MEMORY.md` refleja la
  fase 2.
