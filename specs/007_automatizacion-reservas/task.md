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

- [x] **T13 — Commits por fase, Push y `MEMORY.md` (plan §8.10)** `[trazabilidad]`
  Commits separados por fase (spec+plan+task → config+persistencia+contenido →
  servicio+disparo+web → tests → evidencia+MEMORY) con mensajes que citan
  HU-007/Spec 007.
  Hecho cuando: `git status` limpio, `git rev-parse HEAD` =
  `git rev-parse origin/feature/hu-007` y `MEMORY.md` registra HU-007
  (`appointment.confirmed`, `automation_events`, aislamiento, sin PII).
  **Hecho 2026-10-10**: 5 commits — `4735576` (spec+plan+task),
  `d1a1bd5` (config+persistencia+contenido), `31367d0` (servicio+disparo+web),
  `138b547` (tests) y `9d039a9` (evidencia+MEMORY). HEAD =
  `origin/feature/hu-007` = `9d039a9`; `MEMORY.md` registra HU-007.

- [x] **T14 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `docs/evidencias/hu-007/qa-hu-007.md`
  está marcado con fecha y la §7.2 del plan queda íntegramente en `[x]`.
  **Hecho 2026-10-10**: aceptada por la usuaria («Puedes cerrar la HU. Y realizar
  el merge»); checkbox marcado y §7.2 del plan íntegra en `[x]`; merge a `main`.

- [x] **T15 — Enmienda 2 (Q7/D14): cabecera de autenticación `AUTOMATION_WEBHOOK_AUTH_HEADER`** `[RF-2][RF-6][RNF-1][trazabilidad]`
  Tras el 403 real del webhook n8n de la usuaria: enmienda de la spec 007 (§Envío)
  y del plan (§2.4/§3/D14/Q7/§6.1 TC-007-014/§4.1); implementación en `Config`
  (env `AUTOMATION_WEBHOOK_AUTH_HEADER`, vacía por defecto), `_post_webhook()`
  (partition «Nombre: valor» → cabecera) y paso por `create_booking()` y la capa
  web. **El token es secreto de entorno: nunca en el repo, docs ni tests** (solo
  `X-Test-Token: fake-token` en TC-007-014).
  Hecho cuando: spec y plan enmendados, `python -m pytest -q` → **147 PASS /
  0 FAIL** y TC-007-014 PASS.
  **Hecho 2026-10-10**: enmienda + implementación + TC-007-014; suite
  **147 PASS / 0 FAIL**; prueba live contra `webhook-test/hu-007-cita-creada`
  con la cabecera → **HTTP 200** «Workflow was started»; evidencia en
  `qa-hu-007.md` (sección enmienda 2).

---

## Enmienda 2026-11-01 — Tareas RF-8..RF-13: borrado del evento de Google Calendar en n8n

