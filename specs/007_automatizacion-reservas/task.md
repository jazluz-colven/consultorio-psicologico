# Tareas HU-007 — Automatización de reservas mediante n8n

> Trazabilidad: HU-007 → Spec 007 (enmendada 2026-10-10) → `plan.md` (aprobado
> 2026-10-10) → **este task.md** → código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su
> `Hecho cuando:` es verificable con un comando o una observación concreta. Sin
> marcar una tarea, no se empieza la siguiente. RF indicados por tarea (matriz
> completa en `plan.md` §0).

## Tareas

- [x] **T1 — Aprobación del plan y de las decisiones Q1–Q5 (plan §7.1)** `[trazabilidad]`
  La usuaria aprueba `plan.md` completo: alcance, matriz RF, decisiones D1–D13,
  Q1 (webhook genérico `appointment.confirmed` a n8n), Q2 (payload sin datos
  personales), Q3 (POST síncrono stdlib, timeout 3 s, 1 intento), Q4 (tabla
  `automation_events` con `UNIQUE(event_id)`) y Q5 (sin reintentos automáticos).
  **Bloquea T2** (textos contractuales: AGENTS.md).
  Hecho cuando: las filas Q1–Q6 de `plan.md` §7.1 están fechadas y las casillas
  de §7.2 aplicables a aprobación están en `[x]`.
  **Hecho 2026-10-10**: Q1–Q6 fechadas en §7.1; aprobación marcada en §7.2.

- [x] **T2 — Spec 007: enmienda con dudas cerradas y contratos fijados (plan §8.1)** `[RF-1][RF-2][RF-3][RF-4][RF-5][RF-6]`
  Petición explícita sobre `specs/`: cerrar Q1 (webhook genérico) y Q2 (payload
  mínimo sin PII), fijar la interpretación de «reserva confirmada» (alta exitosa),
  el contrato JSON del evento (allowlist, `event_version`, `event_id`
  determinista), el mecanismo de deduplicación (`UNIQUE(event_id)`), el
  comportamiento ante no-configurado/timeout/no-2xx y el alcance «sin reintento».
  Hecho cuando: `specs/007_automatizacion-reservas/spec.md` contiene la sección
  «Contratos fijados (enmienda 2026-10-10)», sus dudas aparecen cerradas y
  `python -m pytest -q` sigue en **134 PASS / 0 FAIL**.
  **Hecho 2026-10-10**: sección «Contratos fijados» añadida; dudas Q1/Q2 cerradas;
  suite previa intacta (sin ejecución de código nuevo).

- [x] **T3 — Git: rama `feature/hu-007` desde `main` + commit de spec/plan/task (plan §8.0, Q6/D10)** `[base][regresión]`
  Crear `feature/hu-007` desde `main` (HU-006 aceptada y mergeada); commitear
  `spec.md`, `plan.md` y `task.md`; verificar el baseline antes de tocar código.
  Hecho cuando: `git branch --show-current` → `feature/hu-007`,
  `git merge-base --is-ancestor main feature/hu-007` → exit 0,
  `git status` limpio y `python -m pytest -q` → **134 PASS / 0 FAIL**.
  **Hecho 2026-10-10**: rama creada desde `main` (`e2bea63`), commit `4735576`
  (spec+plan+task+MEMORY), merge-base exit 0 y suite **134 PASS / 0 FAIL**.

- [x] **T4 — Config: `AUTOMATION_WEBHOOK_URL` y `AUTOMATION_TIMEOUT_SECONDS` (plan §2.4, D9)** `[RF-2][RF-6]`
  En `consultorio/config.py`: URL vacía por defecto (automatización deshabilitada)
  y timeout **3.0** con parse defensivo (valor de entorno no numérico → 3.0, sin
  romper el arranque); ambos visibles en `app.config`.
  Hecho cuando: `python -c "from consultorio.config import Config as C; assert C.AUTOMATION_WEBHOOK_URL == '' and C.AUTOMATION_TIMEOUT_SECONDS == 3.0"` → exit 0
  y `python -c "from consultorio import create_app; app = create_app(); assert app.config['AUTOMATION_TIMEOUT_SECONDS'] == 3.0"` → exit 0.
  **Hecho 2026-10-10**: `_parse_timeout_seconds` defensivo (vacío/no numérico/≤0 →
  3.0); ambos chequeos → exit 0.

