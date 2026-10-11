# Tareas HU-008 — Enviar confirmación por correo electrónico (vía n8n)

> Trazabilidad: HU-008 → Spec 008 (enmendada 2026-10-10) → `plan.md` (revisado,
> aprobado 2026-10-10) → **este task.md** → código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su
> `Hecho cuando:` es verificable con un comando o una observación concreta. Sin
> marcar una tarea, no se empieza la siguiente. RF indicados por tarea (matriz
> completa en `plan.md` §0). Baseline previo: **147 PASS / 0 FAIL**.

## Tareas

- [x] **T1 — Aprobación del plan revisado y de las decisiones Q1–Q7 (plan §7.1)** `[trazabilidad]`
  La usuaria aprueba el plan con mecanismo n8n: Q1 (multipart HTML con paleta),
  Q2 (best-effort), Q3 (mismo webhook de HU-007), Q4 (`automation_events`),
  Q5 (rama `feature/hu-008`), Q6 (la app compone; n8n transporta), Q7 (PII
  `to`+`patient_name`) y D15 (adaptación de TC-007-002/007).
  Hecho cuando: las filas Q1–Q7 de `plan.md` §7.1 están fechadas y §7.2 tiene
  marcada la aprobación.

- [x] **T2 — Spec 008: enmienda con mecanismo n8n y contratos fijados (plan §8.1)** `[RF-1][RF-2][RF-3][RF-4][RNF-1][RNF-2]`
  Petición explícita de la usuaria («Modifiquemos la spec»): sección
  «Contratos fijados» con mecanismo vía n8n (Q3), payload
  `appointment.confirmation_email` con `recipient`/`message` (Q6/Q7), registro y
  dedup en `automation_events` (Q4), contenido multipart (Q1), fallo
  best-effort (Q2), contrato de integración del workflow de n8n y fuera de
  alcance del SMTP propio.
  Hecho cuando: `specs/008_enviar-correo/spec.md` contiene «Contratos fijados»,
  sus dos dudas constan [RESUELTA] y `python -m pytest -q` sigue en
  **147 PASS / 0 FAIL**.

- [x] **T3 — Git: rama `feature/hu-008` desde `main` + commit de spec/plan/task (plan §8.0, Q5/D12)** `[base][regresión]`
  Crear la rama desde `main` (HU-007 mergeada); commitear `spec.md`, `plan.md`
  y `task.md`; verificar el baseline antes de tocar código.
  Hecho cuando: `git branch --show-current` → `feature/hu-008`,
  `git merge-base --is-ancestor main feature/hu-008` → exit 0, `git status`
  limpio y `python -m pytest -q` → **147 PASS / 0 FAIL**.

- [x] **T4 — Espejo: literales del correo en `tests/expected_content.py` (plan §8.3, D10)** `[RF-2]`
  Añadir los literales contractuales de plan §2.2 (asunto, etiquetas, pie,
  motivos, incluido `DETAIL_EMAIL_NOT_CONFIGURED`); sin lógica.
  Hecho cuando: `python -c "import tests.expected_content as e; assert e.EMAIL_SUBJECT_TEMPLATE and e.DETAIL_EMAIL_NOT_CONFIGURED == 'Envío de correo no configurado.'"` → exit 0.

- [x] **T5 — Contenido: `email_content.py` (plan §8.4, §2.2/§2.2.1, D5/D6/D7)** `[RF-2][RNF-2]`
  `EMAIL_SUBJECT_TEMPLATE`, etiquetas, `EMAIL_FOOTER`, `EMAIL_HTML_TEMPLATE`
  (paleta, inline, sin remotos), `WEEKDAYS_ES`/`MONTHS_ES`,
  `MSG_APPOINTMENT_INCOMPLETE`, `DETAIL_INVALID_RECIPIENT`,
  `DETAIL_EMAIL_NOT_CONFIGURED`; reutilizar los motivos de
  `automation_content`; sin lógica ni BD.
  Hecho cuando: `python -c "from consultorio.content.email_content import EMAIL_SUBJECT_TEMPLATE as s, MONTHS_ES as m, DETAIL_EMAIL_NOT_CONFIGURED as d; assert 'Confirmación de tu cita' in s and len(m) == 12 and d"` → exit 0
  y `python -c "import tests.expected_content as e; from consultorio.content import email_content as c; assert e.EMAIL_SUBJECT_TEMPLATE == c.EMAIL_SUBJECT_TEMPLATE"` → exit 0.

- [x] **T6 — Servicio: `email_service.py` (plan §8.5, §3, D1/D11/D14)** `[RF-1][RF-2][RF-3][RF-4][CL-1][CL-2][CL-3][CL-4][RNF-1]`
  `EVENT_TYPE`/`EVENT_VERSION`, `build_confirmation_message()`,
  `build_event()` (allowlist con `recipient`/`message`, sin documento/teléfono),
  `send_confirmation()` (defensivos → `insert_event` con dedup → URL vacía
  `skipped` → `_post_webhook` por referencia de módulo → `sent`/`failed`;
  **nunca propaga**).
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/email_service.py').read_text(encoding='utf-8'); assert 'smtplib' not in src and 'automation_service._post_webhook' in src and 'document_number' not in src"` → exit 0
  y `python -m pytest -q` → **0 FAIL**.

