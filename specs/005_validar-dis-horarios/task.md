# Tareas HU-005 — Validar disponibilidad de horarios

> Trazabilidad: HU-005 → Spec 005 → `plan.md` (propuesto, pendiente de aprobación) → **este task.md** → código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su `Hecho cuando:`
> es verificable con un comando o una observación concreta. Sin marcar una tarea, no se
> empieza la siguiente. RF indicados por tarea (matriz completa en `plan.md` §0).

## Tareas

- [x] **T1 — Aprobación del plan y de los literales Q1–Q4 (plan §7.1)** `[RF-1..RF-6][trazabilidad]`
  La usuaria aprueba `plan.md` completo: alcance, decisiones D1–D11, cierre de la duda
  Q1 (disponibilidad = servicio + fecha + hora) y los 5 literales nuevos de §2.2
  (`MSG_OCCUPIED_HOUR`, `MSG_CHECKING_HOURS`, `CALENDAR_LEGEND_FREE`,
  `CALENDAR_LEGEND_FULL`, `DAY_LABEL_NO_HOURS`).
  **Bloquea T2 y T3** (textos contractuales: AGENTS.md «Textos contractuales»).
  Hecho cuando: la aprobación queda registrada con fecha en las filas Q1–Q4 de
  `plan.md` §7.1 y las casillas aplicables de §7.2 están marcadas.
  **Hecho 2026-10-09**: Q1–Q4 fechadas en §7.1; §7.2 con las 3 primeras casillas en `[x]`.

- [x] **T2 — Git: rama de trabajo (plan §8.0, Q4)** `[base/regresión]`
  Crear `feature/hu-005` desde `main` (`6807afc`, HU-004 mergeada y aceptada).
  `plan.md` y `task.md` quedan como ficheros sin seguimiento en la rama nueva, listos
  para su commit.
  Hecho cuando: `git branch --show-current` → `feature/hu-005`, `git status` limpio salvo
  `specs/005_validar-dis-horarios/{plan,task}.md` sin seguimiento y
  `git merge-base --is-ancestor main feature/hu-005` → exit 0.
  **Hecho 2026-10-09**: rama creada desde `main` (`6807afc`), verificado con
  `git branch --show-current` y `git merge-base --is-ancestor`.

- [x] **T3 — Spec 005: enmienda con duda cerrada y literales/contratos fijados (plan §8.1)** `[RF-1][RF-2][RF-4][RF-6][RNF-1][RNF-2]`
  Petición explícita sobre `specs/`: cerrar la duda abierta (Q1: disponibilidad
  exclusivamente por servicio + fecha + hora, sin reglas adicionales), fijar los 5
  literales de §2.2 y el contrato HTTP — `/citas/horarios` con `available` + `occupied`
  y `GET /citas/disponibilidad?service=…&month=YYYY-MM` (200/400/405).
  Hecho cuando: `specs/005_validar-dis-horarios/spec.md` contiene los literales idénticos
  a los del plan §2.2 (comparación directa), su duda abierta aparece cerrada y
  `python -m pytest -q` sigue en **102 PASS / 0 FAIL**.
  **Hecho 2026-10-09**: sección «Literales y contrato» con los 5 literales del plan
  §2.2, «Dudas cerradas» con Q1 resuelta y verificación de regresión
  **102 PASS / 0 FAIL**.

- [x] **T4 — Espejo en `tests/expected_content.py` (plan §8.3, D11)** `[RF-4][RF-6][RNF-1][RNF-2]`
  Añadir los 5 literales nuevos de la spec al espejo único, sin tocar los literales de
  HU-004.
  Hecho cuando: `python -c "from tests import expected_content as e; from consultorio.content import appointment_content as c; assert e.MSG_OCCUPIED_HOUR == c.MSG_OCCUPIED_HOUR == 'Ocupado' and e.MSG_CHECKING_HOURS == c.MSG_CHECKING_HOURS and e.CALENDAR_LEGEND_FREE == c.CALENDAR_LEGEND_FREE and e.CALENDAR_LEGEND_FULL == c.CALENDAR_LEGEND_FULL and e.DAY_LABEL_NO_HOURS == c.DAY_LABEL_NO_HOURS"` → exit 0.
  **Hecho 2026-10-09**: comando → exit 0.