> **Estado: `IMPLEMENTADO — VALIDADO TÉCNICAMENTE; PENDIENTE DE ACEPTACIÓN
> FUNCIONAL` (2026-11-04).** La spec 007 está aprobada (enmienda 2026-10-23) y
> RF-8..RF-13 quedan implementados en el workflow **v5**; el plan §9 y estas
> tareas T16–T22 fueron aprobados y ejecutados. **T16–T21 cerradas**; **T22
> cerrada salvo la aceptación funcional de la usuaria**. Trazabilidad:
> **HU-007 → Spec 007 RF-8..RF-13 → `plan.md` §9 → estas tareas → workflow n8n →
> evidencia E2E → commit**. Las tareas T1–T15 quedan **cerradas y sin reabrir**.
> Cada tarea dura **20–30 min**, se ejecuta **en orden** y su `Hecho cuando:` es
> verificable con un comando o una observación concreta. **Sin marcar una tarea
> no se empieza la siguiente.**
> **Roles**: `[usuaria]` (UI de n8n/data table), `[implementador]` (JSON),
> `[coordinador]` (pre-check, E2E, evidencia, memoria). El backend **no cambia**:
> no se toca código ni tests de la app. La fase suma **7 tareas** (T16–T22, ≤10;
> no requiere división adicional).
> Evidencia de la fase en `docs/evidencias/hu-007/enmienda-2026-11-01/`; artefacto
> del workflow en `docs/workflows/hu-007/` (plan §9.9). Sin secretos ni datos de
> pacientes.
> **Nota de corrección 2026-11-02 (corrección 3, sustituye a las correcciones
> 1 y 2 en la rama de error; **aprobada 2026-11-04, superada en la verificación
> por la corrección 4**):** el nodo
> `googleCalendar` **oculta el código HTTP**: el error es
> `Your request is invalid or could not be processed by the service`, sin 4xx/5xx
> en los campos ni en la serialización (`calendar_http_code: null`). Interpretar
> el texto no permite distinguir 404 de 400/403, así que el JSON v3 tampoco
> cumple RF-10. Decisión aprobada por la usuaria (2026-11-02): **verificar la
> existencia del evento** tras un borrado fallido (`Verificar evento` +
> `Preparar borrado fallido` + `Preparar no encontrado`, plan §9.5.6 / D-E13).
> **T18** generó el JSON **v4** (47 nodos, `Clasificar resultado de Calendar` sin
> cambios) y **T20-B se repite sobre la cita 32** verificando las dos ramas.
> Ni la ejecución 13 ni los intentos con los JSON v2/v3 cuentan como PASS.
> **Histórico: sustituido por el v5 (48 nodos) de la corrección 4.**
> **Nota de corrección 4 (2026-11-02; aprobada 2026-11-04, sustituye a la
> corrección 3 en la verificación):** el JSON v4 tampoco cumple RF-10.
> Con el evento borrado a mano (cita 32), `Verificar evento` (`events.get`)
> **devuelve el evento** con `status: "cancelled"` y el mismo `id`: Google lo
> marca como cancelado **antes de purgarlo**, aunque ya no aparezca en el
> calendario visual. La **mera existencia no basta**: se añade
> `¿Evento cancelado?` (`n8n-nodes-base.if` 2.4, `combinator: "or"`, dos
> `string equals` sobre
> `={{ ($json.status ?? '').toString().toLowerCase() }}` frente a `cancelled` y
> `canceled`): true → `Preparar no encontrado`; false → `Preparar borrado
> fallido`; `Verificar evento` error → `Preparar no encontrado` (sin cambios).
> **T18** genera el JSON **v5** (**48 nodos**); **T19** espera **48 nodos**;
> **T20-B** verifica las **tres ramas** (evento cancelado → `not_found`; error
> 404 → `not_found`; evento confirmado → `failed`). Estado: **PASS sobre el v5**.
> Registro: `docs/defectos/D-007-01.md` (`CORREGIDO — PENDIENTE DE VALIDACIÓN`).

- [x] **T16 — Pre-check: el export entregado es el workflow activo en producción** `[base][RF-8]` `[coordinador]`
  Depende de: aprobación del plan §9 y de las tareas T16–T22; T15 cerrada.
  Verificar en la **UI de n8n** que el workflow `HU-007 - Integración de citas
  con n8n` (id `v0WykUcKCzccxfyI`) está **activo** y recibe el webhook de
  producción `POST /webhook/hu-007-cita-creada`. Descargar un export **fresco**
  y compararlo con el archivo entregado (`C:\Users\Jaz\Downloads\HU-007 -
  Integración de citas con n8n.json`): 42 nodos, conexiones, data table
  `t4GENwUkjVodM5cg`, `webhookId 8889e9dd-ca30-4548-9505-95336cc04b51` y
  referencias de credenciales. Registrar `versionId` y la hora del export.
  **`active:false` en el export no prueba inactividad**: es un artefacto de la
  serialización. Si hay diferencias, el export entregado está desactualizado →
  usar el export fresco como base de T18 y decirlo en la nota.
  Hecho cuando: la nota de T16 registra workflow id, `versionId`, 42 nodos,
  confirmación de «activo» en la UI y el resultado de la comparación
  (sin diferencias / export fresco adjunto).
  Evidencia esperada: `precheck.md` en la carpeta de evidencia + el export
  fresco (o su hash si es idéntico).
  **Hecho 2026-11-04:** `precheck.md` **PASS estructural** (2026-11-01):
  workflow `v0WykUcKCzccxfyI`, `versionId 279f3ea1-f444-410a-afc8-24f492ca18dc`,
  42 nodos, export vigente confirmado en la UI y sin secretos ni PII. La UI
  confirmó el workflow **desactivado** durante las modificaciones, con el export
  del 2026-10-30 como base válida para T18.