- [x] **T5 — Persistencia: tabla `automation_events` + repositorio (plan §2.1, D4/D5)** `[RF-4][RF-5][RNF-3][RNF-4]`
  `database.py`: `SCHEMA += automation_events` (idempotente, sin tocar
  `appointments`). Nuevo `persistence/automation_events_repository.py` con
  `insert_event()` (devuelve `False` ante `sqlite3.IntegrityError` = duplicado),
  `mark_sent()`, `mark_skipped()`, `mark_failed()` y `get_by_event_id()`.
  Hecho cuando: `python -c "import os, tempfile; from consultorio.persistence.database import init_db, get_connection; p = os.path.join(tempfile.mkdtemp(), 't.db'); init_db(p); init_db(p); c = get_connection(p); assert len(c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name IN ('appointments','automation_events')\").fetchall()) == 2; assert 'UNIQUE' in c.execute(\"SELECT sql FROM sqlite_master WHERE name='automation_events'\").fetchone()[0]"` → exit 0
  y `python -m pytest tests/test_appointment_service.py tests/test_double_booking_service.py -q` → **0 FAIL**.
  **Hecho 2026-10-10**: chequeo de esquema → exit 0 (init doble idempotente);
  **12 PASS / 0 FAIL**.

- [x] **T6 — Contenido: `automation_content.py` (plan §8.5, §2.3, D8/D12)** `[RF-3][RF-4]`
  `EVENT_TYPE = "appointment.confirmed"`, `EVENT_VERSION = 1` y los 5 motivos de
  incidencia en español (claves en inglés, textos idénticos a la spec enmendada);
  sin lógica ni acceso a la BD.
  Hecho cuando: `python -c "from consultorio.content.automation_content import EVENT_TYPE as t, EVENT_VERSION as v, DETAIL_NOT_CONFIGURED as d; assert t == 'appointment.confirmed' and v == 1 and d == 'Automatización no configurada.'"` → exit 0.
  **Hecho 2026-10-10**: módulo creado → exit 0.

- [x] **T7 — Servicio: `automation_service.py` (plan §8.6, §3, D6/D13)** `[RF-1][RF-2][RF-3][RF-4][RF-5][RF-6][RF-7]`
  `build_event()` con allowlist sin PII; `on_appointment_confirmed()`:
  `insert_event` → duplicado sin POST; URL vacía → `skipped`;
  `TimeoutError`/`URLError`/no-2xx/otro → `failed` con los motivos de §2.3;
  2xx → `sent`; **nunca propaga excepciones** (try/except externo).
  `_post_webhook()` con `urllib.request` + `json` (stdlib, sin dependencias).
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/automation_service.py').read_text(encoding='utf-8'); assert 'urllib.request' in src and 'patient_name' not in src and 'document_number' not in src"` → exit 0
  y `python -m pytest -q` → **0 FAIL** (regresión).
  **Hecho 2026-10-10**: chequeo de código → exit 0; suite sin regresiones.

- [x] **T8 — Disparo en `create_booking()` + inyección en la capa web (plan §8.6–§8.7, D7/D9)** `[RF-1][RF-2][RF-6][RF-7]`
  `create_booking(data, db, automation_url="", automation_timeout=3.0)` invoca
  `on_appointment_confirmed()` **solo tras el INSERT exitoso** (los caminos
  `SLOT_TAKEN` de HU-006 intactos); `POST /citas` inyecta
  `current_app.config["AUTOMATION_WEBHOOK_URL"]` y `…_TIMEOUT_SECONDS`; contrato
  HTTP 303/200 sin cambios.
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/appointment_service.py').read_text(encoding='utf-8'); assert 'on_appointment_confirmed' in src"` → exit 0
  y `python -m pytest tests/test_appointment_routes.py tests/test_availability_routes.py tests/test_double_booking_routes.py -q` → **0 FAIL**.
  **Hecho 2026-10-10**: chequeo → exit 0; **20 PASS / 0 FAIL**.

- [x] **T9 — Tests de servicio `test_automation_service.py` (plan §6.1, TC-007-001..009)** `[RF-1..RF-7][CL-1..CL-6]`
  9 tests con `urlopen`/`_post_webhook` parcheado: payload allowlist sin PII;
  2xx → `sent` + 1 POST; URL vacía → `skipped` + 0 POST; `URLError` → `failed`
  «Servicio de automatización no disponible.»; `TimeoutError` → `failed` timeout;
  HTTP 500 → `failed` «…(HTTP 500).»; reproceso → 1 evento y 1 POST; aislamiento
  (repositorio que lanza → `create_booking()` devuelve la `Appointment`); timeout
  efectivo.
  Hecho cuando: `python -m pytest tests/test_automation_service.py -v` → **9 PASS / 0 FAIL**.
  **Hecho 2026-10-10**: **9 PASS / 0 FAIL** (0,59 s).