- [x] **T5 — Literales en `content/appointment_content.py` (plan §8.4, §2.2)** `[RF-4][RF-6][RNF-1][RNF-2]`
  `MSG_OCCUPIED_HOUR`, `MSG_CHECKING_HOURS`, `CALENDAR_LEGEND_FREE`,
  `CALENDAR_LEGEND_FULL` y `DAY_LABEL_NO_HOURS` (claves en inglés, textos en español,
  idénticos a la spec enmendada — constitución #6).
  Hecho cuando: `python -c "from consultorio.content.appointment_content import MSG_OCCUPIED_HOUR as o, MSG_CHECKING_HOURS as c, CALENDAR_LEGEND_FREE as f, CALENDAR_LEGEND_FULL as u, DAY_LABEL_NO_HOURS as d; assert o == 'Ocupado' and 'Consultando' in c and f == 'Con horarios disponibles' and u == 'Sin horarios disponibles' and d.startswith(', ')"` → exit 0.
  **Hecho 2026-10-09**: comando → exit 0.

- [x] **T6 — Repositorio `list_booked_times_by_date()` (plan §8.5, §3)** `[RF-1][RF-5][RF-6]`
  Nueva función de solo lectura en `persistence/appointments_repository.py`:
  `SELECT date, time … WHERE service = ? AND date >= ? AND date <= ?` agrupado por
  fecha; `insert_appointment`, `is_slot_taken` y `list_booked_times` sin cambios;
  esquema intacto.
  Hecho cuando: `python -c "import os, tempfile; from consultorio.persistence.database import init_db; from consultorio.persistence import appointments_repository as r; p = os.path.join(tempfile.mkdtemp(), 't.db'); init_db(p); r.insert_appointment({'document_type':'CC','document_number':'12345678','patient_name':'Ana Perez','email':'a@b.co','phone':'3001234567','service':'nutrition','date':'2026-10-13','time':'08:00'}, p); m = r.list_booked_times_by_date('nutrition','2026-10-01','2026-10-31',p); assert m == {'2026-10-13': ['08:00']}"` → exit 0.
  **Hecho 2026-10-09**: comando → exit 0 (commit `40a71ac`).

- [x] **T7 — Servicio: `get_hours_with_status()` y `get_available_days()` (plan §8.6, §3)** `[RF-1][RF-2][RF-4][RF-5][RF-6][CL-1][CL-3][CL-5]`
  `get_hours_with_status(service, date, db)` → `[(hora, bool)]` en orden de
  `BOOKING_HOURS` (`[]` en finde/pasada); `get_available_hours()` pasa a envoltura
  (contrato HU-004 intacto); `get_available_days(service, year, month, db)` → días
  laborables ≥ hoy con ≥ 1 libre, `[]` si no hay ninguno.
  Hecho cuando: `python -c "import os, tempfile; from consultorio.persistence.database import init_db; from consultorio.services.appointment_service import get_hours_with_status as g, get_available_hours as a, get_available_days as d; p = os.path.join(tempfile.mkdtemp(), 't.db'); init_db(p); pairs = g('nutrition','2026-10-13',p); assert len(pairs) == 14 and all(f for _, f in pairs) and a('nutrition','2026-10-13',p) == [h for h,_ in pairs] and g('nutrition','2026-10-11',p) == [] and len(d('nutrition',2026,10,p)) > 0"` → exit 0.
  **Hecho 2026-10-09**: comando → exit 0 (commit `9d92e0c`).

- [x] **T8 — Tests de servicio `test_availability_service.py` (plan §6.1, TC-005-001..007)** `[RF-1][RF-2][RF-4][RF-5][RF-6][CL-1][CL-3][CL-5]`
  14 pares libres en orden; hora reservada pasa a `free=False` y la envoltura la
  excluye; días sin citas = laborables ≥ hoy; tras `create_booking()` el día desaparece
  al llenarse los 14; día lleno en servicio A sigue libre en B; mes lleno → `[]`;
  ocupada en A libre en B (D2).
  Hecho cuando: `python -m pytest tests/test_availability_service.py -v` → **7 PASS / 0 FAIL**.
  **Hecho 2026-10-09**: **7 PASS** (commit `ef8a5ca`).

- [x] **T9 — Capa web: `/citas/horarios` con `occupied` + `GET /citas/disponibilidad` (plan §8.7, §4.2)** `[RF-1][RF-2][RF-4][RF-5][RF-6]`
  `handle_availability` devuelve `{"available": […], "occupied": […]}` (D9); nuevo
  `handle_month_days` con validación de servicio/mes (`YYYY-MM` real) → 200 `{"days": […]}`
  o 400 `{"error": "Parámetros inválidos."}`, otros métodos → 405; enmienda de TC-004-021
  para asertar ambas claves (refuerzo, D9).
  Hecho cuando: `python -c "import os, tempfile; from consultorio import create_app; from consultorio.persistence.database import init_db; p = os.path.join(tempfile.mkdtemp(), 't.db'); app = create_app(); app.config['DATABASE_PATH'] = p; init_db(p); c = app.test_client(); r = c.get('/citas/horarios?service=nutrition&date=2026-10-13'); j = r.get_json(); assert r.status_code == 200 and set(j) == {'available','occupied'} and len(j['available']) == 14 and j['occupied'] == []; d = c.get('/citas/disponibilidad?service=nutrition&month=2026-10'); assert d.status_code == 200 and isinstance(d.get_json()['days'], list) and c.get('/citas/disponibilidad?service=x&month=2026-10').status_code == 400 and c.post('/citas/disponibilidad').status_code == 405"` → exit 0
  y `python -m pytest tests/test_appointment_routes.py -q` → **0 FAIL**.
  **Hecho 2026-10-09**: JSON verificado → exit 0; HU-004 routes **0 FAIL** (commit `faf967c`).

- [x] **T10 — Tests de ruta `test_availability_routes.py` (plan §6.1, TC-005-008..013)** `[RF-1][RF-2][RF-3][RF-4][RF-5][CL-3][CL-5]`
  JSON con ambas claves (vacías en finde); hora en `occupied` tras insert; E2E reserva
  303 → reconsulta con la hora no disponible; `days` con laborables ≥ hoy; día lleno
  ausente para A y presente para B; 400 (servicio/mes inválidos) y 405.
  Hecho cuando: `python -m pytest tests/test_availability_routes.py -v` → **6 PASS / 0 FAIL**.
  **Hecho 2026-10-09**: **6 PASS** (commit `c37fd53`).

- [x] **T11 — Plantilla: horas ocupadas y leyenda (plan §8.7, §3)** `[RF-2][RF-4][RF-6][RNF-2]`
  En `templates/appointments/index.html`: radios ocupadas con `disabled`, **sin**
  `name`, clase `appointment__hour--taken` y `<span>` «Ocupado» dentro de su bloque
  Mañana/Tarde; leyenda del calendario (`CALENDAR_LEGEND_FREE` / `CALENDAR_LEGEND_FULL`)
  visible; `_render_form` alimenta ambas listas; literales nuevos en `data-*` del
  calendario (`data-checking`, `data-occupied-label`, `data-day-no-hours`,
  `data-slot-taken`).
  Hecho cuando: `python -c "import os, tempfile; from consultorio import create_app; from consultorio.persistence.database import init_db; p = os.path.join(tempfile.mkdtemp(), 't.db'); app = create_app(); app.config['DATABASE_PATH'] = p; init_db(p); h = app.test_client().get('/citas').get_data(as_text=True); q = chr(34); assert 'appointment__calendar-legend' in h and 'Con horarios disponibles' in h and 'Sin horarios disponibles' in h and h.count('name=' + q + 'time' + q) == 14"` → exit 0.
  **Hecho 2026-10-09**: comando → exit 0.

- [x] **T12 — JS `availability.js`: días, guard, carga y ocupadas (plan §8.8, §3)** `[RF-1][RF-2][RF-3][RF-4][RF-5][RF-6][CL-2][CL-3][CL-4][RNF-1]`
  Vanilla: `loadDayStates()` (fetch `/citas/disponibilidad` al iniciar, al cambiar mes y
  al cambiar servicio; fallo → degrada a D12), `renderCalendar()` con `is-full` +
  `disabled` + aria «sin horarios disponibles», `refreshHours()` con estado
  «Consultando disponibilidad…», guard de secuencia (`seq`) que ignora respuestas
  obsoletas, `fillHours(available, occupied)` con radios ocupadas deshabilitadas sin
  `name`, deselección si la hora elegida pasa a ocupada (`MSG_SLOT_TAKEN`) o desaparece.
  El literal de carga se sirve desde el atributo `data-checking` del calendario
  (patrón `data-empty-message` de HU-004), no incrustado en el JS.
  Hecho cuando: `python -c "import pathlib; js = pathlib.Path('static/js/availability.js').read_text(encoding='utf-8'); assert '/citas/disponibilidad' in js and 'is-full' in js and 'seq' in js and 'data-checking' in js and 'import ' not in js and 'import(' not in js"` → exit 0
  y `python -c "from consultorio import create_app; assert 'data-checking' in create_app().test_client().get('/citas').get_data(as_text=True)"` → exit 0.
  **Hecho 2026-10-09**: ambos comandos → exit 0; TC-004-028 sigue PASS (commit `f9b62f1`).

- [x] **T13 — CSS `.is-full`, `.appointment__hour--taken`, leyenda (plan §8.9)** `[RF-6][RNF-2]`
  Reglas mobile-first en `main.css` con la paleta intacta (solo los 6 hex), estado
  `is-full` distinguible **además del color** (texto/leyenda presente en el HTML),
  hora «Ocupado» atenuada y tachada, párrafos `justify` + `hyphens: none`.
  Hecho cuando: `python -m pytest tests/test_hu_001.py tests/test_hu_003.py tests/test_hu_004.py tests/test_hu_016.py -q` → **0 FAIL** (paleta y reglas HU-004 intactas)
  y `grep -c "is-full" static/css/main.css` → `>= 1` y `grep -c "appointment__hour--taken" static/css/main.css` → `>= 1`.
  **Hecho 2026-10-09**: **14 PASS** en regresión; `is-full` y `hour--taken` presentes (commit `6dedebd`).

- [x] **T14 — Tests de HU `test_hu_005.py` (plan §6.1, TC-005-014..015)** `[RF-3][RF-6][CL-2][CL-4][RNF-1][RNF-2]`
  Plantilla: leyenda visible, `data-*` con literales nuevos, CSS con las reglas nuevas,
  colores ⊆ paleta y justificación; `availability.js` (inspección estática): tokens
  `/citas/disponibilidad`, `is-full`, contador de secuencia, condición de guard,
  deselección y sin librerías externas.
  Hecho cuando: `python -m pytest tests/test_hu_005.py -v` → **2 PASS / 0 FAIL**.
  **Hecho 2026-10-09**: **2 PASS**.

- [x] **T15 — Regresión y suite completa (plan §6.1 TC-005-016, §6.2)** `[RF-6][todos]`
  Añadir TC-005-016 (carga inicial `/citas` con BD vacía: 14 `name="time"`, 0 radios
  ocupados) y ejecutar la suite completa.
  Hecho cuando: `python -m pytest tests/test_hu_005.py -q` → **3 PASS / 0 FAIL** y
  `python -m pytest -q` → **0 FAIL** con los **102 tests previos** intactos (única
  enmienda: TC-004-021 con dos claves, D9) más los **16 nuevos** de HU-005
  (**118 en total**).
  **Hecho 2026-10-09**: `test_hu_005.py` **3 PASS**; suite completa **118 PASS / 0 FAIL**
  (commit `accb304`).

- [x] **T16 — Evidencia QA y visual (plan §6.3, §8.12)** `[RF-1][RF-3][RF-4][RF-6][RNF-1][RNF-2][finalización]`
  Servidor (`python app.py`), recorrido manual: cambiar fecha (rápido, CL-2), cambiar
  servicio (CL-3), registrar cita y volver (RF-5), fecha sin horarios (RF-4) y hora
  ocupada marcada (RF-6); capturas CDP 1280/375 → `docs/evidencias/hu-005/`, informe
  `qa-hu-005.md` con PASS/FAIL por TC y veredicto (skill `pytest-qa`).
  Hecho cuando: existen `qa-hu-005.md` con veredicto **PASS** (16 TC en verde),
  `escritorio-1280.png` y `movil-375.png` verificadas por medidas programáticas, y
  `GET /citas` → 200 con el servidor en marcha (URL comunicada a la usuaria).
  **Hecho 2026-10-09**: `qa-hu-005.md` PASS (16/16 TC, suite 118 PASS, demo manual
  16/16); capturas `escritorio-1280.png` (1280×1539), `movil-375.png` (375×2726) y
  extra `dia-lleno-1280.png` (1280×1486, día 6 `is-full`), todas sin desborde;
  `GET /citas` → 200 con servidor en marcha.

- [x] **T17 — Commits por fase, Push y `MEMORY.md` (plan §8.13)** `[trazabilidad]`
  Commits separados por fase (spec+plan+task, contenido/espejo, persistencia, servicio,
  web, JS/CSS, tests, evidencia) con mensajes que citan HU-005/Spec 005.
  Hecho cuando: `git status` limpio, `git rev-parse HEAD` = `git rev-parse origin/feature/hu-005`
  y `MEMORY.md` registra HU-005 (estados por día, horas «Ocupado», endpoint
  `/citas/disponibilidad`).
  **Hecho 2026-10-09**: 11 commits de fase `e92112b`…`accb304` + evidencia/memoria
  `de2bdf4`; rama publicada `origin/feature/hu-005` con HEAD = remoto; `MEMORY.md`
  actualizado (bloque HU-005, decisiones y aprendizajes).

- [ ] **T18 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `docs/evidencias/hu-005/qa-hu-005.md`
  está marcado con fecha y la §7.2 del plan queda íntegramente en `[x]`.