- [x] **T17 — Crear en la data table las columnas `cancellation_status` y `cancellation_detail`** `[RF-12][RF-8][RF-11]` `[usuaria]`
  Depende de: T16.
  En n8n → **Data tables** → `HU007EventosProcesados` (id `t4GENwUkjVodM5cg`),
  siguiendo el checklist exacto del plan §9.4.3:
  1. `cancellation_status` — **String/Texto**, default **`none`**, no obligatoria.
  2. `cancellation_detail` — **String/Texto**, default **vacío**, no obligatoria.
  3. Nombres exactos (minúsculas y guion bajo); no renombrar, borrar ni cambiar
     el tipo de las 12 columnas existentes.
  4. Filas existentes: `none` / vacío (si la UI no aplica el default, el vacío
     se interpreta como `none`).
  5. Exportar el CSV de la data table y comprobar que las cabeceras incluyen las
     dos columnas nuevas.
  Hecho cuando: las dos columnas existen con nombre, tipo y default exactos; el
  CSV exportado incluye ambas cabeceras; ninguna columna existente cambió.
  Evidencia esperada: `datatable-antes.csv` en la carpeta de evidencia + captura
  opcional de la configuración de columnas.
  **Hecho 2026-11-04:** data table `HU007EventosProcesados` con **14 columnas**
  (12 existentes + `cancellation_status` + `cancellation_detail`), verificadas en
  los CSV del v5 (`datatable-e2e-A-B-v5-2026-11-04.csv` y
  `datatable-e2e-D-E-v5-2026-11-04.csv`, cabeceras con ambas columnas) y en el
  informe QA §1. `datatable-antes-reset.csv` **no** se usa como evidencia
  (export inválido por caché; QA §5.7).

