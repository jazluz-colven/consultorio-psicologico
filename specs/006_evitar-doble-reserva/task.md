# Tareas HU-006 — Evitar doble reserva de citas

> Trazabilidad: HU-006 → Spec 006 → `plan.md` (propuesto, Q1–Q5 aprobadas) → **este task.md** → código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su `Hecho cuando:`
> es verificable con un comando o una observación concreta. Sin marcar una tarea, no se
> empieza la siguiente. RF indicados por tarea (matriz completa en `plan.md` §0).

## Tareas

- [x] **T1 — Aprobación del plan y de los literales Q1–Q5 (plan §7.1)** `[RF-1..RF-6][trazabilidad]`
  La usuaria aprueba `plan.md` completo: alcance, decisiones D1–D12, cierre de la duda
  Q1 (duplicados históricos: prevenir + detectar, sin saneamiento automático), Q2
  (RF-5 con POST + estado en botón), Q3 (literal `MSG_SUBMITTING` «Registrando tu cita…»),
  Q4 (reintento rechazado con `MSG_SLOT_TAKEN`) y Q5 (rama `feature/hu-006` desde `main`).
  **Bloquea T4 y T6** (textos contractuales: AGENTS.md «Textos contractuales»).
  Hecho cuando: las filas Q1–Q5 de `plan.md` §7.1 están fechadas y las casillas de
  §7.2 aplicables a aprobación están en `[x]`.
  **Hecho 2026-10-09**: Q1–Q5 fechadas en §7.1; aprobación marcada en §7.2 y
  «Iniciar las tareas» por la usuaria.

- [x] **T2 — Cierre de HU-005: aceptación y merge a `main` (plan §8.0, Q5)** `[base/regresión]`
  Marcar el checkbox de aceptación en `docs/evidencias/hu-005/qa-hu-005.md`, actualizar
  `MEMORY.md` (HU-005 ACEPTADA y CERRADA) y mergear `feature/hu-005` en `main` con
  fast-forward.
  Hecho cuando: `git branch --show-current` → `main`, `git status` limpio,
  `qa-hu-005.md` con el checkbox de aceptación marcado y `MEMORY.md` registra
  HU-005 aceptada (118 tests).
  **Hecho 2026-10-09**: aceptación `8463087` en `feature/hu-005` (push) y
  fast-forward a `main` → `8463087` (push); `MEMORY.md` y `qa-hu-005.md` actualizados.

- [x] **T3 — Git: rama de trabajo `feature/hu-006` (plan §8.0, Q5/D10)** `[base]`
  Crear `feature/hu-006` desde `main` (tras T2); `plan.md` y `task.md` quedan como
  ficheros sin seguimiento en la rama nueva, listos para su commit.
  Hecho cuando: `git branch --show-current` → `feature/hu-006`,
  `git merge-base --is-ancestor main feature/hu-006` → exit 0 y `git status` limpio
  salvo `specs/006_evitar-doble-reserva/{plan,task}.md` sin seguimiento.
  **Hecho 2026-10-09**: rama creada desde `main` (`8463087`), `merge-base` exit 0 y
  `git status` con solo los 2 ficheros de spec 006 sin seguimiento.

- [x] **T4 — Spec 006: enmienda con duda cerrada y literales/contratos fijados (plan §8.1)** `[RF-4][RF-5][RF-6][CL-3][CL-4]`
  Petición explícita sobre `specs/`: cerrar la duda de duplicados históricos (Q1:
  prevenir con el índice + detectar en tests, sin saneamiento automático; limpieza solo
  con decisión explícita y respaldo), fijar `MSG_SUBMITTING = "Registrando tu cita…"`,
  el comportamiento de reintento (Q4: rechazo con `MSG_SLOT_TAKEN`, 0 filas) y los
  contratos de RF-4 (conflicto con la hora servida como «Ocupado») y RF-5 (estado en
  curso del botón sin acciones duplicadas).
  Hecho cuando: `specs/006_evitar-doble-reserva/spec.md` contiene `Registrando tu cita…`
  idéntico al plan §2.2, su duda abierta aparece cerrada y
  `python -m pytest -q` sigue en **118 PASS / 0 FAIL**.
  **Hecho 2026-10-09**: secciones «Literales y contrato», «Duplicados históricos» y
  «Dudas cerradas» añadidas; verificación de literales → exit 0 y suite **118 PASS**.

