# Tareas HU-004 — Agendar una cita

> Trazabilidad: HU-004 → Spec 004 → `plan.md` (aprobado 2026-10-09) → **este task.md** → código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su `Hecho cuando:`
> es verificable con un comando o una observación concreta. Sin marcar una tarea, no se
> empieza la siguiente. RF indicados por tarea (matriz completa en `plan.md` §0).

## Tareas

- [x] **T1 — Git: rama de trabajo (plan §8.0)** `[base/regresión]`
  Merge `feature/identidad-buscador` (HU-016 aceptada) en `main` y crear `feature/hu-004`
  desde `main` (Q6). `plan.md` y `task.md` quedan como ficheros sin seguimiento en la
  rama nueva, listos para su commit.
  Hecho cuando: `git branch --show-current` → `feature/hu-004`, `git status` limpio salvo
  `specs/004_agendar-cita/{plan,task}.md` sin seguimiento y
  `git merge-base --is-ancestor feature/identidad-buscador main` → exit 0.

- [x] **T2 — Aprobación de los literales Q9 (plan §2.2, §7.1)** `[RF-1][RF-2][RF-3][trazabilidad]`
  La usuaria aprueba los literales propuestos en el plan §2.2 (mensajes de error, literal
  RF-3, `CONFIRMATION_TITLE`, `STATUS_PENDING_LABEL`, `BOOKING_HELPER` y `MSG_NO_HOURS`).
  **Bloquea T3** (los textos son contrato: AGENTS.md «Textos contractuales»).
  Hecho cuando: la aprobación queda registrada con fecha en la fila Q9 de
  `plan.md` §7.1 y la casilla correspondiente de §7.2 está marcada.

- [x] **T3 — Spec 004: enmienda con dudas cerradas y literales fijados (plan §8.1)** `[RF-1][RF-2][RF-3][RF-4][RF-5][CL-1][CL-2][CL-5]`
  Petición explícica sobre `specs/`: cerrar las 2 dudas abiertas (Q1 datos obligatorios,
  Q2 estado inicial «Pendiente») y añadir los literales del plan §2.2 — 8 campos
  obligatorios, `BOOKING_HOURS` (14 bloques de 30 min, 08:00–12:00 / 14:00–17:00 como
  fin), solo lunes–viernes con fecha ≥ hoy y mensajes de error/éxito.
  Hecho cuando: `specs/004_agendar-cita/spec.md` contiene los literales idénticos a los
  del plan §2.2 (comparación directa), sus 2 dudas aparecen cerradas y
  `python -m pytest -q` sigue en **74 PASS / 0 FAIL**.

- [x] **T4 — Config y espejo en `tests/expected_content.py` (plan §8.3)** `[RF-1][RF-2][RF-3][RF-4]`
  `Config.DATABASE_PATH` (`data/consultorio.db`), `data/` en `.gitignore` y espejo único
  con `BOOKING_HOURS`, `DOCUMENT_TYPES` y todos los mensajes de la spec (D15). **No se
  toca aún `PLACEHOLDER_SECTIONS`** (eso va en T11, junto con la ruta).
  Hecho cuando: `python -c "from tests.expected_content import BOOKING_HOURS as h, DOCUMENT_TYPES as d; assert len(h) == 14 and len(d) == 5"` → exit 0
  y `grep -c "^data/$" .gitignore` → `1` y `python -m pytest -q` → **74 PASS / 0 FAIL**.

- [x] **T5 — Módulo de contenido `content/appointment_content.py` (plan §8.4)** `[RF-1][RF-2][RNF-1]`
  `BOOKING_HOURS` (08:00–11:30 y 14:00–16:30), `DOCUMENT_TYPES` (CC, TI, CE, PASSPORT,
  RC), `BOOKING_PAGE_TITLE` y todos los literales de mensajes (claves en inglés, textos
  en español — D15).
  Hecho cuando: `python -c "from consultorio.content.appointment_content import BOOKING_HOURS as h, DOCUMENT_TYPES as d; assert len(h) == 14 and h[0] == '08:00' and h[-1] == '16:30' and [c for c, _ in d] == ['CC', 'TI', 'CE', 'PASSPORT', 'RC']"` → exit 0.

- [x] **T6 — Tests de contenido `test_appointment_content.py` (plan §6.1, TC-004-001..003)** `[RF-1][RF-2]`
  14 horas exactas y ordenadas, 5 tipos de documento, espejo spec ↔ plan ↔
  `expected_content` ↔ `appointment_content`.
  Hecho cuando: `python -m pytest tests/test_appointment_content.py -v` → **3 PASS / 0 FAIL**.