- [x] **T18 — Generar el JSON parcheado del workflow (sin secretos)** `[RF-8][RF-9][RF-10][RF-11][RF-12][RF-13]` `[implementador]`
  Depende de: T16 (export base) y plan §9 aprobado.
  Generar el JSON según plan §9.5, **preservando** `id`, `type`, `typeVersion`,
  `position`, `parameters` no afectados, `credentials` y `webhookId` de los
  nodos existentes; nodos nuevos con **UUID nuevos** (también los `id` internos
  de condiciones/asignaciones). Cambios obligatorios:
  - Entrada común: `Enrutar acciones tras registro` [3] y `Enrutar reintento por
    tipo` [2] → `Preparar cancelación`; `Preparar cancelación` → `Consulta`.
  - Nodos nuevos: `Preparar cancelación`, `¿Fila de creación encontrada?`,
    `Marcar sin fila de creación`, `¿Cancelación ya completada?`,
    `Marcar sin calendar_event_id - creación`, `Marcar sin calendar_event_id -
    evento`, `Clasificar resultado de Calendar` (código del plan §9.5.5),
    `¿Borrado o ya eliminado?`, `Marcar cancelación fallida - creación`.
  - Repurposición: `Update row(s)2` quita `processing_status` del `columns.schema`
    (`removed:true`) y escribe `cancellation_status='completed'`, `cancellation_detail` y
    `calendar_event_id=''`; `Update row(s)3` y `Marcar cancelación completada`
    filtran por `$('Preparar cancelación').first().json.event_row_id`;
    `Marcar cancelación completada`, `Marcar sin fila de creación` y `Marcar sin
    calendar_event_id - evento` con `onError: continueErrorOutput` →
    `Update row(s)3`.
  - **Corrección D-007-02 (2026-11-02, sustituye a D-007-01):** `Elimina cita`
    se mantiene como **`n8n-nodes-base.googleCalendar`** con la configuración
    del nodo v1 de
    `docs/workflows/hu-007/n8n-hu-007-integracion-citas-2026-11-01.json`
    (`typeVersion: 1.3`, `operation: delete`, `calendar` como resource locator
    `ingjazar@gmail.com` / `mode: list` / `cachedResultName: ingjazar@gmail.com`,
    `eventId: ={{ $json.calendar_event_id }}`, `options: {}`), `credentials`
    intactas (`googleCalendarOAuth2Api`, id `Jzc9xfMvMH5AeRBN`, nombre
    `Google Calendar account`), `onError: continueErrorOutput` y
    `retryOnFail: false`. Motivo: n8n Cloud prohíbe usar la credencial OAuth2 de
    Google Calendar en nodos HTTP Request/GraphQL
    (`This credential is configured to prevent use within an HTTP Request or
    GraphQL node`); la opción A **no es viable**.
  - **Corrección 3 (2026-11-02, D-E13; superada en la conexión de éxito por la
    corrección 4):** añadir los **tres nodos de
    verificación de existencia** y recablear la salida de error de `Elimina cita`
    (plan §9.5.6):
    - `Verificar evento` (`n8n-nodes-base.googleCalendar`, `typeVersion: 1.3`):
      `operation: get`, `calendar` como resource locator `ingjazar@gmail.com` /
      `mode: list` / `cachedResultName: ingjazar@gmail.com`,
      `eventId: ={{ $json.calendar_event_id }}`, `options: {}`, `credentials`
      `googleCalendarOAuth2Api` (id `Jzc9xfMvMH5AeRBN`, nombre
      `Google Calendar account`), `onError: continueErrorOutput`,
      `retryOnFail: false`; `position` libre a la derecha de `Elimina cita`.
    - `Preparar borrado fallido` (`n8n-nodes-base.set`, tv 3.5,
      `includeOtherFields: true`): `calendar_ok=false`,
      `calendar_http_code=null`, `cancellation_detail="http_error_unknown"`.
    - `Preparar no encontrado` (`n8n-nodes-base.set`, tv 3.5,
      `includeOtherFields: true`): `calendar_ok=true`, `calendar_http_code=null`,
      `cancellation_detail="not_found"`.
    - **Retirar** la conexión `Elimina cita` salida 1 → `Clasificar resultado de
      Calendar` y **añadir** las cinco del plan §9.5.2:
      `Elimina cita` (error) → `Verificar evento`;
      `Verificar evento` (éxito) → `Preparar borrado fallido`;
      `Preparar borrado fallido` → `Marcar cancelación fallida - creación`;
      `Verificar evento` (error) → `Preparar no encontrado`;
      `Preparar no encontrado` → `¿Borrado o ya eliminado?`.
    - `Clasificar resultado de Calendar` **no cambia** y solo recibe la salida 0
      (éxito) de `Elimina cita`.
  - **Corrección 4 (2026-11-02, D-E14):** añadir `¿Evento cancelado?`
    (`n8n-nodes-base.if`, `typeVersion: 2.4`) con `combinator: "or"` y **dos**
    condiciones `string equals`:
    `leftValue: ={{ ($json.status ?? '').toString().toLowerCase() }}` frente a
    `cancelled` y frente a `canceled`; `options: {}`. Recablear:
    - **Retirar** `Verificar evento` (éxito) → `Preparar borrado fallido`.
    - **Añadir** `Verificar evento` (éxito) → `¿Evento cancelado?`;
      `¿Evento cancelado?` true → `Preparar no encontrado`;
      `¿Evento cancelado?` false → `Preparar borrado fallido`.
    - `Verificar evento` (error) → `Preparar no encontrado` **sin cambios**.
  - `Clasificar resultado de Calendar` usa el `jsCode` **literal** del plan
    §9.5.5 (lecturas estructuradas + string legacy + error serializado), sin
    modificaciones.
  - Eliminar los 7 nodos de la rama de reintento duplicada: `Get row(s)1`,
    `¿Cita ya cancelada?`, `¿Existe evento de Calendar en reintento?`,
    `Elimina cita - Reintento`, `Actualizar cita cancelada - Reintento`,
    `Marcar cancelación completada - Reintento`, `Marcar cancelación fallida -
    Reintento` (y sus conexiones).
  - En cada nodo data table que escriba `cancellation_status`/
    `cancellation_detail`, añadir la entrada correspondiente en `columns.schema`
    con `removed:false`.
  - Archivo final: `active:false`, `pinData` vacío, sin tokens/cabeceras de
    autenticación; **nueva versión**
    `docs/workflows/hu-007/n8n-hu-007-integracion-citas-2026-11-02-v5.json`
    (se conservan `...-v4.json`, `...-v3.json`, `...-2026-11-02.json` y
    `...-2026-11-01.json` como histórico; ninguno de los anteriores se activa).
  Hecho cuando: el JSON parsea; tiene **48 nodos** (42 − 7 + 9 + 3 + 1); los 7
  nodos eliminados no aparecen; los 13 nuevos tienen UUID únicos; toda conexión
  apunta a un nodo existente; `Elimina cita` es `googleCalendar` `typeVersion 1.3`
  con los parámetros del v1, `onError: continueErrorOutput` y
  `retryOnFail: false`; **`Verificar evento` es `googleCalendar` `operation: get`**
  con `eventId: ={{ $json.calendar_event_id }}`, `onError: continueErrorOutput` y
  `retryOnFail: false`; **`¿Evento cancelado?` es `n8n-nodes-base.if`
  `typeVersion: 2.4`** con `combinator: "or"` y las **dos** condiciones
  `string equals` sobre `={{ ($json.status ?? '').toString().toLowerCase() }}`
  (`cancelled` / `canceled`); `Preparar borrado fallido` y `Preparar no
  encontrado` son `set` tv 3.5 con `includeOtherFields: true` y los tres campos
  exactos; `Verificar evento` salida 0 apunta a `¿Evento cancelado?`, sus salidas
  true/false apuntan a `Preparar no encontrado` / `Preparar borrado fallido`, y
  `Verificar evento` salida 1 apunta a `Preparar no encontrado`;
  `Elimina cita` salida 1 apunta a `Verificar evento` y **no** a
  `Clasificar resultado de Calendar`; `Clasificar resultado de Calendar`
  conserva el `jsCode` idéntico al plan §9.5.5 **sin cambios**; los nodos que
  escriben las columnas nuevas las incluyen en `schema`; `active` es `false`; no
  hay `pinData` ni secretos; el resumen de cambios coincide con plan
  §9.5.1–§9.5.2 y §9.5.6.
  Evidencia esperada: el JSON versionado + salida de validación estructural
  (recuento de nodos, ids, conexiones, tipo/config de `Elimina cita` y ausencia
  de secretos) + resumen del diff.
  **Hecho 2026-11-04:** JSON **v5**
  (`docs/workflows/hu-007/n8n-hu-007-integracion-citas-2026-11-02-v5.json`) con
  **48 nodos** y sha256
  `8918306709c0e13132861cea04cc2d7ff98dded6d7f005c94e4f5e02f3dfb766`;
  `Elimina cita` `googleCalendar` 1.3, `Verificar evento` `get`,
  `¿Evento cancelado?` If 2.4 con las dos condiciones, `active:false`, sin
  `pinData` ni secretos. Las cinco versiones (v1–v5) están conservadas en
  `docs/workflows/hu-007/` con sus sha256 en el informe QA §1.