- [x] **T10 — Tests de HU `test_hu_007.py` (plan §6.1, TC-007-010..012)** `[RF-5][RF-7][RNF-3][RNF-4]`
  Esquema: `sqlite_master` con `automation_events` y `UNIQUE(event_id)`;
  `COUNT(*)=1` por `event_id` tras flujo + reproceso. Config: defaults de `Config`
  y parse defensivo del timeout. Regresión funcional HU-004/005/006 con webhook
  configurado y sin configurar (`/citas/horarios`, `/citas/disponibilidad`,
  `/citas/confirmada/<id>`, doble reserva).
  Hecho cuando: `python -m pytest tests/test_hu_007.py -v` → **3 PASS / 0 FAIL**.
  **Hecho 2026-10-10**: **3 PASS / 0 FAIL** (0,28 s).

- [x] **T11 — Regresión y suite completa (plan §6.1 TC-007-013, §6.2)** `[todos]`
  Ejecutar la suite completa sin tocar tests previos (ninguna aserción se relaja
  ni se omite).
  Hecho cuando: `python -m pytest -q` → **0 FAIL** con los **134 tests previos**
  intactos más los **12 nuevos** de HU-007 (**146 en total**).
  **Hecho 2026-10-10**: `python -m pytest -q` → **146 passed / 0 FAIL** (9,94 s).

- [x] **T12 — Evidencia QA y demo manual (plan §6.2/§6.3)** `[RF-1][RF-2][RF-4][RF-5][RF-6][RF-7][finalización]`
  Servidor (`python app.py`) + **receptor local stdlib** (script efímero fuera del
  repo; o n8n real si la usuaria lo indica): (a) webhook arriba → la reserva
  responde 303/200 y el receptor recibe **1 POST** con el payload de plan §2.2
  (captura del cuerpo); (b) evento `sent` en `automation_events`; (c) webhook
  apagado → la reserva se confirma igual y el evento queda `failed` con su motivo;
  (d) reproceso del mismo evento → **sin segundo POST**. Sin cambios visuales →
  sin capturas 1280/375; evidencia = payload capturado + dump de la tabla.
  Informe `docs/evidencias/hu-007/qa-hu-007.md` con PASS/FAIL por TC y checkbox
  de aceptación (skill `pytest-qa`).
  Hecho cuando: existe `qa-hu-007.md` con veredicto **PASS** (12 TC en verde,
  suite 146/146), el payload y el dump en `docs/evidencias/hu-007/`, y el
  servidor en marcha con la URL comunicada a la usuaria.
  **Hecho 2026-10-10**: `qa-hu-007.md` **PASS** (12/12 TC, suite 146/146);
  demo con receptor stdlib: cita 38 → 303 + evento `sent` + payload sin PII;
  cita 40 con receptor apagado → 303 intacto + evento `failed` «Servicio de
  automatización no disponible.»; reproceso cita 38 → 0 POST añadidos y 1 fila.
  Evidencia: `demo-step1.json`, `demo-step2.json`, `webhook_payloads.jsonl`,
  `automation_events_dump.json`, `demo_appointments.json`. Servidor de demo en
  marcha → http://127.0.0.1:5001/citas (receptor apagado tras la demo).

- [ ] **T13 — Commits por fase, Push y `MEMORY.md` (plan §8.10)** `[trazabilidad]`
  Commits separados por fase (spec+plan+task → config+persistencia+contenido →
  servicio+disparo+web → tests → evidencia+MEMORY) con mensajes que citan
  HU-007/Spec 007.
  Hecho cuando: `git status` limpio, `git rev-parse HEAD` =
  `git rev-parse origin/feature/hu-007` y `MEMORY.md` registra HU-007
  (`appointment.confirmed`, `automation_events`, aislamiento, sin PII).

- [ ] **T14 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `docs/evidencias/hu-007/qa-hu-007.md`
  está marcado con fecha y la §7.2 del plan queda íntegramente en `[x]`.