- [x] **T7 — Persistencia `persistence/` + fixture de BD en `conftest.py` (plan §8.5)** `[RF-3][RF-4][CL-4]`
  `database.py` (`get_connection()`, `init_db()` con las 11 columnas y
  `UNIQUE (service, date, time)`) y `appointments_repository.py` (`insert_appointment`,
  `get_appointment_by_id`, `is_slot_taken`, `list_booked_times`). `conftest.py`: la
  fixture `app` apunta `DATABASE_PATH` a un temporal por test y lo borra al cerrar (los
  74 tests previos no se tocan).
  Hecho cuando: `python -c "import os, tempfile; from consultorio.persistence.database import init_db, get_connection; p = os.path.join(tempfile.mkdtemp(), 't.db'); init_db(p); c = get_connection(p); assert len(c.execute('PRAGMA table_info(appointments)').fetchall()) == 11"` → exit 0
  y `python -m pytest -q` → **74 PASS / 0 FAIL**.

- [x] **T8 — Tests de persistencia `test_appointment_persistence.py` (plan §6.1, TC-004-004..007)** `[RF-3][RF-4][CL-4]`
  Esquema con UNIQUE, insert/recuperación con `status='pending'`, `IntegrityError` ante
  duplicado (1 fila) y permiso de la misma hora con servicio distinto.
  Hecho cuando: `python -m pytest tests/test_appointment_persistence.py -v` → **4 PASS / 0 FAIL**.

- [x] **T9 — Servicio `services/appointment_service.py` (plan §8.6)** `[RF-1][RF-2][RF-3][RF-4][RF-5][CL-1][CL-2][CL-3][CL-4][CL-5]`
  `validate_booking()` (reglas §2.3, sin excepciones), `get_available_hours()`
  (catálogo − ocupadas; `[]` en finde/pasada) y `create_booking()` con doble
  comprobación SELECT + `IntegrityError` → `SLOT_TAKEN` (D9).
  Hecho cuando: `python -c "from consultorio.services.appointment_service import validate_booking as v; ok = {'service': 'nutrition', 'date': '2026-10-12', 'time': '08:00', 'document_type': 'CC', 'document_number': '1234567890', 'patient_name': 'Ana Pérez', 'email': 'ana@correo.com', 'phone': '3001234567'}; assert v(ok) == {} and 'email' in v({**ok, 'email': 'malo'}) and 'service' in v({**ok, 'service': 'nope'}) and 'date' in v({**ok, 'date': '2026-10-11'})"` → exit 0.

- [x] **T10 — Tests de servicio `test_appointment_service.py` (plan §6.1, TC-004-008..014)** `[RF-1][RF-2][RF-3][RF-4][RF-5][CL-1][CL-2][CL-3][CL-4][CL-5]`
  Datos válidos sin errores; mensaje por campo ante vacíos e inválidos; servicio fuera de
  catálogo; disponibilidad (14 slots, tras reserva desaparece la hora, finde → `[]`);
  `create_booking()` sobre horario ocupado → `SLOT_TAKEN` sin insertar.
  Hecho cuando: `python -m pytest tests/test_appointment_service.py -v` → **7 PASS / 0 FAIL**.

- [x] **T11 — Capa web + plantillas + placeholders (plan §8.7)** `[RF-1][RF-2][RF-3][RF-4][RF-5][regresión HU-001/002/003/016]`
  `web/appointments.py` (GET/POST `/citas`, GET `/citas/horarios`, GET
  `/citas/confirmada/<id>`; 200/303/400/404/405 según §4.2), plantillas
  `appointments/index.html` (8 campos + «Volver al inicio») y `confirmation.html`
  («Pendiente»), retiro de `/citas` de `placeholders.py`, registro de `appointments_bp`
  + `init_db()` en `create_app()` y `PLACEHOLDER_SECTIONS` sin `/citas` (D16).
  Hecho cuando: `python -c "from consultorio import create_app; c = create_app().test_client(); r = c.get('/citas'); assert r.status_code == 200 and 'Agendar cita' in r.get_data(as_text=True)"` → exit 0
  y `python -m pytest -q` → **0 FAIL**.

- [x] **T12 — Tests de ruta `test_appointment_routes.py` (plan §6.1, TC-004-015..023)** `[RF-1][RF-2][RF-3][RF-4][RF-5][regresión]`
  Formulario completo (200), alta válida 303 → confirmación, rechazos en 200 con 0
  inserts, JSON de `/citas/horarios` (200/400/405), confirmación 404, `PUT /citas` → 405
  y regresión de placeholders y navegación.
  Hecho cuando: `python -m pytest tests/test_appointment_routes.py -v` → **9 PASS / 0 FAIL**.