- [x] **T19 — Importar el workflow inactivo y revisar mapeos y credenciales** `[trazabilidad][RF-8..RF-13]` `[usuaria][implementador]`
  Depende de: T17 y T18.
  Importar el JSON de T18 **como workflow nuevo** (no sobrescribir el activo).
  Comprobar: inactivo; **48 nodos**; data table `HU007EventosProcesados`; las
  credenciales `Header Auth account`, `SMTP account` y `Google Calendar account`
  resuelven sin avisos; `cancellation_status`/`cancellation_detail` aparecen en
  los nodos data table que las escriben; expresiones sin errores; path
  `hu-007-cita-creada` y `webhookId` conservados. **No activar todavía.**
  Hecho cuando: el workflow importado está inactivo, con **48 nodos**, 0 avisos
  de credencial faltante, columnas nuevas visibles en los mapeos y una nota con
  el resultado (y captura opcional).
  Evidencia esperada: nota de importación/revisión + captura opcional del
  workflow importado y de los mapeos.
  **Hecho 2026-11-04:** importado inactivo y activado en n8n Cloud; **48 nodos**;
  data table y credenciales resueltas; columnas nuevas visibles en los mapeos.
  Validación registrada en `D-007-01` §8 (T19) y en `ejecuciones.md`.

- [x] **T20 — Activar (swap) y E2E: cancelación normal, ya eliminado y reintento tras completar** `[RF-8][RF-9][RF-10][RF-13]` `[coordinador][usuaria]`
  Depende de: T19.
  Precondiciones: backend **local** (`python app.py`) con
  `AUTOMATION_WEBHOOK_URL` apuntando a la URL de **producción**
  (`/webhook/hu-007-cita-creada`, no `webhook-test`) y
  `AUTOMATION_WEBHOOK_AUTH_HEADER` tomada del entorno (nunca en la evidencia);
  sin tocar Render ni `DATABASE_PATH`. Desactivar el workflow anterior y
  activar la copia importada (solo uno activo con el mismo path).
  Ejecutar los escenarios A–C de plan §9.6/§9.7.2:
  - **A** cancelación normal: el evento se borra de Calendar; C queda
    `cancellation_status='completed'`, detalle vacío, `calendar_event_id=''`,
    `processing_status` de creación intacto; X `completed`.
  - **B** «ya eliminado»: borrar a mano el evento en Calendar antes de cancelar →
    `Elimina cita` (`googleCalendar`, `typeVersion 1.3`) entra en error;
    `Verificar evento` (plan §9.5.6) devuelve el evento con
    `status: "cancelled"` (o falla con 404 si ya no lo devuelve) →
    `¿Evento cancelado?` true → `Preparar no encontrado` → `completed` +
    `not_found`, sin `failed`; `calendar_event_id=''`. No se exige código HTTP en
    el error (el nodo lo oculta: `calendar_http_code: null`).
    **B se repite tras la corrección 4:** se ejecuta sobre la **cita 32** (filas
    ya existentes en estado `failed`) reenviando
    `appointment.cancelled:32:v1`, lo que valida el E2E-B y la rama de reintento
    a la vez, y debe comprobar **las tres ramas**:
    - **(a) evento cancelado**: `Verificar evento` devuelve el evento con
      `status: cancelled` → `¿Evento cancelado?` true → C queda `completed` +
      `not_found` + `calendar_event_id=''`.
    - **(b) error 404**: `Verificar evento` falla sin devolver evento →
      `Preparar no encontrado` → C queda `completed` + `not_found` +
      `calendar_event_id=''`.
    - **(c) evento confirmado**: el borrado falla dejando el evento `confirmed` →
      `Verificar evento` lo devuelve → `¿Evento cancelado?` false →
      `Preparar borrado fallido` → C queda `failed` + `http_error_unknown` y
      `calendar_event_id` sin cambios.
    Ni la ejecución n8n **13** (D-007-01), ni los intentos con los JSON **v2**
    (HTTP Request), **v3** (error genérico) ni **v4** (existencia) cuentan como
    PASS; el PASS válido es la ejecución con el JSON **v5** (corrección 4, T18).
  - **C** reintento tras completar: poner la fila X de una cita de prueba en
    `failed` y reenviar el mismo payload → la guarda `¿Cancelación ya
    completada?` cierra X en `completed` y **no** se ejecuta `Elimina cita`.
  Comprobar RF-13: la rama de `appointment.cancellation_email` no invoca
  `Elimina cita`.
  Hecho cuando: A, B (repetido sobre la cita 32 con el JSON v5, con las **tres
  ramas** (a), (b) y (c)) y C dan PASS con estados de §9.6, IDs de ejecución de
  n8n registrados (el de B con el JSON v5, posterior a la corrección) y evidencia
  del calendario (A/B: evento ausente o cancelado; C: sin borrado nuevo). Si (a)
  o (b) devuelven `failed`, o (c) devuelve `not_found`/`completed`, **no se
  declara PASS**: se revisan `Verificar evento`/`¿Evento cancelado?` y se repite.
  Evidencia esperada: `datatable-despues.csv`, `ejecuciones.md` con IDs de A/B/C
  (incluido el B con el JSON v5 sobre la cita 32 y sus ramas (a)/(b)/(c)) y el
  detalle de la fila X/C por escenario.
  **Hecho 2026-11-04:** **A, B y C PASS** sobre el v5 (B sobre la cita 32:
  evento ya borrado → `status: cancelled` → `completed` / `not_found` / id
  vacío; C: guard sin llamada a Calendar). `ejecuciones.md` registra la serie del
  2026-11-04 (02:00:58–02:19:30) y los CSV
  `datatable-e2e-A-B-v5-2026-11-04.csv` y `datatable-e2e-B-fallido.csv`.