- [x] **T7 — Disparo en `create_booking()` (plan §8.6, firma intacta)** `[RF-1][RF-3]`
  Tras `on_appointment_confirmed()`, invocar
  `email_service.send_confirmation(appointment, db, automation_url,
  automation_timeout, automation_auth_header)`; sin cambios de firma ni en
  `web/appointments.py`.
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/appointment_service.py').read_text(encoding='utf-8'); assert 'send_confirmation' in src and 'email_settings' not in src"` → exit 0
  y `python -m pytest tests/test_appointment_routes.py tests/test_double_booking_routes.py -q` → **0 FAIL**.

- [x] **T8 — Adaptación D15: TC-007-002 y TC-007-007 filtran por `event_type` (plan §5 D15)** `[regresión][RF-1]`
  En `tests/test_automation_service.py`, contar los POST de
  `appointment.confirmed` filtrando `payload["event_type"]` (los tests siguen
  exigiendo 1 POST por tipo y el dedup); sin relajar ninguna otra aserción.
  Hecho cuando: `python -m pytest tests/test_automation_service.py tests/test_hu_007.py -v` → **0 FAIL** y el diff solo toma esas dos funciones.

- [x] **T9 — Tests de servicio `test_email_service.py` (plan §6.1, TC-008-001..010)** `[RF-1..RF-4][CL-1..CL-4][RNF-1][RNF-2]`
  10 tests con `_post_webhook` parcheado: mensaje (4 campos, paleta, sin
  remotos/PII extra); 2xx → `sent` + 1 POST del tipo con payload completo; URL
  vacía → `skipped`; `URLError`/`TimeoutError` → `failed` + cita intacta;
  reproceso → 1 evento y 1 POST; aislamiento; datos incompletos; email inválido;
  allowlist del payload (`event_id` determinista, sin documento/teléfono).
  Hecho cuando: `python -m pytest tests/test_email_service.py -v` → **10 PASS / 0 FAIL**.

- [x] **T10 — Tests de HU `test_hu_008.py` (plan §6.1, TC-008-011..016)** `[RF-1][RF-2][RF-3][RF-4][RNF-1]`
  Registro (2 eventos por reserva con webhook, `COUNT(*)=1` por `event_id`);
  config (sin `SMTP_*`, defaults de HU-007 intactos); espejo; stdlib-only
  (sin `smtplib`); HTTP end-to-end 303 + evento `sent`; regresión funcional
  HU-004/005/006/007 y email inválido → 200 + 0 eventos de correo.
  Hecho cuando: `python -m pytest tests/test_hu_008.py -v` → **6 PASS / 0 FAIL**.

- [x] **T11 — Regresión y suite completa (plan §6.1 TC-008-017, §6.2)** `[todos]`
  Ejecutar la suite completa sin tocar más tests previos.
  Hecho cuando: `python -m pytest -q` → **0 FAIL** con los **147 previos**
  intactos (tras D15) más los **16 nuevos** (**163 en total**).

- [x] **T12 — Evidencia QA y demo manual (plan §6.2/§6.3)** `[RF-1][RF-2][RF-3][RF-4][CL-2][RNF-2][finalización]`
  Servidor + **receptor local stdlib** (JSON sobre el webhook):
  (a) reserva → 303/200 y **2 POST** capturados (`appointment.confirmed` y
  `appointment.confirmation_email` con subject/text/html de §2.2);
  (b) ambos eventos `sent`; (c) receptor apagado → reserva intacta + `failed`
  con motivo; (d) reproceso → sin POST adicionales. Demo live opcional con la
  n8n de la usuaria (workflow + nodo de email según el contrato de integración;
  token solo en entorno). Evidencia = payload capturado + dump de
  `automation_events`. Sin cambios visuales → sin capturas 1280/375.
  Informe `docs/evidencias/hu-008/qa-hu-008.md` con PASS/FAIL por TC y checkbox
  de aceptación (skill `pytest-qa`).
  Hecho cuando: existe `qa-hu-008.md` con veredicto **PASS** (16 TC, suite
  163/163), la evidencia en `docs/evidencias/hu-008/` y el servidor en marcha
  con la URL comunicada.

- [x] **T13 — Commits por fase, Push y `MEMORY.md` (plan §8.11)** `[trazabilidad]`
  Commits por fase (spec+plan+task+espejo → contenido → servicio+disparo →
  adaptación D15+tests → evidencia+MEMORY) citando HU-008/Spec 008; nunca
  claves, tokens ni PII en repo o memoria.
  Hecho cuando: `git status` limpio, `git rev-parse HEAD` =
  `git rev-parse origin/feature/hu-008` y `MEMORY.md` registra HU-008
  (evento `appointment.confirmation_email`, vía n8n, `automation_events`, D15).

- [ ] **T14 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `qa-hu-008.md` está marcado con
  fecha y la §7.2 del plan queda íntegramente en `[x]`.