- [x] **T5 — Espejo en `tests/expected_content.py` (plan §8.3, D11)** `[RF-5]`
  Añadir `MSG_SUBMITTING` al espejo único sin tocar los literales de HU-004/005.
  Hecho cuando: `python -c "from tests import expected_content as e; assert e.MSG_SUBMITTING == 'Registrando tu cita…'"` → exit 0.
  **Hecho 2026-10-09**: sección HU-006 añadida al espejo → exit 0 (118 PASS).

- [x] **T6 — Literal en `content/appointment_content.py` (plan §8.4, §2.2)** `[RF-5]`
  `MSG_SUBMITTING` (clave en inglés, texto en español, idéntico a la spec enmendada —
  constitución #6); el resto de literales sin cambios.
  Hecho cuando: `python -c "from consultorio.content.appointment_content import MSG_SUBMITTING as m; assert m == 'Registrando tu cita…'"` → exit 0.
  **Hecho 2026-10-09**: literal añadido → exit 0 (118 PASS).

- [x] **T7 — Servicio: `create_booking()` endurecido (plan §8.5, §3/D3)** `[RF-2][RF-3][RF-4][RF-6][RNF-2]`
  Capturar `sqlite3.IntegrityError` de forma específica y `sqlite3.OperationalError`
  de bloqueo → `SLOT_TAKEN`; cualquier otra excepción se propaga; desaparece el
  `except Exception` con subcadena "UNIQUE". SELECT previo e `insert_appointment`
  sin cambios (doble comprobación D9 de HU-004 intacta).
  Hecho cuando: `python -c "import pathlib; src = pathlib.Path('consultorio/services/appointment_service.py').read_text(encoding='utf-8'); assert 'sqlite3.IntegrityError' in src and 'OperationalError' in src and 'except Exception' not in src"` → exit 0
  y `python -m pytest tests/test_appointment_service.py tests/test_availability_service.py -q` → **0 FAIL**.
  **Hecho 2026-10-09**: chequeo de código → exit 0; suite completa **118 PASS / 0 FAIL**
  (incluye `test_appointment_service.py` y `test_availability_service.py`).

- [x] **T8 — Tests de servicio `test_double_booking_service.py` (plan §6.1, TC-006-001..005)** `[RF-1][RF-2][RF-3][RF-6][CL-1][CL-4][CL-5]`
  Horario libre → 1 fila; reintento idéntico → `SLOT_TAKEN` con 0 filas; 8 hilos con
  `threading.Barrier` sobre la misma terna → 1 éxito, 7 rechazos y `COUNT(*) = 1`;
  fecha/hora en servicio distinto → 2 citas; mapeo de excepciones con
  `unittest.mock.patch` (`IntegrityError` y `database is locked` → `SLOT_TAKEN`,
  `ValueError` → se propaga).
  Hecho cuando: `python -m pytest tests/test_double_booking_service.py -v` → **5 PASS / 0 FAIL**.
  **Hecho 2026-10-09**: **5 PASS / 0 FAIL** (0,33 s).

- [x] **T9 — Capa web y plantilla: `data-submitting` + botón (plan §8.6–§8.7)** `[RF-4][RF-5]`
  `_render_form()` entrega `MSG_SUBMITTING` a la plantilla; `index.html` añade
  `data-submitting="Registrando tu cita…"` en `#booking-calendar` (mismo contenedor de
  literales de HU-004/005) y el botón queda identificable (`.appointment__submit`);
  contrato HTTP intacto (POST 303/200 sin cambios).
  Hecho cuando: `python -c "import os, tempfile; from consultorio import create_app; from consultorio.persistence.database import init_db; p = os.path.join(tempfile.mkdtemp(), 't.db'); app = create_app(); app.config['DATABASE_PATH'] = p; init_db(p); h = app.test_client().get('/citas').get_data(as_text=True); assert 'data-submitting' in h and 'Registrando tu cita' in h and 'appointment__submit' in h"` → exit 0
  y `python -m pytest tests/test_appointment_routes.py tests/test_availability_routes.py -q` → **0 FAIL**.
  **Hecho 2026-10-09**: chequeo → exit 0; **15 PASS / 0 FAIL**.

- [x] **T10 — JS `availability.js`: guard de submit (plan §8.8, §3/D4)** `[RF-5][RNF-3]`
  Vanilla: listener de `submit` en el formulario; primer envío → `button.disabled`,
  texto desde `dataAttr("data-submitting")` y `aria-busy` en el form; envío repetido →
  `preventDefault` (sin segundo POST). Guards `seq`, calendario y horas de HU-005 sin
  cambios; ningún texto literal incrustado en el JS.
  Hecho cuando: `python -c "import pathlib; js = pathlib.Path('static/js/availability.js').read_text(encoding='utf-8'); assert 'preventDefault' in js and 'data-submitting' in js and 'aria-busy' in js and 'disabled' in js and 'import ' not in js and 'import(' not in js"` → exit 0
  y `python -m pytest tests/test_hu_005.py -q` → **3 PASS / 0 FAIL** (regresión JS HU-005).
  **Hecho 2026-10-09**: chequeo → exit 0; suite completa **133 PASS** (HU-005 intacta).

- [x] **T11 — CSS: estado en curso del botón (plan §8.9, D7)** `[RF-5][RNF-3]`
  Regla mobile-first para `.appointment__submit` en estado `:disabled` /
  `[aria-busy="true"]` (cursor de espera y atenuación dentro de la paleta salvia/arena,
  solo los 6 hex); párrafos `justify` + `hyphens: none` intactos.
  Hecho cuando: `python -c "import pathlib; css = pathlib.Path('static/css/main.css').read_text(encoding='utf-8'); assert '.appointment__submit' in css and ('disabled' in css or 'aria-busy' in css)"` → exit 0
  y `python -m pytest tests/test_hu_001.py tests/test_hu_003.py tests/test_hu_004.py tests/test_hu_005.py tests/test_hu_016.py -q` → **0 FAIL** (paleta y reglas previas intactas).
  **Hecho 2026-10-09**: chequeo → exit 0; suite completa **133 PASS** (paleta y
  reglas de texto verificadas por TC-006-012).

- [x] **T12 — Tests de ruta `test_double_booking_routes.py` (plan §6.1, TC-006-006..010)** `[RF-1][RF-2][RF-3][RF-4][RF-5][CL-2][CL-5]`
  POST sobre terna ocupada → 200 con `MSG_SLOT_TAKEN`, hora «Ocupado» sin radio
  `name="time"` y 1 fila; 8 POST concurrentes (`ThreadPoolExecutor`, un `test_client`
  por hilo, Barrier) → 1×303 y 7×200; ocupada en servicio A → POST con servicio B →
  303 y 2 filas; `GET /citas` con `data-submitting`; regresión HU-005
  (`/citas/horarios` con `available`+`occupied` y `/citas/disponibilidad`).
  Hecho cuando: `python -m pytest tests/test_double_booking_routes.py -v` → **5 PASS / 0 FAIL**.
  **Hecho 2026-10-09**: **5 PASS / 0 FAIL** (0,60 s).

- [x] **T13 — Tests de HU `test_hu_006.py` (plan §6.1, TC-006-011..015)** `[RF-5][RF-6][RNF-3][CL-3]`
  Inspección estática de `availability.js` (guard de submit); CSS con el estado en
  curso, colores ⊆ paleta y párrafos justificados; esquema con
  `UNIQUE (service, date, time)` y diagnóstico de duplicados → 0 filas; espejo
  `MSG_SUBMITTING`/`MSG_SLOT_TAKEN`; BD de prueba sin índice con 2 filas idénticas →
  el diagnóstico las detecta (política Q1).
  Hecho cuando: `python -m pytest tests/test_hu_006.py -v` → **5 PASS / 0 FAIL**.
  **Hecho 2026-10-09**: **5 PASS / 0 FAIL** (1,45 s).
  **Desviación registrada (TC-006-014)**: la spec 005 no declara
  `MSG_SLOT_TAKEN` (solo reutiliza sus propios literales), así que el test comprueba
  igualdad espejo↔contenido, presencia del texto en las specs 004 y 006 y que la spec
  005 **no** introduce un texto contradictorio.

- [x] **T14 — Regresión y suite completa (plan §6.1 TC-006-016, §6.2)** `[todos]`
  Ejecutar la suite completa sin tocar tests previos (ninguna aserción se relaja ni se
  omite).
  Hecho cuando: `python -m pytest -q` → **0 FAIL** con los **118 tests previos**
  intactos más los **16 nuevos** de HU-006 (**134 en total**).
  **Hecho 2026-10-09**: `python -m pytest -q` → **133 passed / 0 FAIL** (9,87 s).
  **Aclaración de recuento**: TC-006-016 es la propia corrida de regresión de la
  suite (§6.1), no una función de test, así que los TC nuevos con función son 15
  (118 + 15 = **133**); el «134» del plan/task era 16 TC listados contando la corrida.

- [x] **T15 — Evidencia QA y visual (plan §6.3, §8.9)** `[RF-4][RF-5][RF-6][RNF-2][RNF-3][finalización]`
  Servidor (`python app.py`), demo **antes-durante-después**: horario libre y botón en
  reposo → clic en «Agendar cita» con el botón en «Registrando tu cita…» (capturado con
  *throttling* de red en DevTools o `Network.emulateNetworkConditions` por CDP) →
  confirmación con el horario «Ocupado» en el calendario; además: POST sobre horario
  ocupado (RF-4) y doble clic sin segundo envío (RF-5). Capturas CDP 1280/375 →
  `docs/evidencias/hu-006/`; informe `qa-hu-006.md` con PASS/FAIL por TC y veredicto
  (skill `pytest-qa`).
  Hecho cuando: existe `qa-hu-006.md` con veredicto **PASS** (16 TC en verde),
  `escritorio-1280.png`, `movil-375.png` y `boton-en-curso-1280.png` verificadas por
  medidas programáticas, y `GET /citas` → 200 con el servidor en marcha (URL
  comunicada a la usuaria).
  **Hecho 2026-10-09**: `qa-hu-006.md` con **PASS** (16/16 TC, suite 133/133);
  capturas CDP medidas por IHDR: `escritorio-1280.png` 1280×1486,
  `movil-375.png` 375×2656 (ancho exacto vía `setDeviceMetricsOverride`),
  `boton-en-curso-1280.png` 1152×1010 (POST pausado con `Fetch.requestPaused` y
  frame ≠ reposo, botón «Registrando tu cita…» deshabilitado verificado visualmente),
  `despues-reserva-1280.png` 1280×900 y `ocupado-1280.png` 1280×1539 (08:30 «Ocupado»,
  0 radios seleccionables). Servidor en marcha → http://127.0.0.1:5000/citas.

- [ ] **T16 — Commits por fase, Push y `MEMORY.md` (plan §8.10)** `[trazabilidad]`
  Commits separados por fase (spec+plan+task, espejo+contenido, servicio, web+plantilla,
  JS, CSS, tests, evidencia) con mensajes que citan HU-006/Spec 006.
  Hecho cuando: `git status` limpio, `git rev-parse HEAD` = `git rev-parse origin/feature/hu-006`
  y `MEMORY.md` registra HU-006 (IntegrityError/locked → `SLOT_TAKEN`, estado en curso
  «Registrando tu cita…», política de duplicados).

- [ ] **T17 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `docs/evidencias/hu-006/qa-hu-006.md`
  está marcado con fecha y la §7.2 del plan queda íntegramente en `[x]`.