- [x] **T21 — E2E de los casos `skipped` (RF-11): sin fila de creación y sin `calendar_event_id`** `[RF-11][RF-12]` `[coordinador][usuaria]`
  Depende de: T20 (workflow activo y cadena verificada).
  - **D — sin fila de creación**: enviar a mano a la URL de producción un
    payload válido `appointment.cancelled:999999:v1` (id inexistente, 10 campos
    del contrato, sin PII) con la cabecera de auth del entorno. Esperado: 202,
    fila X insertada, `cancellation_status='skipped'` +
    `cancellation_detail='no_creation_record'`, `processing_status='completed'`,
    **0 llamadas a Calendar** y **el caso no queda en `received`**.
  - **E — sin `calendar_event_id`**: elegir una cita de prueba cuya fila C tenga
    `calendar_event_id` vacío (o vaciarlo en una fila de prueba) y cancelarla.
    Esperado: C `skipped` + `missing_calendar_event_id`; X `completed`;
    **0 llamadas a Calendar**; nunca `failed` ni «eliminado».
  Hecho cuando: D y E dan PASS con estados de §9.6, IDs de ejecución y 0
  llamadas a Google Calendar; ambos casos quedan registrados y localizables por
  `cancellation_status='skipped'`.
  Evidencia esperada: filas de D/E en `datatable-despues.csv` + IDs de
  ejecución en `ejecuciones.md`.
  **Hecho 2026-11-04:** **D y E PASS** sobre el v5: D
  (`appointment.cancelled:999:v1`) → `skipped` / `no_creation_record`; E (cita
  34, creación sin `calendar_event_id`) → `skipped` /
  `missing_calendar_event_id`; ambas con **0 llamadas a Calendar**, registradas
  en `datatable-e2e-D-E-v5-2026-11-04.csv` y `ejecuciones.md` (02:13:32 y
  02:19:29).