- [x] **T13 — JS de disponibilidad `static/js/availability.js` (plan §8.8)** `[RF-1][RF-3][RNF-2]`
  Vanilla con `fetch` a `/citas/horarios` al cargar y al cambiar servicio/fecha; rellena
  el `<select>` de horas y muestra `MSG_NO_HOURS` con la lista vacía; sin librerías
  externas (constitución #1). Enlazado desde `appointments/index.html`.
  Hecho cuando: `python -c "import pathlib; js = pathlib.Path('static/js/availability.js').read_text(encoding='utf-8'); assert 'fetch(' in js and 'import ' not in js and 'import(' not in js"` → exit 0
  y `python -c "from consultorio import create_app; assert 'availability.js' in create_app().test_client().get('/citas').get_data(as_text=True)"` → exit 0.

- [x] **T14 — CSS `.appointment-*` en `main.css` (plan §8.9, D14)** `[RNF-2]`
  Sección mobile-first con paleta intacta (solo los 6 hex), tipografía vigente y párrafos
  `text-align: justify` + `hyphens: none`.
  Hecho cuando: `python -m pytest tests/test_hu_001.py tests/test_hu_003.py tests/test_hu_016.py -q` → **0 FAIL** (paleta y reglas existentes intactas)
  y `grep -c "\.appointment-" static/css/main.css` → `>= 1`.

- [x] **T15 — Tests de HU `test_hu_004.py` (plan §6.1, TC-004-024..027)** `[RNF-1][RNF-2][fuera de alcance]`
  RNF (viewport, `@media`, paleta ⊆ 6 hex, justify + hyphens, sin desborde a 375 px, JS
  sin dependencias), formulario estrictamente de 8 campos, E2E home → «Agendar cita» →
  submit → confirmación y ausencia de textos de correo/WhatsApp/cancelación.
  Hecho cuando: `python -m pytest tests/test_hu_004.py -v` → **4 PASS / 0 FAIL**.

- [x] **T16 — Suite completa y regresión (plan §6.2)** `[todos]`
  Hecho cuando: `python -m pytest -q` → **0 FAIL** con los **74 tests previos** intactos
  (HU-001/002/003/016 sin relajar) más los **27 nuevos** de HU-004 (**101 en total**).

- [x] **T17 — Evidencia QA y visual (plan §6.3, §8.12)** `[RF-1][RF-3][RNF-2][finalización]`
  Servidor (`python app.py`), recorrido manual del flujo (formulario, error de
  validación, horario ocupado, confirmación), capturas CDP 1280/375 →
  `docs/evidencias/hu-004/`, informe `qa-hu-004.md` con PASS/FAIL por TC y veredicto
  (skill `pytest-qa`).
  Hecho cuando: existen `qa-hu-004.md` con veredicto **PASS** (27 TC en verde),
  `escritorio-1280.png` y `movil-375.png` verificadas por medidas programáticas, y
  `GET /citas` → 200 con el servidor en marcha (URL comunicada a la usuaria).

- [x] **T18 — Commits por fase, Push y `MEMORY.md` (plan §8.13)** `[trazabilidad]`
  Commits separados por fase (spec+plan+task, contenido, persistencia, servicio, web,
  JS/CSS, tests, evidencia) con mensajes que citan HU-004/Spec 004.
  Hecho cuando: `git status` limpio, `git rev-parse HEAD` = `git rev-parse origin/feature/hu-004`
  y `MEMORY.md` registra HU-004 (incluida la primera persistencia del proyecto).

- [x] **T19 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `docs/evidencias/hu-004/qa-hu-004.md`
  está marcado con fecha y la §7.2 del plan queda íntegramente en `[x]`.
  **Aceptada el 2026-10-09** (incluye la modificación visual D19 y el ajuste de
  columna izquierda).

- [x] **T20 — Modificación visual: 2 columnas + datepicker + bloques (plan D19)** `[RNF-2]`
  Layout en 2 columnas (datos del paciente ‖ datepicker + horas), datepicker
  vanilla con días agendables (lun–vie ≥ hoy) diferenciados y navegación de
  meses, horas en bloques Mañana/Tarde; literales nuevos en content/espejo.
  Hecho cuando: `python -m pytest -q` → **0 FAIL** (101 + 1 nuevo TC-004-028),
  `GET /citas` → 200 con las dos columnas, y evidencia visual regenerada.