- [ ] **T22 — Regresión, evidencia QA, versionado y `MEMORY.md`** `[finalización][trazabilidad]` `[coordinador]`
  Depende de: T20 y T21.
  Ejecutar `python -m pytest -q` (backend sin cambios; registrar el conteo real
  y compararlo con el baseline de `MEMORY.md`, 302 PASS tras D-010-01) y
  `git diff --name-only main...HEAD` (sin archivos de `consultorio/` ni `tests/`).
  Crear `docs/evidencias/hu-007/enmienda-2026-11-01/qa-hu-007-enmienda-2026-11-01.md`
  con: matriz RF-8..RF-13, escenarios A–E (y F si se ejecutó) con PASS/FAIL, IDs de ejecución,
  enlaces a `datatable-antes.csv`/`datatable-despues.csv`, decisiones D1–D4,
  cuestiones abiertas OQ-1..OQ-6 y veredicto (`PASS` / `PARCIAL` / `FAIL`).
  Versionar el JSON en `docs/workflows/hu-007/` (plan §9.9), actualizar
  `MEMORY.md` (estado de la enmienda, decisiones, pendientes) y hacer commits de
  docs/artefactos que citen HU-007 enmienda 2026-11-01 / RF-8..RF-13.
  **Coordinar el push**: un push a `main` redeploya Render y vacía la BD; esta
  enmienda no requiere despliegue de la app.
  Hecho cuando: existe el informe QA con veredicto y matriz completa, la
  evidencia CSV + IDs está en la carpeta indicada, el JSON está versionado,
  `MEMORY.md` refleja el estado, `git status` está limpio y el diff no incluye
  código de la app ni tests.
  Evidencia esperada: informe QA + CSV + `ejecuciones.md` + JSON versionado +
  registro de `MEMORY.md` y del commit.
  **Hecho 2026-11-04 (todo salvo la aceptación funcional):**
  - [x] Regresión `python -m pytest -q` → **302 passed / 0 FAIL**; sin cambios
        en `consultorio/` ni `tests/`.
  - [x] Informe QA `qa-hu-007-enmienda-2026-11-01.md` con matriz RF-8..RF-13,
        escenarios A–E PASS, CA-8..CA-13 marcados y veredicto **PASS funcional
        (5/5)**.
  - [x] Evidencia CSV + `ejecuciones.md` + `precheck.md` en
        `docs/evidencias/hu-007/enmienda-2026-11-01/`.
  - [x] JSON **v5** versionado (48 nodos, sha256 `89183067…`); v1–v4
        conservadas.
  - [x] `MEMORY.md` actualizado (enmienda implementada y validada, 2026-11-04);
        `D-007-01` en `CORREGIDO — PENDIENTE DE VALIDACIÓN`.
  - [x] Commit de cierre de docs/artefactos con HU-007 enmienda 2026-11-01 /
        RF-8..RF-13; push coordinado (no requiere despliegue de la app).
  - [ ] **Aceptación funcional de la usuaria** (pendiente único).
