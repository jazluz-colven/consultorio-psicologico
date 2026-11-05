# Plan 007 — Automatización de reservas mediante n8n

> Trazabilidad: **HU-007 → Spec 007 (`specs/007_automatizacion-reservas/spec.md`) →
> este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs`.
> Etapa actual: **HU-007 ACEPTADA Y CERRADA** (2026-10-10); **enmienda 2 completada
> (2026-10-10): cabecera de autenticación opcional `AUTOMATION_WEBHOOK_AUTH_HEADER`
>** (Q7, decisión D14) — suite **147 PASS / 0 FAIL**, TC-007-014 PASS y live
> contra n8n **HTTP 200**. Decisiones Q1–Q5 respondidas por la usuaria
> (2026-10-10): webhook genérico a n8n, payload sin datos personales, POST
> síncrono con timeout corto, registro en tabla `automation_events` y sin
> reintento automático. **Enmienda de la spec 007 confirmada (2026-10-10)**.
> QA **PASS** en `docs/evidencias/hu-007/qa-hu-007.md` (12/12 TC + enmienda 2).
> Baseline declarado en `MEMORY.md` (2026-10-09): **134 PASS / 0 FAIL**; verificar al
> crear la rama.

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 007: que, cuando una reserva quede
confirmada (alta exitosa), el sistema emita un **evento estructurado** que active las
automatizaciones administrativas configuradas en n8n, **sin que la automatización sea
jamás condición de validez de la reserva** (RF-2, RF-7), enviando solo los datos
necesarios e identificando la versión del evento (RF-3), registrando incidencias sin
invalidar la reserva (RF-4) y evitando duplicados ante reprocesos (RF-5).

**Base existente (HU-001/002/003/016/004/005/006 aceptadas)**:
- `create_booking()` con doble comprobación + `UNIQUE (service, date, time)`
  (D3 plan 006); PRG `POST /citas → 303 → /citas/confirmada/<id>`; estado `pending`.
- Capa de persistencia stdlib (`consultorio/persistence/`, SQLite, sin ORM),
  inyección de `database_path` en servicios; `Config`/`app.config` como única fuente
  de configuración (`create_app()`).
- **Baseline: `python -m pytest -q` → 134 PASS / 0 FAIL** (declarado en MEMORY.md,
  2026-10-09; verificar en la rama).

Esta HU **no reescribe lo que funciona**: el flujo de reserva, disponibilidad y
protección de doble reserva quedan intactos (RF-7); solo se añade un disparo
best-effort tras el INSERT y su registro persistente.

**Fuera de alcance** (spec 007): automatizaciones que cancelen o modifiquen reservas;
convertir la automatización en requisito para confirmar; notificaciones de correo o
WhatsApp (Specs 008/009); flujos concretos de n8n (viven en n8n, no en la app);
reintentos automáticos; panel de administración de incidencias; dependencias nuevas
(constitución #1).

**Interpretación fijada en la spec (enmienda 2026-10-10)**: «reserva confirmada» =
**alta exitosa** de la cita (INSERT commitado → página `/citas/confirmada/<id>`),
que es el único momento de confirmación existente hoy; el estado de negocio sigue
siendo `pending` (sin cambio de modelo de `appointments`).

**Dudas de la spec, cerradas por la usuaria (2026-10-10)** (detalladas en §7.1):
- **Q1 — automatizaciones del primer incremento**: webhook genérico a n8n; los flujos
  concretos se configuran en n8n.
- **Q2 — datos del evento**: sin datos personales (minimización); n8n puede consultar
  por `appointment.id` si se amplía el alcance después.

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Reserva confirmada → evento estructurado para iniciar automatizaciones | §2.2 contrato del evento; §3 `build_event`/`on_appointment_confirmed`; §5 D1/D7; §6 TC-007-001/002/012 |
| RF-2 | Servicio de automatización no disponible → reserva sigue válida | §3 aislamiento total; §5 D3/D6; §6 TC-007-003/004/008/009 |
| RF-3 | Evento con únicamente datos necesarios e identificable su versión | §2.2 payload mínimo + `event_version`; §5 D2/D4; §6 TC-007-001/002/012 |
| RF-4 | Error/timeout/respuesta no válida → incidencia registrada, reserva intacta | §2.3 estados y motivos; §3 mapeo de fallos; §5 D3/D6/D8; §6 TC-007-004/005/006/008 |
| RF-5 | Reproceso de la misma reserva → sin automatizaciones duplicadas | §2.1 `UNIQUE (event_id)`; §3 `insert_event` → duplicado sin POST; §5 D5; §6 TC-007-007/010 |
| RF-6 | Evento válido → ejecución de las automatizaciones configuradas | §2.4 configuración; §3 `_post_webhook`; §5 D1/D3/D9; §6 TC-007-002/011 |
| RF-7 | Agendamiento, disponibilidad y doble reserva operativos con independencia | §3 aislamiento + sin cambios de contrato; §5 D6/D7; §6 TC-007-008/012/013 (regresión total) |
| RNF-1 | Seguridad y minimización de datos compartidos | §2.2 payload sin PII; §5 D2; §6 TC-007-001 |
| RNF-2 | Tolerancia a indisponibilidad temporal | §3 try/except + timeout; §5 D3; §6 TC-007-003/004/009 |
| RNF-3 | Trazabilidad de errores y eventos | §2.1/§2.3 tabla `automation_events` + motivos; §5 D4/D8; §6 TC-007-005/006/010 |
| RNF-4 | Consistencia ante reintentos y duplicados | §2.1 `UNIQUE(event_id)` en el punto de persistencia; §5 D5; §6 TC-007-007/010 |
| CL-1 | Servicio de automatización no disponible (caída) | §3 `URLError` → `failed`; §6 TC-007-004 |
| CL-2 | Timeout | §3 `timeout` configurable → `failed`; §6 TC-007-005/009 |
| CL-3 | Respuesta no válida (no-2xx) | §3 HTTP 500 → `failed`; §6 TC-007-006 |
| CL-4 | Reintento del mismo evento | §3 duplicado → sin POST; §6 TC-007-007 |
| CL-5 | Evento duplicado | constitución #5 + §2.1 `UNIQUE(event_id)`; §6 TC-007-007/010 |
| CL-6 | Datos incompletos o no permitidos en el evento | §2.2 allowlist de campos (sin PII); §6 TC-007-001 |
| Finalización | Tests en verde (incl. indisponibilidad, errores, reprocesos) + demo manual | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-7]` — Constitución #3: la lógica de automatización vive en `services/` +
`persistence/`; la capa web solo inyecta la configuración (mismo patrón DI que
`database_path`). Sin dependencias nuevas (constitución #1: solo stdlib
`urllib.request`, `json`, `socket`). Solo se muestran los **cambios sobre lo
existente**:

```text
Consultorio_Carolina/
├── consultorio/
│   ├── config.py                      # + AUTOMATION_WEBHOOK_URL (env, default "")
│   │                              #   + AUTOMATION_TIMEOUT_SECONDS (env, default 3.0,
│   │                              #   parse defensivo)
│   │                              #   + AUTOMATION_WEBHOOK_AUTH_HEADER (env, default "",
│   │                              #   formato "Nombre: valor")              [RF-2][RF-6]
│   ├── content/
│   │   └── automation_content.py      # EVENT_TYPE="appointment.confirmed",
│   │                              #   EVENT_VERSION=1, motivos de incidencia
│   │                              #   (español)                            [RF-3][RF-4]
│   ├── services/
│   │   ├── automation_service.py      # build_event(), on_appointment_confirmed(),
│   │   │                          #   dispatch_event(), _post_webhook()
│   │   │                          #   (nunca propaga excepciones)
│   │   │                          #   [RF-1][RF-2][RF-3][RF-4][RF-5][RF-6][RF-7]
│   │   └── appointment_service.py     # create_booking(): 1 disparo best-effort
│   │                              #   tras el INSERT (contrato intacto)   [RF-1][RF-7]
│   └── persistence/
│       ├── database.py                # SCHEMA += automation_events (idempotente)
│       │                              #   [RF-4][RF-5][RNF-3]
│       └── automation_events_repository.py  # insert_event() (UNIQUE event_id),
│                                   #   mark_sent/mark_skipped/mark_failed,
│                                   #   get_by_event_id            [RF-4][RF-5]
├── consultorio/web/appointments.py    # POST /citas: pasar config de automatización
│                                   #   a create_booking(); contrato HTTP intacto
│                                   #   [RF-2][RF-6][RF-7]
└── tests/
    ├── test_automation_service.py     # unit + integración: payload, envío, caída,
    │                              #   timeout, no-2xx, duplicados, aislamiento
    │                              #   [RF-1..RF-6][CL-1..CL-6]
    └── test_hu_007.py                 # esquema, configuración, flujo completo,
                                   #   regresión total y RNF          [RF-5][RF-7][todos]
```

**Sin cambios**: esquema de `appointments`, `appointments_repository.py`,
`availability.js`, plantillas, CSS, `base.html` (sin UI: no hay copy nuevo ni
espejo en `expected_content.py`). `init_db()` sigue siendo `CREATE TABLE IF NOT
EXISTES` → la tabla nueva se crea en BDs existentes **sin migración destructiva**.

Responsabilidades (solo módulos tocados):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/automation_content.py` | Constantes: tipo, versión y motivos de incidencia | Contener lógica o acceder a la BD |
| `services/automation_service.py` | Construir el payload, orquestar registro + envío, traducir fallos a `failed`, **nunca propagar** | Escribir HTML, gestionar status codes HTTP de la app, contener PII |
| `services/appointment_service.py` | Tras el INSERT, invocar `on_appointment_confirmed()` | Bloquear o condicionar la reserva a la automatización |
| `persistence/automation_events_repository.py` | Acceso a datos de `automation_events` (insert con dedup, actualización de estado) | Reglas de negocio ni llamadas HTTP |
| `persistence/database.py` | DDL de `automation_events` | Tocar tablas existentes |
| `web/appointments.py` | Inyectar `AUTOMATION_WEBHOOK_URL`/timeout desde `app.config` | Consultar la BD ni contener reglas de negocio |
| `config.py` | Variables de entorno con defaults seguros | Lógica de envío |

---

## 2. Literales, modelo de datos y contrato del evento

`[RF-1][RF-3][RF-4][RF-5][RNF-1][RNF-3][RNF-4]` — **Con cambios de esquema (§2.1)**,
respaldados por la enmienda de la spec 007 (2026-10-10) (AGENTS.md: nada de tablas
sin spec y plan).

### 2.1 Modelo de datos — tabla `automation_events`

`appointments` y su `UNIQUE (service, date, time)` quedan **intactos** (RF-7). Se
añade:

```sql
CREATE TABLE IF NOT EXISTS automation_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT NOT NULL UNIQUE,
    event_type      TEXT NOT NULL,
    event_version   INTEGER NOT NULL,
    appointment_id  INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    detail          TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    sent_at         TEXT
);
```

- `event_id` = clave de idempotencia: **determinista**
  `appointment.confirmed:{appointment.id}:v{EVENT_VERSION}` (§3).
- `UNIQUE (event_id)` **en el punto de persistencia** (constitución #5): el
  reproceso de la misma reserva choca en el INSERT y se descarta antes de cualquier
  POST (RF-5, CL-4, CL-5).
- `status`: `pending` → `sent` | `skipped` | `failed` (identificadores en inglés,
  constitución #6). `detail` en español (documentación funcional).
- Sin FK forzada (SQLite la ignora sin PRAGMA, como el resto del proyecto);
  `appointment_id` documenta el vínculo.

### 2.2 Contrato del evento (payload JSON, texto contractual de la spec enmendada)

`[RF-1][RF-3][RNF-1][CL-6]` — allowlist estricta de campos; **cero datos
personales** (Q2):

```json
{
  "event_id": "appointment.confirmed:34:v1",
  "event_type": "appointment.confirmed",
  "event_version": 1,
  "occurred_at": "2026-10-10 12:34:56",
  "appointment": {
    "id": 34,
    "service": "individual",
    "date": "2026-10-15",
    "time": "10:00",
    "status": "pending"
  }
}
```

- `event_version` (RF-3): entero, empieza en **1**; cualquier cambio de forma eleva
  la versión y el `event_id` correspondiente.
- Campos excluidos a propósito: `patient_name`, `email`, `phone`, `document_type`,
  `document_number`, `created_at` de la cita (minimización, RNF-1, CL-6).
- `service` es el identificador del catálogo; n8n resuelve el nombre.

### 2.3 Estados e incidencias (RF-4, RNF-3)

| Situación | `status` | `detail` (español) | RF/CL |
|---|---|---|---|
| Evento registrado, a punto de enviarse | `pending` | `NULL` | RF-1 |
| HTTP 2xx | `sent` | `NULL` + `sent_at` | RF-6 |
| URL no configurada | `skipped` | `Automatización no configurada.` | RF-2, RF-6 |
| `URLError` / conexión rechazada | `failed` | `Servicio de automatización no disponible.` | RF-2, RF-4, CL-1 |
| Timeout | `failed` | `Tiempo de espera agotado (timeout).` | RF-4, CL-2 |
| Respuesta no-2xx | `failed` | `Respuesta no válida del servicio (HTTP {code}).` | RF-4, CL-3 |
| Otra excepción | `failed` | `Error inesperado durante la automatización.` | RF-4 |

Ningún `failed` invalida la cita (RF-2, RF-4): son **registros**, no estados de la
reserva. No hay reintento automático (Q5): la re-ejecución la decide el
administrador/n8n; si alguien vuelve a disparar el mismo evento, el `UNIQUE` impide
el duplicado (RF-5).

### 2.4 Configuración (RF-2, RF-6)

- `AUTOMATION_WEBHOOK_URL` (env): URL del workflow de n8n; **vacía por defecto =
  automatización deshabilitada** (el sistema sigue operativo; evento `skipped`).
- `AUTOMATION_TIMEOUT_SECONDS` (env): **3.0 s** por defecto; parse defensivo (valor
  no numérico → 3.0, sin arrancar la app).
- `AUTOMATION_WEBHOOK_AUTH_HEADER` (env, enmienda 2 / Q7): cabecera opcional en
  formato `Nombre: valor`; vacía por defecto = POST sin cabecera extra. El token es
  un secreto de entorno: **nunca** en el repositorio, documentación ni tests
  (solo valores falsos en los tests).
- Se declaran en `Config` (visibles en `app.config`) y se **inyectan como
  parámetros** desde `web/appointments.py` a `create_booking()` →
  `on_appointment_confirmed()`, mismo patrón de DI que `database_path`.

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-7][CL-1..CL-6]`

```text
# --- persistence/automation_events_repository.py ----------------------
FUNCTION insert_event(event, db) -> bool:                 # True = creado
    TRY:
        INSERT INTO automation_events (event_id, event_type, event_version,
            appointment_id, status) VALUES (..., 'pending')
        RETURN True
    CATCH sqlite3.IntegrityError:                          # UNIQUE (event_id)
        RETURN False                                       [RF-5][CL-4][CL-5]

FUNCTION mark_sent(event_id, db) / mark_skipped(event_id, detail, db)
FUNCTION mark_failed(event_id, detail, db)                 [RF-4][RNF-3]

# --- services/automation_service.py -----------------------------------
FUNCTION build_event(appointment) -> dict:                 # allowlist, sin PII
    RETURN {                                               [RF-3][RNF-1][CL-6]
        "event_id": f"appointment.confirmed:{appointment.id}:v{EVENT_VERSION}",
        "event_type": EVENT_TYPE, "event_version": EVENT_VERSION,
        "occurred_at": datetime.now().isoformat(sep=" "),
        "appointment": {"id": …, "service": …, "date": …,
                        "time": …, "status": appointment.status}}

FUNCTION on_appointment_confirmed(appointment, db, url, timeout,
                                  auth_header="") -> None:
    TRY:                                                   # nunca propaga
        event = build_event(appointment)
        IF NOT insert_event(event, db):
            RETURN                                 # ya procesada → sin POST [RF-5]
        IF url EMPTY:
            mark_skipped(event_id, "Automatización no configurada.")  [RF-2]
            RETURN
        TRY:
            status_code = _post_webhook(url, event, timeout, auth_header)
        CATCH TimeoutError:
            mark_failed(…, "Tiempo de espera agotado (timeout).")     [CL-2]
            RETURN
        CATCH urllib.error.URLError:                       # incluye refused
            mark_failed(…, "Servicio de automatización no disponible.") [CL-1]
            RETURN
        CATCH Exception:
            mark_failed(…, "Error inesperado durante la automatización.")
            RETURN
        IF 200 <= status_code < 300:
            mark_sent(event_id, db)                        [RF-6]
        ELSE:
            mark_failed(…, f"Respuesta no válida del servicio (HTTP {status_code}).")
                                                          [RF-4][CL-3]
    CATCH Exception:
        RETURN   # fallo de registro/log: la reserva ya es válida
                                                          [RF-2][RF-4][RF-7]

FUNCTION _post_webhook(url, payload, timeout, auth_header="") -> int:  # stdlib
    headers = {"Content-Type": "application/json"}
    IF auth_header NOT EMPTY:                    # enmienda 2 (Q7/D14)
        name, _, value = auth_header.partition(": ")   # primer "Nombre: valor"
        IF name NOT EMPTY: headers[name] = value.strip()
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
        headers=headers, method="POST")
    WITH urllib.request.urlopen(request, timeout=timeout) AS response:
        RETURN response.status                             [RF-6]

# --- services/appointment_service.py (único punto tocado) -------------
FUNCTION create_booking(data, db, automation_url="", automation_timeout=3.0,
                        automation_auth_header=""):
    IF repository.is_slot_taken(…): RETURN SLOT_TAKEN      # sin cambios (HU-006)
    TRY:
        appointment = repository.insert_appointment(data, db)  # 1 fila
    CATCH sqlite3.IntegrityError / OperationalError:
        RETURN SLOT_TAKEN                                  # sin cambios (HU-006)
    automation_service.on_appointment_confirmed(
        appointment, db, automation_url, automation_timeout,
        automation_auth_header)                                [RF-1][RF-7]
    RETURN appointment                                     # la reserva no depende
                                                          # de la automatización [RF-2]

# --- web/appointments.py (POST /citas) --------------------------------
    result = create_booking(data, _database_path(),
        current_app.config["AUTOMATION_WEBHOOK_URL"],
        current_app.config["AUTOMATION_TIMEOUT_SECONDS"],
        current_app.config["AUTOMATION_WEBHOOK_AUTH_HEADER"])     [RF-2][RF-6]
    # contrato intacto: 303 a /citas/confirmada/<id>             [RF-7]
```

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor (BD existente) | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `python -m pytest -q` | Suite completa (134 previos + 13 nuevos = 147) | `147 passed` | `0` / `1` |
| `python -m pytest tests/test_hu_007.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-7]` — **sin cambios de endpoints**

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `POST` | `/citas` (válido y libre) | redirige a la confirmación; **1 fila**; además 1 fila en `automation_events` | **303** → **200** |
| resto de rutas | sin cambios | como hasta ahora | 200/303/400/404/405 |

No hay rutas nuevas: el sistema no expone UI de automatización (la incidencia se
consulta en la BD; un panel sería otra HU).

**Contrato semántico (lo que verifican los tests):**

```text
[RF-1] POST /citas válido → INSERT en automation_events con event_id
       determinista, event_type/version y payload sin PII         → absent ⇒ FAIL
[RF-2] webhook no configurado / URLError → 303 y la cita existe
       intacta (status 'pending')                                 → absent ⇒ FAIL
[RF-3] payload = allowlist exacta de §2.2; ningún campo de PII     → absent ⇒ FAIL
[RF-4] timeout / 500 / URLError → evento 'failed' con detail y
       la cita intacta; jamás excepción al paciente               → absent ⇒ FAIL
[RF-5] segunda invocación sobre la misma cita → 0 eventos nuevos
       y 0 POST adicionales                                       → absent ⇒ FAIL
[RF-6] HTTP 2xx → evento 'sent' con sent_at                        → absent ⇒ FAIL
[RF-7] flujo completo de reserva con y sin webhook: /citas,
       /citas/horarios, /citas/disponibilidad y /citas/confirmada
       con contrato idéntico al de HU-004/005/006                  → absent ⇒ FAIL
[regresión] 134 tests previos intactos, sin aserciones relajadas   → present ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Webhook genérico único `appointment.confirmed`**; los flujos concretos se configuran en n8n (Q1) | El sistema solo emite el evento estructurado (RF-1/RF-6); n8n es el orquestador, la app no acopla procesos administrativos | *Varios tipos de evento en la app*: acoplamiento, más alcance y más spec sin necesidad | RF-1, RF-6 |
| D2 | **Payload sin datos personales** (Q2): solo ids, servicio, fecha, hora, estado y metadatos del evento | RNF minimización; la automatización no necesita PII para existir; n8n puede ampliarse después con una enmienda | *Incluir nombre/email/teléfono*: excede lo estrictamente necesario y obliga a justificar la excepción en spec | RF-3, RNF-1, CL-6 |
| D3 | **POST síncrono con stdlib `urllib.request`, timeout 3 s, 1 intento** (Q3+Q5), best-effort tras el INSERT | Constitución #1 (sin `requests`); el INSERT ya está commitado, la respuesta al paciente no depende del resultado; determinista y fácil de parchear en tests | *Hilo en background*: ciclo de vida y tests frágiles sin ganancia funcional. *`requests`/webhooks lib*: dependencia sin aprobación. *Reintentos con backoff*: alcance extra (Q5) | RF-2, RF-4, RF-6, RNF-2 |
| D4 | **Tabla `automation_events` con `UNIQUE (event_id)`** como registro de eventos e incidencias (Q4) | RF-4 exige registrar y RF-5 exige dedup **en el punto de persistencia** (constitución #5); trazabilidad consultable (RNF-3); `CREATE TABLE IF NOT EXISTS` no migra nada destructivamente | *Solo log en fichero*: dedup débil y consulta frágil. *Tabla sin UNIQUE*: RF-5 quedaría sin garantía | RF-4, RF-5, RNF-3, RNF-4 |
| D5 | **`event_id` determinista `appointment.confirmed:{id}:v{version}`** (sin uuid aleatorio) | El reproceso genera el mismo id → el UNIQUE corta el duplicado **antes** de reenviar (RF-5, CL-4/CL-5); traza legible | *UUID por emisión*: cada reproceso crearía un evento nuevo y dispararía n8n otra vez | RF-5, CL-4, CL-5 |
| D6 | **La capa de automatización nunca propaga excepciones** (try/except completo en `on_appointment_confirmed`, con caps en cada paso) | RF-2/RF-4/RF-7: un fallo de n8n, de red o de registro no puede ni tumbar la reserva ni el 303 | *Dejar propagar*: un 500 rompería la reserva ya creada. *`except Exception` en create_booking*: enmascararía errores ajenos (lección D3 plan 006) | RF-2, RF-4, RF-7 |
| D7 | **Disparo = alta exitosa** («confirmada» = INSERT commitado → `/citas/confirmada/<id>`), sin cambio de `status` | Es el único momento de confirmación existente; no se inventa un flujo de estados (fuera de alcance) y no toca el modelo de HU-004 | *Nuevo estado `confirmed` + workflow*: alcance nuevo sin requisito; Specs 010/011/012 manejan estados posteriores | RF-1, RF-7 |
| D8 | **Estados `pending/sent/skipped/failed` + `detail` en español** | Identificadores en inglés y mensajes en español (constitución #6); `skipped` distingue «no configurado» de un error real (no es incidencia) | *Solo sent/failed*: un fallo de configuración parecería incidencia. *Detalle en inglés*: rompe la constitución | RF-2, RF-4, RNF-3 |
| D9 | **Config por variables de entorno en `Config` e inyectada por parámetros** (patrón DI de `database_path`) | Fuente única `app.config`, testeable sin `monkeypatch` de entorno, y deshabilitado por defecto = el sitio opera sin n8n (RF-2) | *`os.environ` directo en el servicio*: dos fuentes de verdad y tests más frágiles. *Config global importada*: acoplamiento | RF-2, RF-6 |
| D10 | **Rama `feature/hu-007` desde `main`** (HU-006 aceptada y mergeada, baseline 134) | AGENTS.md: aislamiento de HU por rama; `main` está limpia | *Rama desde otra feature*: arrastra pendientes | regresión |
| D11 | **Sin dependencias nuevas**: `urllib.request`, `json`, `sqlite3` de la stdlib | Constitución #1; todo lo necesario ya está en la stdlib | *requests, celery, colas*: dependencias sin aprobación escrita | todos |
| D12 | **Identificadores en inglés; literales de `automation_content.py` y `detail` en español**; sin espejo en `expected_content.py` (no hay UI) | Constitución #6; el espejo existe para textos visibles al usuario y esta HU no añade copy visible | *Texto hardcodeado en el servicio*: rompe la trazabilidad y la coherencia | todos |
| D13 | **Tests deterministas parcheando `_post_webhook`/`urlopen`** (respuestas 2xx/500, `URLError`, `TimeoutError` simulados), sin red real ni `sleep` | La demo manual (§6.2) usa el webhook real; los tests no deben depender de n8n ni de la red (pytest-qa) | *Levantar un servidor real en los tests*: lentitud y fragilidad. *`sleep` para simular timeout*: flaky | RF-2, RF-4, CL-1..CL-3 |
| D14 | **Cabecera de autenticación opcional vía `AUTOMATION_WEBHOOK_AUTH_HEADER`** (formato `Nombre: valor`, vacía por defecto), añadida al POST por `_post_webhook()` (enmienda 2, Q7) | n8n en la nube exige auth en el webhook (403 real de la usuaria, 2026-10-10); una sola variable de entorno permite usar Header Auth de n8n sin código específico y mantiene el token **fuera del repositorio** (seguridad: nunca en código, docs ni tests) | *Token hardcodeado o en la BD*: secreto en el repo/datos. *Soporte de Basic Auth/queries*: más alcance sin necesidad. *Parchear el código por instancia*: rompe la configuración por entorno (D9) | RF-2, RF-6, RNF-1 |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` (suite) ·
`python -m pytest tests/test_hu_007.py -v` (HU). Fixtures de `conftest.py` **sin
cambios** (`app`, `client`, `database_path` con BD temporal). Arrange/Act/Assert,
sin dependencia del orden. Config de automatización pasada por parámetro (D9), sin
tocar el entorno del proceso.

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-007-001 | `test_automation_service.py` | `build_event()` con una cita → allowlist exacta de §2.2 (`event_id`, `event_type`, `event_version=1`, `occurred_at`, `appointment{id,service,date,time,status}`) y **ningún** campo de PII (nombre, email, teléfono, documento) | RF-3, RNF-1, CL-6 |
| TC-007-002 | `test_automation_service.py` | `create_booking()` con `urlopen` parcheado (200) → 1 fila + evento `sent` + **1 POST** cuyo body JSON es el payload de §2.2 | RF-1, RF-6 |
| TC-007-003 | `test_automation_service.py` | **CL-1 (no configurado):** URL vacía → reserva `303`/1 fila + evento `skipped` («Automatización no configurada.») + **0 POST** | RF-2, RF-6 |
| TC-007-004 | `test_automation_service.py` | **CL-1:** `urlopen` lanza `urllib.error.URLError` → evento `failed` con «Servicio de automatización no disponible.», **0 excepción** y la cita intacta | RF-2, RF-4, CL-1 |
| TC-007-005 | `test_automation_service.py` | **CL-2:** `urlopen` lanza `TimeoutError` → evento `failed` con «Tiempo de espera agotado (timeout).» y la cita intacta | RF-4, CL-2 |
| TC-007-006 | `test_automation_service.py` | **CL-3:** `urlopen` responde **500** → evento `failed` con «Respuesta no válida del servicio (HTTP 500).» y la cita intacta | RF-4, CL-3 |
| TC-007-007 | `test_automation_service.py` | **CL-4/CL-5:** segunda llamada de `on_appointment_confirmed()` con la misma cita → **1 evento** total (UNIQUE) y **1 POST** acumulado | RF-5, CL-4, CL-5, RNF-4 |
| TC-007-008 | `test_automation_service.py` | **RF-7 (aislamiento):** parchear el repositorio de eventos para que lance `RuntimeError` → `create_booking()` **devuelve la `Appointment`** (reserva válida) y el 303 no se ve afectado | RF-2, RF-4, RF-7 |
| TC-007-009 | `test_automation_service.py` | Timeout **efectivo**: `timeout=0.01` con un `urlopen` que tarda (o parche que lanza `socket.timeout`) → `failed`, sin bloquear el retorno | RF-2, RF-4, CL-2 |
| TC-007-010 | `test_hu_007.py` | **RF-5 (esquema):** `sqlite_master` con `automation_events` y `UNIQUE(event_id)`; tras flujo completo + reproceso, `COUNT(*)=1` por `event_id` | RF-5, RNF-3, RNF-4 |
| TC-007-011 | `test_hu_007.py` | **Config:** `Config.AUTOMATION_WEBHOOK_URL == ""`, `AUTOMATION_TIMEOUT_SECONDS == 3.0` y `AUTOMATION_WEBHOOK_AUTH_HEADER == ""` por defecto; parse defensivo del timeout y de la cabecera | RF-2, RF-6 |
| TC-007-012 | `test_hu_007.py` | **Regresión funcional HU-004/005/006:** flujo de reserva completo con webhook configurado y sin configurar → `/citas/horarios` (`available`+`occupied`), `/citas/disponibilidad`, `/citas/confirmada/<id>` y bloqueo de doble reserva **idénticos** al contrato vigente | RF-7 |
| TC-007-013 | `test_hu_007.py` | **Regresión total:** `python -m pytest -q` → **0 FAIL** con los **134 tests previos** intactos (HU-001/002/003/016/004/005/006) | todos, finalización |
| TC-007-014 | `test_automation_service.py` | **Enmienda 2 (Q7/D14):** `_post_webhook()` con `auth_header="X-Test-Token: fake-token"` → la petición `urllib` parcheada lleva la cabecera `X-Test-Token: fake-token` además de `Content-Type`; sin `auth_header` no se añade ninguna cabecera extra. (Solo valores falsos: el token real es secreto de entorno.) | RF-2, RF-6, RNF-1 |

> **Nota de recuento**: TC-007-013 es la corrida de la suite, no una función de test;
> las funciones nuevas son **13** (TC-007-001…012 + TC-007-014), de modo que el
> total esperado es **147** (134 previos + 13). **0 FAIL con los 134 previos
> intactos** es la condición real de cierre.

### 6.2 Pirámide

1. **Unitarias** — `build_event()` (allowlist, versión, sin PII) y
   `insert_event()` (dedup por UNIQUE) sin HTTP ni Flask.
   `[RF-3][RF-5][RNF-1][CL-5][CL-6]`
2. **Integración de servicio** — `create_booking()` + `on_appointment_confirmed()`
   con `_post_webhook`/`urlopen` parcheado: 2xx→`sent`, no configurado→`skipped`,
   `URLError`/`TimeoutError`/500→`failed`, duplicados→1 POST, aislamiento total.
   `[RF-1][RF-2][RF-4][RF-5][RF-6][RF-7][CL-1..CL-4]`
3. **Regresión** — `python -m pytest -q` completo: los **134 tests actuales** deben
   seguir verdes sin enmiendas (ninguna aserción existente se relaja ni se omite).
   `[todos]`
4. **Demo manual** — con `python app.py` y un **receptor local stdlib** (script
   efímero fuera del repo) o la instancia n8n de la usuaria si existe:
   configurar `AUTOMATION_WEBHOOK_URL`, reservar en `/citas` y verificar
   (a) la página de confirmación responde 303/200 normalmente,
   (b) el receptor recibe **1 POST** con el payload de §2.2 (captura del cuerpo),
   (c) el evento aparece como `sent` en `automation_events`,
   (d) **apagando el receptor**, repetir el proceso: la reserva se confirma igual,
   el evento queda `failed` con su motivo y no se invalida nada (RF-2/RF-4),
   (e) reintentar el disparo del mismo evento: **sin segundo POST** (RF-5).
   Sin cambios visuales → sin capturas 1280/375 (como HU-016 Q6); la evidencia es
   el payload capturado + el estado de la tabla.
   `[RF-1][RF-2][RF-4][RF-5][RF-6][RF-7]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar (pytest-qa §1.2).
- Pruebas deterministas: `urlopen`/`_post_webhook` parcheados, sin red real, sin
  `sleep`, BD temporal por fixture, fechas relativas.

```text
HU: HU-007
Caso: TC-007-007
Comando: python -m pytest tests/test_automation_service.py -v
Resultado: PASS
Rama: feature/hu-007
Commit: <hash>
Evidencia: payload del POST capturado + dump de automation_events (demo §6.2)
```

- Informe QA: `docs/evidencias/hu-007/qa-hu-007.md` con PASS/FAIL por TC y checkbox
  de aceptación; veredicto `PASS` / `PARCIAL` / `FAIL` (skill `pytest-qa`).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Duda de la spec: automatizaciones del primer incremento | **Webhook genérico `appointment.confirmed` a n8n; los flujos concretos se configuran en n8n** (D1). **Respondida 2026-10-10 y fijada en la enmienda de la spec.** |
| Q2 | Duda de la spec: datos estrictamente necesarios del evento | **Payload mínimo sin datos personales** (§2.2, D2); `appointment.id` permite ampliar después. **Respondida 2026-10-10 y fijada en la enmienda.** |
| Q3 | Mecanismo y momento de envío | **POST síncrono best-effort con stdlib y timeout 3 s tras el INSERT** (D3, D6). **Respondida 2026-10-10.** |
| Q4 | Registro de eventos e incidencias / deduplicación | **Tabla `automation_events` con `UNIQUE(event_id)` + estados y detalle** (D4, D5, D8). **Respondida 2026-10-10; exige enmienda de spec + plan (AGENTS.md) → enmienda confirmada.** |
| Q5 | Reintentos automáticos | **Sin reintento en la app**: 1 intento; la re-ejecución la decide el administrador/n8n y el UNIQUE evita duplicados (D3, D5). **Respondida 2026-10-10.** |
| Q6 | Rama de trabajo | **`feature/hu-007` desde `main`** (D10), tras aprobar plan y enmienda. |
| Q7 | Autenticación del webhook n8n (la nube devuelve 403 sin credenciales; la usuaria aporta una cabecera `X-HU007-Token`) | **Cabecera opcional configurable `AUTOMATION_WEBHOOK_AUTH_HEADER`** (formato `Nombre: valor`, vacía por defecto; token solo en entorno, nunca en el repo) (D14). Enmienda 2 de la spec **confirmada 2026-10-10**. |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Aprobación de este `plan.md` (alcance, matriz RF, D1–D13, §2.2 y §2.3) por la
      usuaria — **2026-10-10**.
- [x] **Enmienda de `specs/007_automatizacion-reservas/spec.md`**: cerrar las dos
      dudas [NECESITA ACLARACIÓN] con Q1/Q2, fijar el contrato del evento de §2.2
      (incluido `event_version`), el mecanismo de deduplicación (Q4,
      `UNIQUE(event_id)`), la interpretación de «reserva confirmada» (D7), el
      comportamiento ante no-configurado/timeout/no-2xx y el alcance «sin
      reintento» (Q5) — **confirmada por la usuaria 2026-10-10**.
- [x] Creación de `feature/hu-007` desde `main` (Q6) y verificación del baseline
      **134 PASS / 0 FAIL** — **2026-10-10 (`4735576`; baseline 134 PASS).**
- [x] Implementación de §1–§5 (config → content → repositorio → servicio →
      `create_booking` → inyección web) con commits por fase — **2026-10-10
      (`d1a1bd5`, `31367d0`).**
- [x] Tests §6 en verde: **146 PASS / 0 FAIL** con los 134 previos intactos —
      **2026-10-10 (`138b547`; suite 146/146).**
- [x] Demo manual §6.2 (webhook arriba → `sent` + payload; abajo → reserva
      intacta + `failed`; reproceso → 0 POST) + evidencia en
      `docs/evidencias/hu-007/` — **2026-10-10 (receptor stdlib; `9d039a9`).**
- [x] Informe QA `qa-hu-007.md` con PASS/FAIL por TC y checkbox de aceptación —
      **2026-10-10 (veredicto PASS, 12/12 TC).**
- [x] Commit/Push por fases, actualización de `MEMORY.md` y aceptación de la HU —
      **2026-10-10 (6 commits; HEAD sincronizado con `origin/feature/hu-007`;
      aceptada por la usuaria 2026-10-10).**
- [x] Dejar el servidor de revisión en marcha (AGENTS.md) y comunicar la URL —
      **2026-10-10 (http://127.0.0.1:5001/citas).**

---

## 8. Secuencia de implementación

0. **Git**: verificar `main` limpia y baseline 134 PASS; crear
   **`feature/hu-007` desde `main`** (Q6) — solo tras aprobar este plan.
1. **Spec primero** (bloqueante, cumplido): enmienda de la spec 007 con Q1/Q2 y los
   contratos fijados en §2.2/§2.3 (D1–D8, Q3–Q5).
2. **Plan**: este `plan.md` (aprobado por la usuaria, 2026-10-10).
3. **Config**: `AUTOMATION_WEBHOOK_URL`/`AUTOMATION_TIMEOUT_SECONDS` en `Config`
   (§2.4) → `test_hu_007.py` (TC-007-011).
4. **Persistencia**: `automation_events` en `database.py` +
   `automation_events_repository.py` (§2.1) → TC-007-010.
5. **Contenido**: `automation_content.py` (tipo, versión, motivos; §2.3).
6. **Servicio**: `automation_service.py` (§3, aislamiento D6) +
   `appointment_service.create_booking()` con el disparo →
   `test_automation_service.py` (TC-007-001…009).
7. **Capa web**: inyección de config en `POST /citas` (contrato intacto).
8. **Suite completa**: `python -m pytest -q` → **146 PASS / 0 FAIL** con los 134
   previos intactos (TC-007-012/013).
9. **Evidencia**: demo manual §6.2 (webhook arriba y abajo, sin duplicados) →
   `docs/evidencias/hu-007/` + `qa-hu-007.md` con PASS/FAIL por TC.
10. **Cierre**: commits por fase, push, `MEMORY.md` (HU-007), aceptación de la HU y
    servidor de revisión en marcha (AGENTS.md).

---

## 9. Enmienda 2026-11-01 — RF-8..RF-13: borrado del evento de Google Calendar en n8n

> Trazabilidad: **HU-007 → Spec 007 (enmienda 2026-10-23, RF-8..RF-13) → este §9
> → workflow de n8n → evidencia E2E → commit**.
> Estado: **`IMPLEMENTADO — VALIDADO TÉCNICAMENTE; PENDIENTE DE ACEPTACIÓN
> FUNCIONAL`** (2026-11-04). La **spec está aprobada** (2026-10-23) y RF-8..RF-13
> quedan implementados en el workflow **v5**; T16–T22 están ejecutadas salvo la
> aceptación funcional de la usuaria. No se ha modificado `spec.md`, código,
> tests ni backend: todo el trabajo vive en n8n (§9.11).
> **Nota de corrección 2026-11-02 (D-007-02; aprobada 2026-11-02, superada en la
> rama de error por la corrección 3):** este §9
> sustituye la corrección anterior (D-007-01, opción A). El E2E-B repetido con el
> JSON v2 falló porque **n8n Cloud prohíbe usar la credencial OAuth2 de Google
> Calendar en nodos HTTP Request/GraphQL**; el nodo HTTP Request devolvió
> literalmente `This credential is configured to prevent use within an HTTP
> Request or GraphQL node`. La petición nunca llega a Google y no hay código HTTP:
> la **opción A no es viable**. Corrección 2 (**sustituida en la rama de error por
> la corrección 3, ver la nota siguiente**): se **restaura el nodo
> `googleCalendar`** (`typeVersion 1.3`, parámetros del nodo v1 de
> `docs/workflows/hu-007/n8n-hu-007-integracion-citas-2026-11-01.json`,
> `onError: continueErrorOutput`, `retryOnFail: false`) y se **endurece el
> clasificador** para leer el `error` en cualquier forma (campos estructurados,
> string legacy `404 - "Not Found"` o error serializado); ver §9.5.1, §9.5.4,
> §9.5.5, D-E12, §9.8/R5, §9.9, §9.10 y §9.11. Exigió regenerar el JSON (**v3**,
> T18, histórico) y **repetir T20-B sobre la cita 32** antes de declarar PASS.
> Registro del defecto: `docs/defectos/D-007-01.md` (**`CORREGIDO — PENDIENTE DE
> VALIDACIÓN`**, 2026-11-04; causa raíz real: restricción de plataforma descrita
> arriba; actualizado por el coordinador, ver §9.11).
> **Nota de corrección 3 (2026-11-02; aprobada 2026-11-04, superada por la
> corrección 4):** el JSON **v3**
> (`googleCalendar` restaurado + clasificador endurecido) **tampoco permite cumplir
> RF-10**. Hecho nuevo verificado: el nodo `googleCalendar` **oculta el código
> HTTP**; el error real es
> `Your request is invalid or could not be processed by the service`, **sin 4xx/5xx**
> en los campos del ítem ni en su serialización (`calendar_http_code: null`).
> Interpretar el texto **no permite distinguir 404 de 400/403**, así que ninguna
> heurística textual puede decidir «ya eliminado». **Decisión aprobada por la
> usuaria (2026-11-02): verificar la existencia en lugar de interpretar el error.**
> Tras un borrado fallido, un nodo `Get` (**`Verificar evento`**) comprueba si el
> evento sigue existiendo (§9.5.6, **D-E13**). Exige regenerar el JSON como
> **v4** (T18, §9.9) y **repetir T20-B sobre la cita 32** verificando las dos ramas
> antes de declarar PASS. No se introduce vocabulario nuevo de
> `cancellation_detail` (se reutilizan `not_found` y `http_error_unknown`; RF-12/D4
> intactos). El registro `docs/defectos/D-007-01.md` quedó actualizado por el
> coordinador (ver §9.11).
> **Nota de corrección 4 (2026-11-02; aprobada 2026-11-04):** el JSON **v4**
> (corrección 3) **tampoco permite cumplir RF-10** en el caso real. Hecho
> verificado en ejecución con el JSON v4 sobre la **cita 32** (evento borrado a
> mano): `Elimina cita` (`delete`) falla y n8n oculta el código, pero
> `Verificar evento` (`events.get`) **sí devuelve el evento**, con
> `status: "cancelled"` y el mismo `id`. El evento ya no aparece en el calendario
> visual del usuario, pero la API de Google lo devuelve como cancelado (Google lo
> marca antes de purgarlo). Conclusión: **la verificación de existencia debe
> comprobar el `status`, no la mera existencia**. Se añade el nodo
> `¿Evento cancelado?` (`n8n-nodes-base.if` 2.4, `combinator: "or"`, dos
> condiciones `string equals` sobre
> `={{ ($json.status ?? '').toString().toLowerCase() }}` frente a `cancelled` y
> `canceled`); la cadena pasa a ser `Verificar evento`[0] → `¿Evento cancelado?`,
> true → `Preparar no encontrado`, false → `Preparar borrado fallido`, y
> `Verificar evento`[1] (error) → `Preparar no encontrado` (sin cambios)
> (§9.5.6, **D-E14**). Exige regenerar el JSON como **v5** (T18, **48 nodos**,
> §9.9) y **repetir T20-B sobre la cita 32** verificando **las tres ramas**:
> evento cancelado → `not_found`; error 404 → `not_found`; evento confirmado →
> `failed`. No se introduce vocabulario nuevo de `cancellation_detail` (se
> reutilizan `not_found` y `http_error_unknown`; RF-12/D4 intactos). El registro
> `docs/defectos/D-007-01.md` quedó actualizado por el coordinador (ver §9.11).
> Decisiones de la usuaria del **2026-11-01**: D1–D4 (§9.2). Base del diseño: la
> auditoría del workflow real exportado (42 nodos; data table
> `HU007EventosProcesados`, id `t4GENwUkjVodM5cg`; `active:false` en el export,
> que es un artefacto de la serialización y **no** prueba de inactividad).
> Backend **sin cambios**: la Spec 010 ya emite `appointment.cancelled` v1 (10
> campos, sin PII) al webhook de automatización con cabecera de autenticación.
> Todo el trabajo vive en n8n (workflow + data table).
> Baseline del backend: suite sin cambios; verificar el conteo real al iniciar
> (`MEMORY.md` registra **302 PASS / 0 FAIL** tras D-010-01, 2026-10-30).
> El bloque de cabecera de este documento (líneas 1–16) describe el estado de la
> HU-007 hasta 2026-10-10 y **no se reescribe**; esta enmienda se añade como §9.

### 9.1 Alcance y fuera de alcance

**Alcance** (RF-8..RF-13): que, cuando n8n reciba el evento de negocio
`appointment.cancelled` (Spec 010):

1. localice la **fila de creación** de la cita por `appointment_id`
   (`event_type='appointment.confirmed'`), nunca por el `event_id` de
   cancelación ni de correo (RF-9);
2. recupere su `calendar_event_id` y borre el evento correspondiente de Google
   Calendar (RF-8);
3. registre el resultado del borrado en un **estado de cancelación separado**
   del estado de creación y del estado del correo (RF-12);
4. trate **404/410** de Google Calendar como «ya completado» (idempotente, no
   fallo) y limpie el `calendar_event_id` tras un borrado exitoso (D1, RF-10);
5. registre como **`skipped` con motivo** —nunca `failed` ni «eliminado»— la
   ausencia de fila de creación o de `calendar_event_id` (D2, RF-11);
6. mantenga el borrado activado **solo** por `appointment.cancelled`, no por
   `appointment.cancellation_email` (RF-13).

**Ejecutor único: n8n.** La data table la gestiona n8n; el backend Flask, el
esquema SQLite, los tests y las variables de entorno **no cambian**.

**Fuera de alcance** de esta enmienda:

- Backend y emisión de eventos: Spec 010 RF-8..RF-10, ya implementados; no se
  tocan `automation_service`, `appointment_service`, `automation_events` ni
  `appointment.cancelled`/`appointment.cancellation_email`.
- UI o endpoints nuevos, reintentos automáticos, colas, sub-workflows,
  credenciales nuevas o variables de entorno nuevas.
- Saneamiento de datos históricos de la data table (filas antiguas con
  `processing_status='cancelled'`): **no se decide aquí** (OQ-4).
- Corregir el enrutamiento de reintento de `appointment.cancellation_email`
  (`Enrutar reintento por tipo` no tiene rama para ese tipo): defecto previo,
  ajeno a RF-8..RF-13 (OQ-6).
- Cambios en `tests/expected_content.py`, `AGENTS.md` o `docs/design-*`.
- `MEMORY.md`: lo actualiza el coordinador (T22); este plan no lo modifica.

**Reglas de negocio y manejo de fechas**: no hay cálculos de fecha ni ventanas
temporales nuevas. `occurred_at` se registra pero no gobierna ninguna decisión.
La idempotencia se apoya en el `event_id` determinista de la Spec 010
(`appointment.cancelled:{id}:v1`) y en el estado de la fila, no en el reloj; por
eso no hace falta inyectar una fecha de referencia.

### 9.2 Decisiones aprobadas por la usuaria (2026-11-01)

| # | Decisión aprobada | Dónde se implementa | RF |
|---|---|---|---|
| **D1** | Tras un borrado exitoso se **limpia `calendar_event_id`** y se marca la cancelación; **404/410 se tratan como «ya completado»** (idempotente), no como fallo | `Update row(s)2`; `Clasificar resultado de Calendar` (salida de éxito); `Verificar evento` + `¿Evento cancelado?` + `Preparar no encontrado` (detección de «ya eliminado» por `status`, corrección 4/D-E14); `¿Borrado o ya eliminado?` | RF-10, RF-8 |
| **D2** | Sin fila de creación (0 filas) o sin `calendar_event_id` → **`skipped` con motivo**, nunca `failed` ni «eliminado» | `¿Fila de creación encontrada?`; `Marcar sin fila de creación`; `If1` falso + nodos de skip | RF-11 |
| **D3** | Columna propia `cancellation_status` en la fila de creación (`none|completed|failed|skipped`); `processing_status` queda como estado de creación y **deja de sobrescribirse con `cancelled`**; `email_processing_status` sigue independiente | §9.4; `Update row(s)2`; se retira la escritura de `'cancelled'` | RF-12 |
| **D4** | Columna `cancellation_detail` (texto corto) con `no_creation_record`, `missing_calendar_event_id`, `not_found`, `http_error_<code>`; vacío si el borrado se completó | §9.4; nodos de escritura de la fila de creación (y de la fila del evento en el caso sin fila) | RF-8, RF-11 |

**Lectura de D4 que este plan adopta** (ratificada en la aprobación de la
corrección 4, 2026-11-04; OQ-2): el
detalle vacío corresponde al **borrado real**; en 404/410 el estado es
`completed` y el detalle `not_found`, porque D4 incluye ese motivo y D1 exige
trazar que ya estaba borrado. Si la usuaria prefiere detalle vacío también en
404/410, se ajusta en T18 sin cambiar el resto del diseño.

### 9.3 Matriz RF-8..RF-13 → comportamiento → evidencia

| RF | Comportamiento esperado | Dónde se cubre | Evidencia |
|---|---|---|---|
| **RF-8** | Al recibir `appointment.cancelled`, se identifica la cita por `appointment_id`, se recupera el `calendar_event_id` de la fila de creación y se borra el evento, registrando el resultado | `Consulta` + `Preparar cancelación` + `Elimina cita` + escritura de `cancellation_status`/`cancellation_detail`; §9.5 | Escenarios A y B (§9.6; F es opcional): ejecución de n8n + CSV de las filas afectadas |
| **RF-9** | La fila de creación conserva `appointment_id` y `calendar_event_id`; la búsqueda es por `appointment_id` + `event_type='appointment.confirmed'` (nunca por el `event_id` de cancelación/correo) | Filtro de `Consulta`; §9.5.3 | CSV antes/después: `calendar_event_id` presente antes y usado en `Elimina cita`; `appointment_id` intacto |
| **RF-10** | Un reintento que encuentra el evento ya eliminado (404/410, o `status: cancelled`) se reconoce como completado y no se repite indefinidamente; tras completar se limpia el ID y un reintento posterior es no-op | `Elimina cita`; `Verificar evento` + `¿Evento cancelado?` + `Preparar no encontrado` (corrección 4/D-E14); `Clasificar resultado de Calendar` (salida de éxito); `¿Borrado o ya eliminado?`; `¿Cancelación ya completada?`; `Update row(s)2` | Escenarios B y C: estado `completed` + detalle `not_found`, y reintento que **no** llega a `Elimina cita` |
| **RF-11** | Sin fila de creación o sin `calendar_event_id` → caso registrado y gestionado, marcado `skipped` con motivo, sin dar por hecho el borrado | `¿Fila de creación encontrada?`; `If1`; nodos `Marcar sin …` | Escenarios D y E: `skipped` + motivo; 0 llamadas a Google Calendar |
| **RF-12** | Tres estados independientes: creación (`processing_status`), cancelación (`cancellation_status` + `cancellation_detail`) y correo (`email_processing_status`) | §9.4; `Update row(s)2` deja de escribir `'cancelled'` | CSV con las tres filas de la misma cita (creación, `cancelled`, `cancellation_email`) mostrando los tres estados por separado |
| **RF-13** | `appointment.cancelled` activa el borrado; `appointment.cancellation_email` no | `Enrutar por tipo de evento` [3] y `Enrutar acciones tras registro` [3] ya separan los tipos; se verifica que la rama de correo no toca `Elimina cita` | Ejecución E2E de una cancelación: la rama de correo no invoca el nodo de Google Calendar |
| **Sin regresión** | Backend, suite y contrato de la Spec 010 intactos | Ningún archivo Python cambia | `python -m pytest -q` en verde + `git diff --name-only` sin archivos de código |

### 9.4 Modelo de datos: columnas nuevas de la data table de n8n

#### 9.4.1 Columnas nuevas (solo dos)

| Columna | Tipo | Valores permitidos | Valor por defecto | Se escribe en | RF |
|---|---|---|---|---|---|
| `cancellation_status` | string (texto) | `none` · `completed` · `failed` · `skipped` | `none` | Fila de creación (`event_type='appointment.confirmed'`); en el caso sin fila de creación, en la fila del evento `appointment.cancelled` | RF-12 |
| `cancellation_detail` | string (texto corto) | vacío · `no_creation_record` · `missing_calendar_event_id` · `not_found` · `http_error_<code>` (o `http_error_unknown` cuando el nodo oculta el código; ver OQ-3) | vacío | Misma fila que `cancellation_status` | RF-8, RF-11 |

**Regla de ubicación** (derivada de D3/D4, OQ-1): `cancellation_status` y
`cancellation_detail` viven en la **fila de creación**. Si no existe fila de
creación, no hay dónde escribir el estado de la cita: el caso `skipped` con
`no_creation_record` se registra en la **fila del evento `appointment.cancelled`**
(la única fila disponible), para que el caso no quede en silencio (RF-11).
Ninguna otra fila recibe estas columnas.

**Semántica de los tres estados** (RF-12): `processing_status` describe el
procesamiento del evento registrado en esa fila (en la fila de creación, el
alta/creación) y **nunca** se escribe con `cancelled`; `cancellation_status` +
`cancellation_detail` describen el borrado en Google Calendar; `email_processing_status`
describe la acción técnica de correo. Los tres son independientes y se
consultan por separado.

**Transiciones permitidas** de `cancellation_status`: `none` → `completed` |
`failed` | `skipped`; `failed` → `completed` | `failed` | `skipped` (reintento).
`completed` y `skipped` son terminales para el flujo automático (el reintento
solo se dispara sobre `processing_status='failed'` de la fila del evento).

#### 9.4.2 Columnas existentes que se dejan de escribir (y por qué)

| Columna | Escritura que se retira | Motivo |
|---|---|---|
| `processing_status` (fila de creación) | Ya no se escribe `'cancelled'` (hoy lo hace `Update row(s)2`) | D3/RF-12: el estado de creación no debe fusionarse con el de cancelación |
| `processing_status` (fila del evento `appointment.cancelled`) | Se conserva para el ciclo del propio evento (`received` → `processing` → `completed`/`failed`) | Es el disparador del reintento; no es el estado de creación de la cita |
| `email_processing_status` | **Sin cambios** | RF-12: estado del correo independiente |
| `calendar_event_id` | Se conserva mientras la cita está activa; se limpia **solo** tras borrado completado | D1: evita reutilizar un ID muerto y hace idempotente el reintento |
| `appointment_id` | **Sin cambios** | RF-9: clave de búsqueda de la fila de creación |

#### 9.4.3 Checklist de creación manual en la UI de n8n (lo ejecuta la usuaria)

El JSON parcheado **no crea** las columnas. Antes de importar/activar el
workflow nuevo:

1. n8n → **Data tables** → `HU007EventosProcesados` (id `t4GENwUkjVodM5cg`).
2. Crear la columna **`cancellation_status`**:
   - Tipo: **String / Texto**.
   - Valor por defecto: **`none`**.
   - Obligatoria: **no**.
3. Crear la columna **`cancellation_detail`**:
   - Tipo: **String / Texto**.
   - Valor por defecto: **vacío**.
   - Obligatoria: **no**.
4. Comprobar que los nombres son **exactos** (minúsculas y guion bajo):
   `cancellation_status`, `cancellation_detail`. No usar mayúsculas ni espacios.
5. **No** renombrar, borrar ni cambiar el tipo de `event_id`, `event_version`,
   `event_type`, `appointment_id`, `service`, `appointment_date`,
   `appointment_time`, `appointment_status`, `processing_status`,
   `occurred_at`, `calendar_event_id` ni `email_processing_status`.
6. Verificar que las filas existentes muestran `none` para
   `cancellation_status` y vacío para `cancellation_detail`. Si la UI no aplica
   el default a las filas antiguas, el workflow trata el vacío como `none`.
7. Exportar el CSV de la data table y comprobar que las cabeceras incluyen las
   dos columnas nuevas (evidencia de T17).
8. Captura opcional (recomendada) de la configuración de las dos columnas.

**Condición de orden**: las columnas deben existir **antes** de importar y, sobre
todo, **antes de activar** el workflow parcheado. Si un nodo escribe una columna
inexistente, la ejecución falla y la fila del evento puede quedarse en
`received`/`processing` (R3).

#### 9.4.4 Filas antiguas y compatibilidad

- No se ejecuta ningún saneamiento histórico (OQ-4): las filas con
  `processing_status='cancelled'` escritas por el workflow anterior se conservan
  como historia. El workflow nuevo no vuelve a escribir ese valor.
- Las filas antiguas sin las columnas nuevas quedan con el default (o vacío, que
  se interpreta como `none`).
- No hay migración de esquema en SQLite ni cambios en `automation_events`: la
  data table es de n8n y su gestión es manual.

### 9.5 Diseño a nivel de nodo

Parte del workflow exportado (42 nodos, `webhookId`
`8889e9dd-ca30-4548-9505-95336cc04b51`, data table `t4GENwUkjVodM5cg`).
**No cambia** el contrato del webhook (`POST hu-007-cita-creada`, `headerAuth`,
`responseMode: responseNode`) ni las credenciales.

#### 9.5.1 Inventario de cambios

| Tipo | Nodo | Cambio |
|---|---|---|
| **Nuevo** | `Preparar cancelación` (`n8n-nodes-base.set`, tv 3.5) | Contexto común de ambas ramas: `event_row_id = {{ $json.event_id }}`, `appointment_id = {{ $json.appointment_id }}` |
| **Nuevo** | `¿Fila de creación encontrada?` (`n8n-nodes-base.if`, tv 2.4) | True si `{{ $json.event_id }}` no está vacío **y** `{{ $json.event_type }} = appointment.confirmed` |
| **Nuevo** | `Marcar sin fila de creación` (`n8n-nodes-base.dataTable`, tv 1.1, update) | Fila del evento: `processing_status='completed'`, `cancellation_status='skipped'`, `cancellation_detail='no_creation_record'`; `onError: continueErrorOutput` |
| **Nuevo** | `¿Cancelación ya completada?` (`n8n-nodes-base.if`, tv 2.4) | `{{ $json.cancellation_status }} = completed` (guarda de idempotencia sobre la fila de creación) |
| **Nuevo** | `Marcar sin calendar_event_id - creación` (dataTable update) | Fila de creación: `cancellation_status='skipped'`, `cancellation_detail='missing_calendar_event_id'`; `onError: continueErrorOutput` |
| **Nuevo** | `Marcar sin calendar_event_id - evento` (dataTable update) | Fila del evento: `processing_status='completed'`; `onError: continueErrorOutput` |
| **Nuevo** | `Clasificar resultado de Calendar` (`n8n-nodes-base.code`, tv 2) | **Sin cambios por la corrección 3**: normaliza solo la salida **de éxito** de `Elimina cita` (`calendar_ok`, `calendar_http_code`, `cancellation_detail`); §9.5.5 |
| **Nuevo** | `Verificar evento` (`n8n-nodes-base.googleCalendar`, tv 1.3) | `operation: get`, `calendar: ingjazar@gmail.com`, `eventId: ={{ $json.calendar_event_id }}`, `onError: continueErrorOutput`, `retryOnFail: false`. Recibe la **salida de error** de `Elimina cita` y entrega el evento leído a `¿Evento cancelado?` (§9.5.6, D-E14) |
| **Nuevo** | `Preparar borrado fallido` (`n8n-nodes-base.set`, tv 3.5) | `includeOtherFields: true`; asigna `calendar_ok=false`, `calendar_http_code=null`, `cancellation_detail="http_error_unknown"`. Se usa cuando `Verificar evento` devuelve el evento **con `status` no cancelado** (`¿Evento cancelado?` false): el borrado falló de verdad |
| **Nuevo** | `Preparar no encontrado` (`n8n-nodes-base.set`, tv 3.5) | `includeOtherFields: true`; asigna `calendar_ok=true`, `calendar_http_code=null`, `cancellation_detail="not_found"`. Se usa cuando `Verificar evento` **no puede leer** el evento (404) o lo devuelve **cancelado** (`¿Evento cancelado?` true) |
| **Nuevo** | `¿Evento cancelado?` (`n8n-nodes-base.if`, tv 2.4) | `combinator: "or"`; dos condiciones `string equals` sobre `={{ ($json.status ?? '').toString().toLowerCase() }}` frente a `cancelled` y `canceled`. Recibe la **salida 0** de `Verificar evento`: true → `Preparar no encontrado`; false → `Preparar borrado fallido` (§9.5.6, D-E14) |
| **Nuevo** | `¿Borrado o ya eliminado?` (`n8n-nodes-base.if`, tv 2.4) | `{{ $json.calendar_ok }}` es `true` |
| **Nuevo** | `Marcar cancelación fallida - creación` (dataTable update) | Fila de creación: `cancellation_status='failed'`, `cancellation_detail={{ $json.cancellation_detail }}` (`http_error_unknown` desde `Preparar borrado fallido`); `onError: continueErrorOutput` |
| **Reutilizado** | `Enrutar acciones tras registro` | Salida [3] (`appointment.cancelled`) pasa a apuntar a `Preparar cancelación` (antes `Consulta`) |
| **Reutilizado** | `Enrutar reintento por tipo` | Salida [2] (`appointment.cancelled`) pasa a apuntar a `Preparar cancelación` (antes `Get row(s)1`) |
| **Reutilizado** | `Consulta` | Sin cambios de parámetros (get por `appointment_id` + `event_type='appointment.confirmed'`, `limit 1`, `alwaysOutputData: true`) |
| **Reutilizado** | `If1` | Sin cambios (`calendar_event_id` notEmpty) |
| **Restaurado** | `Elimina cita` | Vuelve a `n8n-nodes-base.googleCalendar` (v1), **sin cambios de `type` ni de `parameters`** respecto al workflow original: `typeVersion: 1.3`, `operation: delete`, `calendar` como resource locator (`ingjazar@gmail.com`, `mode: list`, `cachedResultName: ingjazar@gmail.com`), `eventId: ={{ $json.calendar_event_id }}`, `options: {}`, `credentials` intactas (`googleCalendarOAuth2Api`, id `Jzc9xfMvMH5AeRBN`, nombre `Google Calendar account`), `onError: continueErrorOutput`, `retryOnFail: false`. Motivo: n8n Cloud prohíbe usar la credencial OAuth2 de Google Calendar en HTTP Request/GraphQL (D-E12, D-007-02); el clasificador se endurece para leer el error legacy en cualquier forma. **Corrección 3 (D-E13):** su **salida 1 (error)** deja de ir a `Clasificar resultado de Calendar` y pasa a `Verificar evento`; la salida 0 (éxito) sigue en `Clasificar resultado de Calendar` |
| **Reutilizado** | `Update row(s)2` | Quita `processing_status` del `columns.schema` (`removed:true`, ya no escribe `'cancelled'`); escribe `cancellation_status='completed'`, `cancellation_detail={{ $json.cancellation_detail }}`, `calendar_event_id=''` (fila de creación) |
| **Reutilizado** | `Update row(s)3` | Filtro pasa a `$('Preparar cancelación').first().json.event_row_id`; sigue escribiendo `processing_status='failed'` |
| **Reutilizado** | `Marcar cancelación completada` | Filtro pasa a `$('Preparar cancelación').first().json.event_row_id`; `onError: continueErrorOutput` → `Update row(s)3` |
| **Eliminados** | `Get row(s)1`, `¿Cita ya cancelada?`, `¿Existe evento de Calendar en reintento?`, `Elimina cita - Reintento`, `Actualizar cita cancelada - Reintento`, `Marcar cancelación completada - Reintento`, `Marcar cancelación fallida - Reintento` | La rama de reintento converge en la cadena única; se eliminan nodos y conexiones para que no diverjan |

Resultado esperado: **48 nodos** (42 − 7 + 9 + 3 de la corrección 3 + 1 de la
corrección 4). Se conservan `id`, `type`,
`typeVersion`, `position`, `credentials` y `webhookId` de los nodos existentes;
los nuevos reciben **UUID nuevos** (también los `id` internos de condiciones,
asignaciones y reglas del switch).

**Corrección 3 (D-E13)**: añade **+3 nodos** (`Verificar evento`,
`Preparar borrado fallido`, `Preparar no encontrado`) y **+5 conexiones**, y
**no modifica ningún nodo existente**: solo **retira** la conexión
`Elimina cita` salida 1 → `Clasificar resultado de Calendar`.

**Corrección 4 (D-E14)**: añade **+1 nodo** (`¿Evento cancelado?`, If 2.4) y
**+2 conexiones netas**, y **no modifica ningún nodo existente**: sustituye la
conexión `Verificar evento` salida 0 → `Preparar borrado fallido` por
`Verificar evento` salida 0 → `¿Evento cancelado?` y añade
`¿Evento cancelado?` true → `Preparar no encontrado` y false →
`Preparar borrado fallido`.

**Regla de mapeo**: toda columna que un nodo data table escriba debe tener su
entrada en `columns.schema` con `removed:false`; los nodos nuevos copian el
esquema del nodo equivalente y ajustan los flags. Si falta la entrada, n8n no
ofrece la columna en el mapeo y la escritura no la incluye.

#### 9.5.2 Conexiones

```text
# Entradas de la cadena única
Enrutar acciones tras registro [3]  -> Preparar cancelación   (antes -> Consulta)
Enrutar reintento por tipo     [2]  -> Preparar cancelación   (antes -> Get row(s)1)

# Cadena única (normal y reintento)
Preparar cancelación                -> Consulta
Consulta                            -> ¿Fila de creación encontrada?
¿Fila de creación encontrada? true  -> ¿Cancelación ya completada?
¿Fila de creación encontrada? false -> Marcar sin fila de creación
¿Cancelación ya completada? true    -> Marcar cancelación completada
¿Cancelación ya completada? false   -> If1
If1 true                            -> Elimina cita
If1 false                           -> Marcar sin calendar_event_id - creación
Marcar sin calendar_event_id - creación -> Marcar sin calendar_event_id - evento
Marcar sin calendar_event_id - creación (error) -> Update row(s)3
Marcar sin calendar_event_id - evento (error) -> Update row(s)3
Marcar sin fila de creación (error) -> Update row(s)3
Elimina cita (éxito)                -> Clasificar resultado de Calendar
Elimina cita (error)                -> Verificar evento
Clasificar resultado de Calendar    -> ¿Borrado o ya eliminado?
Verificar evento (éxito: devuelve el evento) -> ¿Evento cancelado?
Verificar evento (error: no existe)          -> Preparar no encontrado
¿Evento cancelado? true (cancelled/canceled) -> Preparar no encontrado
¿Evento cancelado? false (confirmado/otro)   -> Preparar borrado fallido
Preparar borrado fallido            -> Marcar cancelación fallida - creación
Preparar no encontrado              -> ¿Borrado o ya eliminado?
¿Borrado o ya eliminado? true       -> Update row(s)2
¿Borrado o ya eliminado? false      -> Marcar cancelación fallida - creación
Update row(s)2                      -> Marcar cancelación completada
Update row(s)2 (error)              -> Update row(s)3
Marcar cancelación fallida - creación -> Update row(s)3
Marcar cancelación fallida - creación (error) -> Update row(s)3
Marcar cancelación completada (error) -> Update row(s)3
```

Las conexiones no listadas (webhook, validación, dedupe, alta en Calendar,
correo, respuestas) **no se tocan**. Las conexiones de los siete nodos
eliminados desaparecen con ellos.

**Corrección 3 (D-E13) — conexiones retiradas y añadidas (delta exacto):**

```text
RETIRADA
Elimina cita (error)                -> Clasificar resultado de Calendar

AÑADIDAS (+5)
Elimina cita (error)                -> Verificar evento
Verificar evento (éxito)            -> Preparar borrado fallido
Preparar borrado fallido            -> Marcar cancelación fallida - creación
Verificar evento (error)            -> Preparar no encontrado
Preparar no encontrado              -> ¿Borrado o ya eliminado?
```

**Corrección 4 (D-E14) — conexiones retiradas y añadidas (delta exacto):**

```text
RETIRADA
Verificar evento (éxito)            -> Preparar borrado fallido

AÑADIDAS (+3)
Verificar evento (éxito)            -> ¿Evento cancelado?
¿Evento cancelado? true             -> Preparar no encontrado
¿Evento cancelado? false            -> Preparar borrado fallido
```

`Verificar evento` **salida 0** = el `Get` devuelve el evento: **no basta para
concluir que sigue activo**; `¿Evento cancelado?` mira su `status`. **Salida 1** =
el `Get` falla (p. ej. 404): **el evento ya no existe** → `Preparar no encontrado`.
`Clasificar resultado de Calendar` **no cambia** y solo procesa la salida 0 de
`Elimina cita`.

**Equivalencia rama normal ↔ rama de reintento.** La enmienda **elimina la
duplicación** en lugar de mantener dos ramas paralelas. Ambas entradas
(`Enrutar acciones tras registro` [3] y `Enrutar reintento por tipo` [2]) convergen
en `Preparar cancelación` y recorren exactamente los mismos nodos:

```text
Rama normal (evento nuevo)        Rama reintento (evento duplicado failed)
Insert -> ... -> [3]              Consultar evento existente -> If -> Marcar reintento -> [2]
            \____________________  ____________________/
                                 \/
                         Preparar cancelación
                                 |
                         (cadena única: §9.5.2)
```

Así no puede haber reglas distintas entre el primer intento y el reintento: la
detección «borrado / ya eliminado» (§9.5.6), el skip y las escrituras son las
mismas. La única diferencia es el estado previo de la fila del evento (`received`
vs `processing`), que la cadena no lee.

#### 9.5.3 Referencias de expresiones (clave para no divergir)

| Escritura | Filtro / valor |
|---|---|
| Fila de creación (`Update row(s)2`, skip y fallo) | `event_id = {{ $('Consulta').first().json.event_id }}` |
| Fila del evento (`Update row(s)3`, `Marcar cancelación completada`, `Marcar sin fila de creación`, `Marcar sin calendar_event_id - evento`) | `event_id = {{ $('Preparar cancelación').first().json.event_row_id }}` |
| `Preparar cancelación` | `event_row_id = {{ $json.event_id }}`, `appointment_id = {{ $json.appointment_id }}` |
| `¿Fila de creación encontrada?` | `{{ $json.event_id }}` notEmpty **and** `{{ $json.event_type }}` equals `appointment.confirmed` |
| `¿Cancelación ya completada?` | `{{ $json.cancellation_status }}` equals `completed` |
| `If1` | `{{ $json.calendar_event_id }}` notEmpty (sin cambios) |
| `Elimina cita` | `eventId = {{ $json.calendar_event_id }}` (nodo `googleCalendar`, `operation: delete`; el nombre del nodo se conserva) |
| `Verificar evento` | `eventId = {{ $json.calendar_event_id }}` (nodo `googleCalendar`, `operation: get`; sale de la **salida de error** de `Elimina cita`, que conserva el ítem de entrada con `calendar_event_id`) |
| `¿Evento cancelado?` | `{{ ($json.status ?? '').toString().toLowerCase() }}` equals `cancelled` **or** equals `canceled` (`combinator: "or"`, dos condiciones `string equals`) |

No se usan referencias a `$('Insert')` ni a nodos de la rama de reintento
eliminada: la cadena única toma el identificador de la fila del evento de
`Preparar cancelación`, que funciona igual en la rama normal y en la de
reintento.

#### 9.5.4 `onError`, nodo de borrado y detección de «ya eliminado»

**Historial de la corrección (D-007-01 → D-007-02 → corrección 3 → corrección 4).** El problema se
detectó en varias iteraciones reales:

1. **Primer hallazgo (D-007-01, ejecución n8n 13, E2E-B del 2026-11-02).** El
   nodo `googleCalendar` de `Elimina cita` entregó `error` como string sin código
   HTTP; la fila de creación quedó `cancellation_status='failed'`,
   `cancellation_detail='http_error_unknown'` y con `calendar_event_id` sin
   limpiar.
2. **Intento de corrección (opción A, D-007-01).** Se cambió `Elimina cita` a
   `n8n-nodes-base.httpRequest` (tv 4.2) con `predefinedCredentialType:
   googleCalendarOAuth2Api`.
3. **Segundo hallazgo (D-007-02, E2E-B repetido con el JSON v2, cita 32).** La
   ejecución falló con el ítem de error
   `"error": "This credential is configured to prevent use within an HTTP Request
   or GraphQL node"`. **n8n Cloud prohíbe usar la credencial OAuth2 de Google
   Calendar en nodos HTTP Request/GraphQL**: la petición **nunca llega a Google**
   (no hay código HTTP ni respuesta de la API). La limitación es de
   **plataforma**, no de diseño, así que la opción A **no es viable**.
4. **Corrección 2 (D-007-02, 2026-11-02).** Se **restaura el nodo
   `googleCalendar`** del v1 (§9.5.1) y se **endurece el clasificador** (§9.5.5)
   para obtener el código de cualquier forma del `error`: campos estructurados
   (`httpCode`, `statusCode`, `status`, `response.status`, `cause`), string
   legacy tipo `404 - "Not Found"` o el propio error serializado. El nodo
   `googleCalendar` mantiene `onError: continueErrorOutput` y
   `retryOnFail: false`.
5. **Tercer hallazgo (corrección 3, 2026-11-02, E2E-B con el JSON v3 sobre la
   cita 32).** El nodo `googleCalendar` devolvió el error genérico
   `Your request is invalid or could not be processed by the service`, **sin
   4xx/5xx en ningún campo del ítem ni en su serialización**
   (`calendar_http_code: null`). El nodo **oculta el código HTTP**: leer el texto
   **no permite distinguir 404 de 400/403** y el clasificador de la corrección 2
   **no puede cumplir RF-10** en la rama de error. Decisión aprobada por la
   usuaria: **verificar la existencia del evento** (§9.5.6, D-E13) en lugar de
   interpretar el mensaje.
6. **Cuarto hallazgo (corrección 4, 2026-11-02, E2E-B con el JSON v4 sobre la
   cita 32).** Con el evento borrado a mano, `Elimina cita` volvió a fallar y a
   ocultar el código, pero `Verificar evento` (`events.get`) **devolvió el
   evento** con `status: "cancelled"` y el mismo `id`: la API de Google lo
   entrega como cancelado antes de purgarlo, aunque ya no aparece en el calendario
   visual del usuario. La corrección 3 interpretaba «el `Get` devuelve el
   evento» como «sigue existiendo» y marcaba `failed` un borrado que sí se había
   aplicado. **Decisión aprobada por la usuaria (2026-11-02): la verificación
   comprueba el `status`** del evento devuelto (§9.5.6, D-E14).

**Comportamiento vigente (corrección 4).**

**Salida de éxito:** el borrado en Google Calendar completa sin `error` en el
ítem; `Clasificar resultado de Calendar` recibe un ítem **sin `error`** →
`calendar_ok: true` y `cancellation_detail: ''`.

- `Elimina cita`: **`onError: continueErrorOutput`** y **`retryOnFail: false`**
  (política sin cambios). Su **salida de error** ya **no** va al clasificador:
  va a `Verificar evento`. `retryOnFail: false` sigue siendo obligatorio para que
  el fallo llegue a la verificación en la misma ejecución.
- **La salida 0 (éxito) de `Elimina cita` es la única entrada del clasificador.**
  `Clasificar resultado de Calendar` y `¿Borrado o ya eliminado?` **no cambian**;
  se mantiene la regla única para normal y reintento.
- `Verificar evento` (`googleCalendar`, `operation: get`) usa también
  `onError: continueErrorOutput` y `retryOnFail: false`: **salida 0** = el evento
  se leyó → `¿Evento cancelado?` decide por su `status`; **salida 1** = la
  lectura falló (p. ej. 404), **el evento ya no existe** → `Preparar no encontrado`.
- `¿Evento cancelado?` (`n8n-nodes-base.if`, tv 2.4) es la guarda de la corrección
  4: `combinator: "or"` con dos `string equals` sobre
  `={{ ($json.status ?? '').toString().toLowerCase() }}` frente a `cancelled` y
  `canceled`. **true** (evento cancelado: Google ya aplicó el borrado, aunque la
  API aún lo devuelva antes de purgarlo) → `Preparar no encontrado`; **false**
  (evento confirmado u otro estado: el borrado falló de verdad) →
  `Preparar borrado fallido`.
- `Marcar cancelación completada`, `Marcar sin fila de creación`,
  `Marcar sin calendar_event_id - creación`, `Marcar sin calendar_event_id - evento`
  y `Marcar cancelación fallida - creación` usan `continueErrorOutput` hacia
  `Update row(s)3` para que un fallo de la escritura de la cita no deje la fila
  del evento sin estado terminal (el reintento posterior repara el estado, porque
  la cadena es idempotente).
- **El código HTTP de Google no se usa como criterio.** La decisión «borrado /
  ya eliminado / fallo» se toma por dos hechos observables: el **`status`** del
  evento devuelto por `Verificar evento` y, si la lectura falla, su ausencia.
  `Verificar evento` salida 1 → `Preparar no encontrado` (`calendar_ok=true`,
  `cancellation_detail="not_found"`) → `completed`. Salida 0 →
  `¿Evento cancelado?`: true → `Preparar no encontrado` (`completed` +
  `not_found`); false → `Preparar borrado fallido` (`calendar_ok=false`,
  `cancellation_detail="http_error_unknown"`) → `failed`. Se reutilizan los
  motivos existentes (`http_error_unknown`, `not_found`): no se introduce
  vocabulario nuevo (RF-12/D4 intactos).
- **El `jsCode` de §9.5.5 se conserva literal** (defensivo y sin cambios), pero
  en el flujo vigente **nunca recibe `error`**, porque solo procesa la salida 0
  de `Elimina cita`; ya **no** es la pieza que decide el 404.
- **Riesgo residual (R6, §9.8):** con la corrección 4 un `Get` que devuelve un
  evento **cancelado** ya no se interpreta como «existe» (cuenta como borrado
  aplicado); el riesgo que queda es que un `Get` falle por red, credencial o
  cuota y se interprete como «el evento ya no existe», registrando `completed` +
  `not_found`. La mitigación es la verificación manual de T20-B: el evento debe
  estar realmente cancelado o ausente en Google Calendar.
- **Verificación obligatoria en T20-B (repetido con el JSON v5, sobre la cita
  32)**, con **tres ramas**:
  - **(a) evento cancelado**: se borra a mano el evento en Google Calendar antes
    de cancelar. Se espera `Elimina cita` en error → `Verificar evento` devuelve
    el evento con `status: "cancelled"` → `¿Evento cancelado?` true →
    `Preparar no encontrado` → fila de creación `cancellation_status='completed'`,
    `cancellation_detail='not_found'` y `calendar_event_id=''`.
  - **(b) error 404**: `Verificar evento` **falla** porque el evento ya no existe
    (la API responde 404 y no devuelve evento) → `Preparar no encontrado` →
    `completed` + `not_found` + `calendar_event_id=''`.
  - **(c) evento confirmado**: el borrado falla dejando el evento **todavía
    confirmado** → `Verificar evento` devuelve `status: "confirmed"` →
    `¿Evento cancelado?` false → `Preparar borrado fallido` →
    `cancellation_status='failed'` + `cancellation_detail='http_error_unknown'` y
    `calendar_event_id` sin cambios.
  - Si (a) o (b) devuelven `failed`, o (c) devuelve `not_found`/`completed`, **no
    se declara PASS**: se revisan `Verificar evento` y `¿Evento cancelado?` y se
    repite el escenario.

#### 9.5.5 Código del nodo `Clasificar resultado de Calendar` (Code, Run Once for Each Item)

```js
const item = $json ?? {};
const error = item.error ?? null;

const codeFrom = (value) => {
  if (value === null || value === undefined) return null;
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  const match = String(value).match(/\b([45]\d{2})\b/);
  return match ? Number(match[1]) : null;
};

let code = null;

if (error) {
  if (typeof error === 'object') {
    code = codeFrom(error.httpCode) ?? codeFrom(error.statusCode) ?? codeFrom(error.status) ?? codeFrom(error.response?.status) ?? codeFrom(error.response?.statusCode) ?? codeFrom(error.cause?.status) ?? codeFrom(error.cause?.httpCode);
    if (code === null) {
      let serialized = '';
      try { serialized = JSON.stringify(error); } catch (e) { serialized = String(error); }
      code = codeFrom(serialized);
    }
  } else {
    code = codeFrom(String(error));
  }
}

const alreadyDeleted = code === 404 || code === 410;
const calendarOk = !error || alreadyDeleted;
const cancellationDetail = alreadyDeleted ? 'not_found' : (error ? (code === null ? 'http_error_unknown' : `http_error_${code}`) : '');

return { json: { calendar_ok: calendarOk, calendar_http_code: code, cancellation_detail: cancellationDetail } };
```

`http_error_unknown` es la contingencia para cuando no hay código disponible; en las
**correcciones 3 y 4** pasa a ser el motivo efectivo de los fallos reales (los asigna
`Preparar borrado fallido`), porque el nodo `googleCalendar` **oculta el código
HTTP** (`calendar_http_code: null`) y el texto es genérico
(`Your request is invalid or could not be processed by the service`). El `jsCode`
se **conserva literal** por trazabilidad y como defensa: en el flujo vigente solo
procesa la **salida 0 (éxito)** de `Elimina cita`, de modo que `error` es siempre
`null`; el 404/410 ya **no** se detecta aquí sino por el `status`/ausencia del
evento (§9.5.6, D-E13/D-E14). El nodo sigue siendo defensivo: no lanza excepciones por formas
inesperadas.

#### 9.5.6 Verificación del estado del evento tras borrado fallido (correcciones 3 y 4: D-E13, D-E14)

**Problema (corrección 3).** El nodo `googleCalendar` **oculta el código HTTP** de
Google: el error que entrega es `Your request is invalid or could not be processed
by the service`, sin 4xx/5xx en los campos del ítem ni en su serialización
(`calendar_http_code: null`). Interpretar ese texto **no permite distinguir 404 de
400/403**, así que la rama de error no puede cumplir RF-10 («un reintento que
encuentra el evento ya eliminado se reconoce como completado»).

**Problema (corrección 4).** La verificación de la **mera existencia** tampoco
basta. En la ejecución con el JSON **v4** sobre la **cita 32**, con el evento
borrado a mano, `Verificar evento` (`events.get`) **devolvió el evento** con
`status: "cancelled"` y el mismo `id`: Google marca el evento como cancelado
**antes de purgarlo**, así que ya no aparece en el calendario visual del usuario
pero la API todavía lo devuelve. Interpretar «el `Get` devuelve el evento» como
«sigue existiendo» marcaba `failed` un borrado que **sí se había aplicado**.

**Decisión (aprobada por la usuaria, 2026-11-02).** Verificar el **`status`** del
evento devuelto, no la mera existencia. Tras un borrado fallido, `Verificar evento`
(`Get`) lee el evento y `¿Evento cancelado?` decide:

| Paso observado | Significado | Preparación | `cancellation_status` / `cancellation_detail` |
|---|---|---|---|
| **`Elimina cita` salida 0** (borrado 2xx) | El borrado se aplicó; no se verifica nada | `Clasificar resultado de Calendar`: `calendar_ok=true`, `cancellation_detail=''` | `completed` / vacío |
| **`Verificar evento` salida 1** (el `Get` falla, p. ej. 404) | El evento **ya no existe**: el borrado anterior sí se aplicó | `Preparar no encontrado`: `calendar_ok=true`, `calendar_http_code=null`, `cancellation_detail="not_found"` | `completed` / `not_found` |
| **`Verificar evento` salida 0 → `¿Evento cancelado?` true** (`status` `cancelled`/`canceled`) | El evento está **cancelado**: Google ya aplicó el borrado, aunque la API aún lo devuelva antes de purgarlo | `Preparar no encontrado`: `calendar_ok=true`, `calendar_http_code=null`, `cancellation_detail="not_found"` | `completed` / `not_found` |
| **`Verificar evento` salida 0 → `¿Evento cancelado?` false** (`status` `confirmed` u otro) | El evento **sigue activo**: el borrado falló de verdad | `Preparar borrado fallido`: `calendar_ok=false`, `calendar_http_code=null`, `cancellation_detail="http_error_unknown"` | `failed` / `http_error_unknown` |

**Contratos exactos de los nodos de verificación** (tipo, `typeVersion` y
credenciales contrastados con los del JSON v5):

| Nodo | Tipo | Parámetros |
|---|---|---|
| `Verificar evento` | `n8n-nodes-base.googleCalendar` **1.3** | `operation: get`, `calendar: ingjazar@gmail.com` (resource locator `mode: list`, `cachedResultName: ingjazar@gmail.com`), `eventId: ={{ $json.calendar_event_id }}`, `options: {}`, `onError: continueErrorOutput`, `retryOnFail: false`; `position` libre a la **derecha** de `Elimina cita`; `credentials` (`googleCalendarOAuth2Api`, id `Jzc9xfMvMH5AeRBN`, nombre `Google Calendar account`) |
| `¿Evento cancelado?` | `n8n-nodes-base.if` **2.4** | `combinator: "or"`; dos condiciones `string equals` con `leftValue: ={{ ($json.status ?? '').toString().toLowerCase() }}` y `rightValue: cancelled` / `canceled`; `options: {}`. Salida 0 (`true`, cancelado) → `Preparar no encontrado`; salida 1 (`false`, confirmado u otro) → `Preparar borrado fallido` |
| `Preparar borrado fallido` | `n8n-nodes-base.set` **3.5** | `assignments`: `calendar_ok=false` (boolean), `calendar_http_code=null` (number/empty), `cancellation_detail="http_error_unknown"` (string); `includeOtherFields: true`; `options: {}` |
| `Preparar no encontrado` | `n8n-nodes-base.set` **3.5** | `assignments`: `calendar_ok=true` (boolean), `calendar_http_code=null` (number/empty), `cancellation_detail="not_found"` (string); `includeOtherFields: true`; `options: {}` |

**Cadena final de la rama de cancelación** (se detallan los nodos que cambian;
las conexiones completas están en §9.5.2):

```text
Preparar cancelación
  -> Consulta
  -> ¿Fila de creación encontrada?
  -> ¿Cancelación ya completada?
  -> If1 (calendar_event_id no vacío)
  -> Elimina cita                                  [googleCalendar delete]
       ├── salida 0 (éxito) -> Clasificar resultado de Calendar   [sin cambios]
       │                        -> ¿Borrado o ya eliminado? ($json.calendar_ok === true)
       │                             ├── true  -> Update row(s)2 -> Marcar cancelación completada -> (error) Update row(s)3
       │                             └── false -> Marcar cancelación fallida - creación -> Update row(s)3
       └── salida 1 (error)  -> Verificar evento   [googleCalendar get]
            ├── salida 0 (devuelve el evento) -> ¿Evento cancelado? ($json.status)
            │      ├── true  (cancelled/canceled) -> Preparar no encontrado
            │      │                                   -> ¿Borrado o ya eliminado? (true)
            │      │                                   -> Update row(s)2
            │      │                                   -> Marcar cancelación completada
            │      │                                   -> (error) Update row(s)3
            │      └── false (confirmed/otro)     -> Preparar borrado fallido
            │                                          -> Marcar cancelación fallida - creación
            │                                          -> Update row(s)3
            └── salida 1 (no existe, p. ej. 404) -> Preparar no encontrado
                                                       -> ¿Borrado o ya eliminado? (true)
                                                       -> Update row(s)2
                                                       -> Marcar cancelación completada
                                                       -> (error) Update row(s)3
```

**Contratos existentes que se preservan** (no se tocan):

- `Update row(s)2`: filtra `event_id = {{ $('Consulta').first().json.event_id }}`;
  escribe `cancellation_status='completed'`,
  `cancellation_detail={{ $json.cancellation_detail }}`, `calendar_event_id=''`.
- `Marcar cancelación completada`: filtra
  `event_id = {{ $('Preparar cancelación').first().json.event_row_id }}`; escribe
  `processing_status='completed'` (fila X).
- `Update row(s)3`: mismo filtro que la anterior; escribe
  `processing_status='failed'` (fila X).
- `Marcar cancelación fallida - creación`: filtra
  `event_id = {{ $('Consulta').first().json.event_id }}`; escribe
  `cancellation_status='failed'`,
  `cancellation_detail={{ $json.cancellation_detail }}`.
- `Elimina cita`: `googleCalendar` 1.3, `operation: delete`,
  `calendar: ingjazar@gmail.com`, `eventId: ={{ $json.calendar_event_id }}`,
  `onError: continueErrorOutput`, `retryOnFail: false`.
- `Clasificar resultado de Calendar` y `¿Borrado o ya eliminado?`: **sin
  cambios**; el clasificador solo procesa la salida 0 de `Elimina cita`.

**Por qué no se clasifica por el texto del error.** El mensaje del nodo es genérico
y no contiene código; cualquier heurística (p. ej. asignar `not_found` a todo error
del nodo Calendar) marcaría como **completada** una cancelación que en realidad
falló por 400/401/403 (falso positivo) y rompería RF-8/RF-10. El `status` del
evento devuelto es un **hecho observable**: si es `cancelled`/`canceled`, el
borrado ya se aplicó (Google lo marca antes de purgarlo); si es `confirmed` u otro
estado, el borrado no se aplicó; si el `Get` falla porque el recurso no existe, el
evento ya no está. Alternativas descartadas en **D-E13/D-E14** (§9.5.7): heurística
textual, HTTP Request (bloqueado por la plataforma, D-007-02) y confiar en la mera
existencia (v4, no cumple RF-10).

**Alcance del cambio.** La corrección 3 **retira** una conexión (`Elimina cita`
salida 1 → `Clasificar resultado de Calendar`), **añade cinco** y **tres nodos**
(`Verificar evento`, `Preparar borrado fallido`, `Preparar no encontrado`). La
corrección 4 sustituye `Verificar evento` salida 0 → `Preparar borrado fallido` por
`Verificar evento` salida 0 → `¿Evento cancelado?` y añade las dos salidas del If
(§9.5.2), con **+1 nodo** (`¿Evento cancelado?`). **No se modifica ningún nodo
existente.** Total: **48 nodos** (42 − 7 + 9 + 3 + 1). No se introduce vocabulario nuevo
de `cancellation_detail`: se reutilizan `not_found` y `http_error_unknown`
(RF-12/D4 intactos).

**Riesgo propio de la verificación (R6, §9.8).** Un `Get` que devuelve un evento
**cancelado** ya no se interpreta como «existe» (cuenta como borrado aplicado);
el riesgo residual es que un `Get` falle por red, credencial o cuota y se
interprete como `not_found`. Se mitiga con la verificación manual de T20-B (el
evento debe estar realmente cancelado o ausente en Google Calendar).

#### 9.5.7 Decisiones técnicas de la enmienda (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| **D-E1** | **n8n es el único ejecutor**; backend sin cambios | La Spec 010 ya emite el evento v1 con el contrato y la autenticación; duplicar la lógica en Flask rompería la separación y exigiría spec/plan de backend | *Persistir `calendar_event_id` en SQLite*: fuera de alcance y decidido en contra (spec 007) | RF-8 |
| **D-E2** | **Solo dos columnas nuevas** (`cancellation_status`, `cancellation_detail`) | D3/D4; separa los tres estados sin tocar las columnas existentes y sin migrar nada | *Reutilizar `processing_status`*: fusiona estados (prohibido por RF-12). *Tabla nueva*: más superficie y otra fuente de verdad | RF-12, RF-8 |
| **D-E3** | **Cadena única** con convergencia en `Preparar cancelación` y eliminación de la rama de reintento duplicada | Evita que normal y reintento diverjan (requisito explícito del encargo); reduce nodos y reglas duplicadas | *Mantener dos ramas espejo*: riesgo de correcciones asimétricas. *Sub-workflow*: otra pieza que versionar/importar y más riesgo operativo | RF-8, RF-10, RF-11 |
| **D-E4** | **Clasificador Code + IF booleano** para 404/410, con `retryOnFail:false` en `Elimina cita` | El nodo de Google Calendar expone el error por la salida de error; una regla única y explícita evita bucles de 404. **Vigente solo para la salida de éxito desde la corrección 3**: la rama de error se resuelve por verificación del `status`/ausencia del evento (**D-E13/D-E14**) | *IF directo sobre `$json.error.httpCode`*: frágil ante variantes del error. *Dejar que n8n reintente*: reproduce el bucle del gap 3 | RF-10 |
| **D-E5** | **Limpiar `calendar_event_id` tras completar** (D1) | Idempotencia: un reintento no vuelve a borrar un ID muerto; `cancellation_status` conserva el resultado | *Conservar el ID*: el reintento repetiría la llamada a Calendar en cada entrega (404) y dependería solo del clasificador | RF-10 |
| **D-E6** | **Guarda `¿Cancelación ya completada?` antes de `If1`** | Si la cancelación ya se completó (y el ID se limpió), el reintento debe cerrar la fila del evento, no tratarla como «sin ID» (`skipped`) | *Confiar solo en `If1`*: tras limpiar el ID, un reintento se marcaría `skipped` erróneamente | RF-10 |
| **D-E7** | **Skip con motivo en la fila disponible** (fila de creación; si no existe, fila del evento) | RF-11 exige registrar el caso; sin fila de creación la única fila es la del evento | *No registrar nada*: reproduce el gap 1. *Crear una fila sintética*: inventa datos y rompe el dedupe | RF-11 |
| **D-E8** | **Preservar IDs, `typeVersion`, posiciones, credenciales y `webhookId`**; UUID nuevos solo en nodos/condiciones nuevas | Permite importar sin romper referencias de credenciales ni el webhook de producción y minimiza el diff revisable | *Regenerar el workflow desde cero*: pierde IDs, credenciales y trazabilidad | Todos |
| **D-E9** | **Versionar el JSON parcheado en `docs/workflows/hu-007/`** (§9.9) | Deja el artefacto revisable y reproducible junto a la spec, sin secretos | *Dejarlo solo en `Downloads`*: no es trazable ni reproducible | Trazabilidad |
| **D-E10** | **Sin migración histórica ni cambios de entorno** | AGENTS.md exige decisión explícita para sanear datos; esta enmienda no la tiene (OQ-4). No hay variables nuevas | *Normalizar `'cancelled'` a `'completed'`*: decisión de datos no aprobada | RF-12 |
| **D-E11** | **Evidencia E2E manual** (n8n no es Python) + suite de regresión del backend | La lógica nueva vive en n8n; inventar tests Python no probaría el workflow. La suite protege el contrato de la Spec 010 | *Tests automáticos del JSON*: validan forma, no comportamiento real de Calendar/n8n | RF-8..RF-13 |
| **D-E12** | **Restaurar el nodo `googleCalendar` en `Elimina cita` (configuración del v1) y endurecer el clasificador para leer el `error` en cualquier forma** (campos estructurados, string legacy `404 - "Not Found"` o error serializado) | El E2E-B repetido con el JSON v2 (2026-11-02) falló con `This credential is configured to prevent use within an HTTP Request or GraphQL node`: **n8n Cloud prohíbe la credencial OAuth2 de Google Calendar en nodos HTTP Request/GraphQL**, la petición no llega a Google y no hay código HTTP. La opción A (HTTP Request) no es viable por **restricción de plataforma**, no de diseño. `googleCalendar` es el nodo soportado para borrar eventos con esa credencial; el clasificador se endurece para recuperar el código de cualquier forma del error y restablecer RF-10/RF-8. Se conservan nombre, conexiones y credencial | *Mantener el HTTP Request con la credencial predefinida*: bloqueado por n8n Cloud (fallo real del v2, D-007-02). *Reimplementar OAuth2 con token propio en un HTTP Request*: exige gestionar/rotar credenciales, duplica lo que ya hace n8n y sale del alcance aprobado. *Mapear el mensaje genérico a `not_found`*: enmascararía un 401/403 real como «ya eliminado» y marcaría `completed` una cancelación no realizada. **Superada en la rama de error por D-E13**: el JSON v3 demostró que el nodo oculta el código (`calendar_http_code: null`) y ningún refinamiento del clasificador puede decidir el 404 | RF-10, RF-8 |
| **D-E13** | **Verificar la existencia del evento tras un borrado fallido** (`Verificar evento` = `googleCalendar` **get**) en lugar de clasificar por el texto del error | El nodo `googleCalendar` **oculta el código HTTP**: el error es `Your request is invalid or could not be processed by the service` y `calendar_http_code` queda `null`; interpretar el texto no distingue 404 de 400/403, así que la rama de error **no puede cumplir RF-10**. La existencia es un hecho observable: si el `Get` **devuelve** el evento, el borrado falló de verdad (`failed` + `http_error_unknown`); si el `Get` **falla** porque el recurso no existe, el evento ya no está (`completed` + `not_found`). Reutiliza los motivos existentes (RF-12/D4 intactos). **Superada en la interpretación de «devuelve el evento» por D-E14**: un evento `cancelled` ya está borrado aunque la API aún lo devuelva | *Heurística textual* (asignar `not_found` a todo error del nodo Calendar): falsos positivos ante 400/401/403, marcaría `completed` cancelaciones no realizadas y rompería RF-8/RF-10. *Nodo HTTP Request con la credencial Google Calendar*: bloqueado por n8n Cloud (D-007-02/D-E12). *Seguir afinando el clasificador*: no hay código que leer; iteraciones sin salida (R5) | RF-10, RF-8 |
| **D-E14** | **Verificar el `status` del evento devuelto** por `Verificar evento` (`¿Evento cancelado?`: `cancelled`/`canceled` → borrado aplicado; `confirmed`/otro → fallo real) en lugar de la **mera existencia** | La ejecución con el JSON v4 sobre la cita 32 (evento borrado a mano) demostró que `events.get` **sí devuelve el evento**, con `status: "cancelled"` y el mismo `id`: Google lo marca como cancelado **antes de purgarlo** y deja de mostrarlo en el calendario visual. Con la corrección 3, «el `Get` devuelve el evento» se interpretaba como «sigue existiendo» y marcaba `failed` un borrado ya aplicado (falso negativo, RF-10 incumplido). El `status` es un hecho observable y distingue el evento cancelado (borrado aplicado) del confirmado (borrado fallido); el If normaliza a minúsculas y acepta `cancelled` y `canceled`. Reutiliza los motivos existentes (RF-12/D4 intactos) | *Confiar en la mera existencia* (v4): el evento cancelado que la API aún devuelve se marca `failed` y no cumple RF-10. *Interpretar el texto del error*: sin código, no distingue 404 de 400/403 (D-E13). *Tratar todo `Get` con éxito como `not_found`*: marcaría `completed` un borrado que falló con el evento activo (falso positivo, rompe RF-8) | RF-10, RF-8 |

### 9.6 Matriz de estados esperados por escenario

Filas de la misma cita: **C** = fila de creación (`appointment.confirmed`),
**X** = fila del evento `appointment.cancelled`, **E** = fila del evento
`appointment.cancellation_email` (no se modifica).

| Escenario | C `processing_status` | C `cancellation_status` | C `cancellation_detail` | C `calendar_event_id` | X `processing_status` | Llamada a Calendar |
|---|---|---|---|---|---|---|
| **A. Cancelación normal** | `completed` (sin cambios) | `completed` | vacío | **vacío** (limpiado) | `completed` | 1 borrado 2xx (0 `Get`) |
| **B. Ya eliminado (cancelado o 404)** | `completed` | `completed` | `not_found` | **vacío** | `completed` | 1 borrado (error) + 1 `Get` (éxito con `status: cancelled`, o error 404) |
| **C. Reintento tras completar** | `completed` | `completed` | `not_found` o vacío (no se reescribe) | vacío | `failed` → `completed` | **0** (guarda D-E6) |
| **D. Sin fila de creación** | *(no existe)* | `skipped` (en **X**) | `no_creation_record` (en **X**) | — | `completed` | **0** |
| **E. Sin `calendar_event_id`** | `completed` | `skipped` | `missing_calendar_event_id` | vacío | `completed` | **0** |
| **F. Error real (el evento sigue confirmado)** | `completed` | `failed` | `http_error_unknown` | sin cambios | `failed` | 1 borrado (error) + 1 `Get` (éxito con `status: confirmed`) |

Con la corrección 4, **B y F se distinguen por el `status` del evento devuelto**,
no por el código HTTP ni por la mera existencia: en B el `Get` de `Verificar
evento` **falla** (404) o **devuelve el evento con `status: cancelled`**
(`¿Evento cancelado?` true); en F el `Get` **devuelve el evento con `status:
confirmed`** (`¿Evento cancelado?` false) y el fallo es real. `Failed` en F es
elegible para reintento; `completed` en B es terminal.

La fila **E** conserva su `email_processing_status` independiente (normalmente
`completed` o vacío, según el envío del correo) y la fila **C** conserva el
`processing_status='completed'` de la creación: son los tres estados separados
de RF-12.

En la fila **X**, `processing_status='completed'` significa «evento de
cancelación atendido», **no** «borrado completado»: el resultado del borrado se
lee en `cancellation_status`/`cancellation_detail` de la fila C (o de X en el
caso D).

### 9.7 Estrategia de pruebas

#### 9.7.1 Automatizada (`pytest`) — contrato del backend, ya existente

No se añaden tests: la funcionalidad nueva es de n8n y no hay código Python que
cambiar. La suite existente ya cubre el contrato que consume esta enmienda
(evento `appointment.cancelled` v1, sin PII, `event_id` determinista,
publicación/registro en `automation_events`).

Comandos y criterio:

```powershell
python -m pytest -q
git diff --name-only main...HEAD   # sin archivos de código por esta enmienda
```

- **Criterio**: `0 FAIL` y ningún archivo de `consultorio/` o `tests/`
  modificado por T16–T22. El conteo real se registra en la evidencia (no se
  hardcodea: `MEMORY.md` registra 302 tras D-010-01, verificar al iniciar).
- Prohibido relajar/omitir aserciones para «pasar» (pytest-qa).

#### 9.7.2 Manual E2E en n8n (escenarios A–E obligatorios; F opcional)

Precondiciones: workflow **activo** (el nuevo), columnas creadas, backend local
con `AUTOMATION_WEBHOOK_URL` apuntando a la **URL de producción** del webhook
(`/webhook/hu-007-cita-creada`, no `webhook-test`) y `AUTOMATION_WEBHOOK_AUTH_HEADER`
con el token del entorno (nunca en la evidencia). Usar citas de prueba con
fechas futuras y nombres inequívocos de prueba; no tocar Render ni la BD de
producción.

| ID | Escenario | Pasos mínimos | Resultado esperado |
|---|---|---|---|
| **E2E-A** | Cancelación normal | Crear cita de prueba (el flujo crea el evento de Calendar) → anotar `appointment_id` y el `calendar_event_id` de la fila C → cancelar desde la app (ruta de HU-017) → revisar filas y Calendar | Estado A de §9.6; el evento desaparece de Google Calendar; 1 ejecución de n8n con el nodo `Elimina cita` en éxito |
| **E2E-B** | Ya eliminado (idempotente) | Crear cita de prueba → borrar **a mano** su evento en Google Calendar → cancelar → revisar | Estado B; `completed` + `not_found`; sin `failed`; `Elimina cita` en error y `Verificar evento` devuelve el evento con `status: cancelled` (o falla con 404) → `¿Evento cancelado?` true → `not_found` |
| **E2E-C** | Reintento tras completar | Sobre la cita de E2E-B, poner a mano `X.processing_status='failed'` (fila de prueba) → reenviar el **mismo** payload `appointment.cancelled:{id}:v1` con la cabecera → revisar | Estado C; el reintento **no** llega a `Elimina cita` (guarda); `X` queda `completed`; 0 borrados nuevos |
| **E2E-D** | Sin fila de creación | Enviar a mano `appointment.cancelled:999999:v1` (id inexistente, payload válido v1) → revisar | Estado D; `skipped` + `no_creation_record`; 202 del webhook; 0 llamadas a Calendar; el caso no queda en `received` |
| **E2E-E** | Sin `calendar_event_id` | Elegir una cita de prueba cuya fila C tenga `calendar_event_id` vacío (o vaciarlo en una fila de prueba) y cancelarla → revisar | Estado E; `skipped` + `missing_calendar_event_id`; 0 llamadas a Calendar; `X` `completed` |
| **E2E-F** | Error real con el evento presente (**opcional, no bloqueante**) | Simular un fallo de borrado con el evento aún existente (p. ej. un `eventId` con formato inválido que devuelva 400, o una copia con un permiso insuficiente) → revisar | Estado F; `failed` + `http_error_unknown` (el `Get` de `Verificar evento` **devuelve el evento con `status: confirmed`** → `¿Evento cancelado?` false); `X` `failed` → elegible para reintento; no se pierde la cita |

E2E-F **no es bloqueante**: si no se ejecuta, el estado `failed` queda cubierto
por la matriz de diseño (§9.6) y por la suite del backend, no por evidencia E2E.

**Repetición de E2E-B (corrección 4, D-E14):** se ejecuta sobre la **cita 32**,
cuyas filas ya existen en estado `failed`; el reenvío de
`appointment.cancelled:32:v1` valida el E2E-B y la rama de reintento a la vez. La
repetición debe comprobar **las tres ramas** de la verificación:

- **(a) evento cancelado** (borrado a mano antes de cancelar) → `Elimina cita` en
  error → `Verificar evento` devuelve el evento con `status: cancelled` →
  `¿Evento cancelado?` true → `Preparar no encontrado` → C queda `completed` +
  `not_found` + `calendar_event_id=''`.
- **(b) error 404** → `Verificar evento` falla y no devuelve evento →
  `Preparar no encontrado` → C queda `completed` + `not_found` +
  `calendar_event_id=''`.
- **(c) evento confirmado** → el borrado falla dejando el evento `confirmed` →
  `Verificar evento` lo devuelve → `¿Evento cancelado?` false →
  `Preparar borrado fallido` → C queda `failed` + `http_error_unknown` y
  `calendar_event_id` sin cambios.

Ni la ejecución 13 (D-007-01), ni el intento con el JSON v2 (HTTP Request), ni la
ejecución con el JSON v3 (error genérico, `calendar_http_code: null`), ni el
intento con el JSON v4 (el evento cancelado se interpretaba como existente)
cuentan como PASS. El PASS válido es la ejecución con el **JSON v5** (corrección 4,
T18).

Comprobaciones transversales:

- **RF-13**: en la ejecución de E2E-A, la rama de `appointment.cancellation_email`
  se procesa (correo) y **no** invoca `Elimina cita`.
- **RF-12**: exportar las tres filas (C, X, E) de la misma cita y comprobar que
  los tres estados son columnas distintas.
- **RF-9**: en el CSV previo, C conserva `appointment_id` y `calendar_event_id`;
  en el posterior a un borrado completado, `calendar_event_id` está vacío y
  `cancellation_status='completed'` (D1).

#### 9.7.3 Evidencia (qué se guarda y dónde)

Carpeta propuesta: `docs/evidencias/hu-007/enmienda-2026-11-01/` (separada de la
evidencia de 2026-10-10):

| Archivo | Contenido |
|---|---|
| `datatable-antes.csv` | Export CSV de la data table antes de los escenarios (cabeceras nuevas + filas de prueba) |
| `datatable-despues.csv` | Export CSV tras A–E (y F si se ejecutó), con las filas C/X/E de las citas de prueba |
| `ejecuciones.md` | ID de ejecución de n8n por escenario, fecha/hora, nodo final, resultado PASS/FAIL, incidencias |
| `qa-hu-007-enmienda-2026-11-01.md` | Informe QA: matriz RF-8..RF-13, escenarios, PASS/FAIL, checkboxes de aceptación y trazabilidad |
| `captura-columnas.png` (opcional) | Configuración de `cancellation_status`/`cancellation_detail` en la UI |

Cada fila de evidencia sigue el formato ya usado en HU-007:

```text
HU: HU-007 (enmienda 2026-11-01)
Escenario: E2E-B (404 idempotente)
Ejecución n8n: <id>
Resultado: PASS
Filas: C=<appointment_id> / X=<event_id>
Evidencia: datatable-despues.csv (fila X, cancellation_status)
```

**No** se guardan tokens, cabeceras de autenticación ni datos de pacientes en
los CSV (la data table no contiene PII por diseño; verificar igualmente antes de
versionar el export).

### 9.8 Riesgos y mitigaciones

| # | Riesgo | Impacto | Mitigación |
|---|---|---|---|
| **R1** | El workflow de producción está **activo** y se edita en caliente | Una ejecución real puede usar un workflow a medio cambiar | Trabajar sobre una **copia importada inactiva**; el original se desactiva solo al activar la copia (T19/T20). No editar el activo |
| **R2** | El export trae `active:false` | Falsa sensación de que no está en producción | T16 confirma en la **UI** que está activo; `active` del export es un artefacto de serialización |
| **R3** | Columnas nuevas inexistentes al activar | Los nodos de escritura fallan; la fila queda `received`/`processing` | T17 antes de T19/T20; checkpoint explícito en el checklist §9.4.3 |
| **R4** | Credenciales/secretos | Fuga o import roto | El JSON solo lleva **referencias** de credenciales (id/nombre), nunca secretos; verificar `pinData` vacío y ausencia de tokens; el token del webhook vive solo en el entorno |
| **R5** | Forma del error de Google Calendar distinta de la esperada (`httpCode`/`statusCode`/`response.status`) | 404 no detectado → bucle de reintento (gap 3). **Materializado en la ejecución 13 (D-007-01), en el E2E-B con el JSON v2 (D-007-02) y en el E2E-B con los JSON v3 (corrección 2: `calendar_http_code: null`) y v4 (corrección 3: el evento cancelado se devuelve como existente)** | **D-E12** restauró `googleCalendar` y endureció el clasificador; la corrección 3 (**D-E13**) **deja de depender del código** y la corrección 4 (**D-E14**) **deja de depender de la mera existencia**: la detección de «ya eliminado» pasa a la verificación del `status` del evento devuelto (§9.5.6). Si `Verificar evento`/`¿Evento cancelado?` no distinguen los casos, **no se declara PASS** y se repite T20-B sobre la cita 32 |
| **R6** | Un `Get` de `Verificar evento` **devuelve el evento con `status: cancelled`** (Google lo marca antes de purgarlo) o **falla por red, credencial o cuota** | (a) con la corrección 3 (JSON v4) el evento cancelado se interpretaba como «sigue existiendo» → `failed` falso negativo; (b) un fallo de lectura se interpreta como «no existe» → `completed` + `not_found` aunque el evento siga activo | (a) **D-E14**: `¿Evento cancelado?` decide por `status` (`cancelled`/`canceled` → `not_found`; `confirmed` u otro → `failed`), **no por la mera existencia**. (b) se acepta como riesgo residual: el nodo distingue «evento leído» de «error al leer», no el motivo del error. Mitigación: verificar credenciales antes del E2E y **comprobar en T20-B** que el evento está realmente cancelado o ausente en Google Calendar; si el `Get` falla con el evento activo presente, **no se declara PASS** |
| **R7** | Pérdida del `calendar_event_id` borrado al limpiarlo (D1) | No se puede auditar qué evento se borró desde la data table | Se acepta el diseño de D1; la trazabilidad del ID queda en la ejecución de n8n. Si se necesita conservarlo, requiere columna nueva (OQ-5) |
| **R8** | Filas históricas con `processing_status='cancelled'` | Lectura ambigua de la historia | No se migran (OQ-4); se documenta en el informe QA |
| **R9** | Dos workflows con el mismo path de webhook | n8n rechaza la activación o recibe el tráfico el equivocado | Desactivar el anterior antes de activar la copia; solo uno activo con `hu-007-cita-creada` |
| **R10** | Escrituras a la data table no transaccionales (fila C y fila X) y fallo de la propia escritura de fallo | Estado inconsistente que exige revisión manual | Orden de escritura y salidas de error hacia `Update row(s)3`; la cadena es idempotente y el reintento repara estados intermedios; si falla también la escritura de `failed`, revisión manual (sin recuperación automática) |
| **R11** | Datos/eventos de prueba en Calendar y en la data table de producción | Contaminación de la tabla y del calendario de la usuaria | Citas de prueba identificables, fechas futuras, CSV de evidencia y nota de limpieza; no borrar filas históricas sin decisión (AGENTS.md) |
| **R12** | Backend local apuntando a Render | Un push a `main` redeploya y **vacía la BD**; el E2E fallaría | Usar la app local con variables de entorno de sesión; no cambiar `DATABASE_PATH` ni Render; coordinar el push de docs |
| **R13** | `Enrutar reintento por tipo` no cubre `appointment.cancellation_email` | Un reintento de correo se descarta (defecto previo) | Fuera de alcance (OQ-6); se registra como pendiente, no se corrige en esta enmienda |

### 9.9 Versionado del JSON del workflow (sin secretos)

Ruta propuesta (nueva carpeta, dentro de `docs/`):

```text
docs/workflows/hu-007/
├── n8n-hu-007-integracion-citas-2026-11-02-v5.json          # JSON vigente (T18, corrección 4 / D-E14: verificación del status, 48 nodos)
├── n8n-hu-007-integracion-citas-2026-11-02-v4.json          # v4: verificación de existencia (corrección 3 / D-E13; descartado por D-E14, histórico)
├── n8n-hu-007-integracion-citas-2026-11-02-v3.json          # v3: googleCalendar + clasificador endurecido (corrección 2; descartado por D-E13, histórico)
├── n8n-hu-007-integracion-citas-2026-11-02.json             # v2: intento con HTTP Request (D-007-01; descartado, histórico)
├── n8n-hu-007-integracion-citas-2026-11-01.json             # v1: export previo a las correcciones (histórico, referencia)
└── n8n-hu-007-integracion-citas-2026-11-01-linea-base.json # export del T16 (rollback, opcional)
```

La versión **2026-11-02-v5** es la que se importa y valida (T19/T20): mantiene
`Elimina cita` como `googleCalendar` (`typeVersion 1.3`, parámetros del v1), deja
`Clasificar resultado de Calendar` sin cambios, conserva `Verificar evento`,
`Preparar borrado fallido` y `Preparar no encontrado` y añade
**`¿Evento cancelado?`** (`n8n-nodes-base.if` 2.4, `combinator: "or"`, dos
condiciones `string equals` sobre
`={{ ($json.status ?? '').toString().toLowerCase() }}` frente a `cancelled` y
`canceled`), con **48 nodos** (§9.5.6, D-E14). La **v4** (corrección 3:
verificación de existencia) queda como histórico: el `Get` puede devolver un
evento **cancelado** y se interpretaba como existente, así que **no** debe
activarse. La **v3** (corrección 2: clasificador endurecido) también queda como
histórico: el nodo Calendar oculta el código HTTP y `calendar_http_code` resulta
`null`. La **v2** (HTTP Request, D-007-01) y la **v1** se conservan como
histórico/referencia y tampoco se activan. Ninguna versión histórica se borra.

**Checklist de validación del v5 (T18/T19):**

- [ ] El JSON parsea y `active` es `false`; `pinData` vacío; sin tokens ni
      cabeceras de autenticación.
- [ ] **48 nodos** en total (42 − 7 + 9 + 3 de la corrección 3 + 1 de la
      corrección 4).
- [ ] `¿Evento cancelado?` es `n8n-nodes-base.if` `typeVersion: 2.4`, con
      `combinator: "or"` y **dos** condiciones `string equals`:
      `leftValue: ={{ ($json.status ?? '').toString().toLowerCase() }}` frente a
      `cancelled` y frente a `canceled`.
- [ ] `Verificar evento` salida 0 → `¿Evento cancelado?`; salida 1 →
      `Preparar no encontrado`.
- [ ] `¿Evento cancelado?` salida 0 (`true`) → `Preparar no encontrado`;
      salida 1 (`false`) → `Preparar borrado fallido`.
- [ ] `Elimina cita` sigue siendo `googleCalendar` 1.3 (`delete`) con
      `onError: continueErrorOutput` y `retryOnFail: false`; `Clasificar resultado
      de Calendar` conserva el `jsCode` de §9.5.5 y solo recibe la salida 0.
- [ ] Toda conexión apunta a un nodo existente y los 13 nodos nuevos de la
      enmienda (9 + 3 de la corrección 3 + `¿Evento cancelado?`) tienen UUID
      únicos.

Reglas del artefacto:

- Se versiona el JSON **exportado** de la copia importada y verificada, no un
  fragmento ni un diff manual.
- `active` debe quedar en `false` en el archivo; la activación es un acto
  operativo en la UI (T20), no un valor del JSON.
- **Sin secretos**: el export de n8n no incluye valores de credenciales; las
  referencias (`credentials.httpHeaderAuth`, `smtp`, `googleCalendarOAuth2Api`)
  se conservan para que la importación las resuelva. Verificar `pinData` vacío y
  ausencia de cabeceras/tokens. El identificador de la cuenta de Calendar del
  resource locator es configuración de la usuaria, no un secreto; revisar que no
  haya datos de pacientes.
- El `webhookId` y el `path` (`hu-007-cita-creada`) se conservan: la URL de
  producción del backend no cambia.
- La copia de línea base permite el rollback (desactivar la nueva, activar la
  anterior) sin depender de `Downloads`.

### 9.10 Secuencia de implementación

0. **Aprobación** de este §9, de D1–D4 y de las tareas T16–T22 por la usuaria
   (bloqueante; sin ella no se toca n8n).
1. **T16** — Pre-check del export frente al workflow activo; si difiere,
   reexportar y usar el nuevo como base.
2. **T17** — La usuaria crea `cancellation_status` y `cancellation_detail`
   (§9.4.3) y exporta el CSV con las cabeceras.
3. **T18** — El implementador genera el JSON **corregido** (versión
   `2026-11-02-v5`, con `Elimina cita` como `googleCalendar` `typeVersion 1.3`,
   `Clasificar resultado de Calendar` sin cambios, los tres nodos de verificación
   y `¿Evento cancelado?`, corrección 4 / D-E14) según §9.5 y lo valida
   estructuralmente.
4. **T19** — Importar **inactivo**, revisar 48 nodos, credenciales, data table y
   mapeos de las columnas nuevas; no activar.
5. **T20** — Desactivar el workflow anterior, activar la copia y ejecutar
   E2E-A/B/C; registrar IDs. **B se repite con el JSON v5 sobre la cita 32**
   (filas ya en estado `failed`), reenviando `appointment.cancelled:32:v1`, y
   verifica **las tres ramas**: (a) evento cancelado → `not_found`; (b) error
   404 → `not_found`; (c) evento confirmado → `failed`. Ni la ejecución 13 ni
   los intentos con los JSON v2/v3/v4 cuentan como PASS.
6. **T21** — Ejecutar E2E-D/E (RF-11) y la comprobación de RF-13.
7. **T22** — Regresión (`pytest`), evidencia CSV + IDs, `qa-hu-007-enmienda-2026-11-01.md`,
   versionado del JSON y actualización de `MEMORY.md` (coordinador).
8. **Cierre** — Commit de docs/artefactos con mensaje que cite HU-007 enmienda
   2026-11-01 / RF-8..RF-13; coordinar el push (un push a `main` redeploya
   Render; esta enmienda no requiere despliegue de la app).

### 9.11 Pendientes, aprobaciones y cuestiones abiertas

**Estado de la enmienda (2026-11-04): `IMPLEMENTADO — VALIDADO TÉCNICAMENTE;
PENDIENTE DE ACEPTACIÓN FUNCIONAL`.** El único pendiente de cierre es la
aceptación funcional de la usuaria; no hay cambios técnicos pendientes.

#### Aprobaciones registradas

- [x] Aprobación de este §9 (alcance, D-E1..D-E14, §9.4, §9.5.6, §9.6) y de
      T16–T22 por la usuaria; habilita la ejecución.
- [x] **Corrección 1 — opción A (D-007-01):** aprobada **2026-11-02** (sustituir
      `Elimina cita` por un HTTP Request). **Descartada técnicamente el
      2026-11-02 por D-007-02**: n8n Cloud rechaza la credencial OAuth2 de Google
      Calendar en nodos HTTP Request/GraphQL (`This credential is configured to
      prevent use within an HTTP Request or GraphQL node`); la petición nunca
      llega a Google.
- [x] **Corrección 2 — restaurar `Elimina cita` como `googleCalendar` y endurecer
      el clasificador (v3, D-007-02):** aprobada **2026-11-02**. Sigue vigente el
      nodo `n8n-nodes-base.googleCalendar` (`typeVersion 1.3`, parámetros del v1,
      `onError: continueErrorOutput`, `retryOnFail: false`) y el `jsCode` de
      §9.5.5; queda **superada en la rama de error** por la corrección 3 (el nodo
      oculta el código HTTP). El JSON **v3** es histórico y **no** se activa.
- [x] **Corrección 3 — verificar la existencia del evento (v4, D-E13):** aprobada
      **2026-11-04**. Añade `Verificar evento` + `Preparar borrado fallido` +
      `Preparar no encontrado`; queda **superada por la corrección 4** (la mera
      existencia no basta). El JSON **v4** es histórico y **no** se activa.
- [x] **Corrección 4 — verificar el `status` del evento devuelto (v5, D-E14):**
      aprobada **2026-11-04**. Añade `¿Evento cancelado?` (`n8n-nodes-base.if`
      2.4, `combinator: "or"`, dos `string equals` sobre
      `={{ ($json.status ?? '').toString().toLowerCase() }}` frente a `cancelled`
      y `canceled`): true → `Preparar no encontrado`; false → `Preparar borrado
      fallido`. Evidencia: ejecución con el JSON v4 sobre la cita 32 (evento
      borrado a mano) → `events.get` devuelve el evento con `status: "cancelled"`
      y el mismo `id`; el evento ya no está en el calendario visual, pero la API lo
      entrega como cancelado antes de purgarlo. Documentado en **D-E14**, §9.5.6,
      §9.8/R6 y §9.9.
- [x] Precondiciones del E2E confirmadas y ejecutadas: calendario real de la
      usuaria con citas de prueba identificables; el token del webhook se toma del
      entorno y no se registra en la evidencia.
- [x] Línea base del workflow: no se versiona; el inventario aceptado de
      artefactos es **v1–v5** (§9.9 y tabla siguiente).

#### Inventario de artefactos validados (`docs/workflows/hu-007/`)

| Versión | Archivo | Nodos | SHA-256 | Estado |
|---|---|---|---|---|
| v1 | `n8n-hu-007-integracion-citas-2026-11-01.json` | 44 | `E69483C96EFFC22AEE48FC2575B615338CD3961762F9D3E8391320A135598E77` | Histórico / referencia |
| v2 | `n8n-hu-007-integracion-citas-2026-11-02.json` | 44 | `EB5429CF918AD764E188054522627E1D16A1EAA82E4D619AA7030A2F4EB33C9B` | Histórico (HTTP Request, D-007-01) |
| v3 | `n8n-hu-007-integracion-citas-2026-11-02-v3.json` | 44 | `5E7BE441E420C5A58193E17F5373BCEBC026EEF4E98E915F55B497F446088D52` | Histórico (corrección 2) |
| v4 | `n8n-hu-007-integracion-citas-2026-11-02-v4.json` | 47 | `E80D4EBECA7B7275671FC5AF45022CFFD31ED438630FD9F45719E02FACEE05AB` | Histórico (corrección 3) |
| **v5** | `n8n-hu-007-integracion-citas-2026-11-02-v5.json` | **48** | `8918306709c0e13132861cea04cc2d7ff98dded6d7f005c94e4f5e02f3dfb766` | **Validado** (corrección 4); artefacto de referencia |

La **v5** es el artefacto validado (48 nodos); v1–v4 se conservan como histórico
y **no** se activan. Los hashes completos de v1–v4 constan en el informe QA §1 y
en `D-007-01`; el de v5 es el registrado en `ejecuciones.md`.

#### Validación técnica y desviación aceptada

- **E2E sobre v5:** escenarios **A, B, C, D y E PASS**; suite del backend
  **302 passed** (`python -m pytest -q`).
- **Revisión técnica (2026-11-04):** veredicto `CAMBIOS NECESARIOS` **solo por
  documentación**; los huecos quedaron cerrados (informe QA, `ejecuciones.md`,
  `D-007-01`, `MEMORY.md`).
- **Desviación aceptada (2026-11-04):** `calendar_http_code` **no se asigna** en
  los dos nodos Set (`Preparar borrado fallido` y `Preparar no encontrado`), a
  diferencia de lo descrito en §9.5.6. Se acepta porque el campo **no se consume
  aguas abajo** (`¿Borrado o ya eliminado?` lee `calendar_ok`); la decisión se
  toma por `calendar_ok`/`cancellation_detail` y por el `status` del evento, y no
  afecta a RF-8..RF-13.
- **Pendiente único:** **aceptación funcional de la usuaria** (no bloquea la
  validez técnica ya registrada).

#### Constancia de las correcciones 1 y 2 (2026-11-02) — histórica

- **Defecto:** `docs/defectos/D-007-01.md` (estado `ABIERTO`). Dos hallazgos:
  (a) **ejecución n8n 13** (E2E-B): el nodo `googleCalendar` entregó `error`
  como string sin código HTTP → la fila de creación quedó
  `cancellation_status='failed'` + `cancellation_detail='http_error_unknown'` y
  `calendar_event_id` no se limpió; (b) **E2E-B con el JSON v2**: la opción A no
  es viable porque n8n Cloud rechaza la credencial OAuth2 de Google Calendar en
  HTTP Request/GraphQL (`This credential is configured to prevent use within an
  HTTP Request or GraphQL node`); la petición nunca llega a Google.
- **Causa raíz real (D-007-02):** restricción de plataforma de n8n Cloud, no un
  defecto del clasificador ni del payload.
- **Cambios documentales aplicados:** §9.5.1 (nodo restaurado y configuración
  exacta), §9.5.4 (historial y verificación), §9.5.5 (`jsCode` endurecido),
  §9.5.7 (**D-E12**), §9.8/R5, §9.9 (v3) y esta sección.
- **Pendiente de ejecución (no son cambios documentales):** T18 regenera el JSON
  **v3**; T19 lo importa inactivo; **T20-B se repite sobre la cita 32**
  (reenvío de `appointment.cancelled:32:v1`) y solo entonces puede declararse
  PASS. Ni la ejecución 13 ni el intento con el JSON v2 cuentan como PASS.
- **Datos:** las filas de la ejecución 13 y del intento v2 quedan en `failed`;
  su saneamiento **no** se decide aquí (AGENTS.md: decisión explícita, respaldo y
  auditoría). Se anota en D-007-01 como pendiente fuera de alcance.
- **Acciones sobre `docs/defectos/D-007-01.md`:** el planificador no puede
  modificar archivos fuera de `specs/`; el coordinador debe actualizar ese
  registro con la causa raíz real y mantener el estado `ABIERTO`.

#### Constancia de la corrección 3 (2026-11-02)

- **Defecto:** `docs/defectos/D-007-01.md` (estado `ABIERTO`). **Tercer
  hallazgo:** en el E2E-B con el JSON **v3** (cita 32), el nodo `googleCalendar`
  entregó `error: "Your request is invalid or could not be processed by the
  service"`, **sin código 4xx/5xx** en los campos del ítem ni en su serialización
  (`calendar_http_code: null`). El nodo **oculta el código HTTP**: ninguna
  heurística textual puede distinguir 404 de 400/403 y el clasificador de §9.5.5
  no puede cumplir RF-10.
- **Decisión (aprobada por la usuaria, 2026-11-02):** **verificar la existencia**
  del evento con un `Get` (`Verificar evento`) tras un borrado fallido, en lugar
  de interpretar el error (D-E13).
- **Cambios documentales aplicados:** nota de cabecera de §9, §9.5.1 (+3 nodos y
  contratos exactos), §9.5.2 (conexiones finales y delta), §9.5.3
  (`Verificar evento`), §9.5.4 (historial y comportamiento vigente),
  §9.5.5 (nota de alcance; `jsCode` sin cambios), **§9.5.6** (nuevo:
  verificación de existencia), §9.5.7 (**D-E13**), §9.6 (filas A/B/F), §9.7.2
  (E2E-B y repetición), §9.8 (**R6**; R7–R13 renumerados), §9.9 (v4), §9.10,
  §9.11 y esta constancia. La sección «Equivalencia rama normal ↔ rama de
  reintento» pasa a §9.5.2.
- **Pendiente de ejecución (no son cambios documentales):** T18 regenera el JSON
  **v4** (47 nodos); T19 lo importa inactivo; **T20-B se repite sobre la cita 32**
  (reenvío de `appointment.cancelled:32:v1`) verificando (a) evento borrado →
  `not_found` y (b) evento existente con borrado exitoso → `completed` sin
  `not_found`. Solo entonces puede declararse PASS. Ni la ejecución 13 ni los
  intentos con los JSON v2/v3 cuentan como PASS.
- **Datos:** las filas de la ejecución 13, del intento v2 y del intento v3 quedan
  en `failed`; su saneamiento **no** se decide aquí (AGENTS.md: decisión
  explícita, respaldo y auditoría). Se anota en D-007-01 como pendiente fuera de
  alcance.
- **Acciones sobre `docs/defectos/D-007-01.md`:** el planificador no puede
  modificar archivos fuera de `specs/`; el coordinador debe registrar el tercer
  hallazgo y la decisión D-E13, manteniendo el estado `ABIERTO` hasta que T20-B
  dé PASS.

#### Constancia de la corrección 4 (2026-11-02)

- **Defecto:** `docs/defectos/D-007-01.md` (estado `ABIERTO`). **Cuarto
  hallazgo:** en la ejecución con el JSON **v4** sobre la **cita 32** (evento
  borrado a mano), `Elimina cita` (`delete`) falla y n8n oculta el código, pero
  `Verificar evento` (`events.get`) **sí devuelve el evento**, con
  `status: "cancelled"` y el mismo `id`. El evento no aparece en el calendario
  visual del usuario, pero la API lo devuelve como cancelado (Google lo marca
  antes de purgarlo). La corrección 3 interpretaba «el `Get` devuelve el evento»
  como «sigue existiendo» y marcaba `failed` un borrado ya aplicado: la
  **existencia sola no basta**.
- **Decisión (aprobada por la usuaria, 2026-11-02):** la verificación comprueba
  el **`status`** del evento devuelto (D-E14); `cancelled`/`canceled` → borrado
  aplicado (`not_found`), `confirmed`/otro → fallo real (`failed`).
- **Cambios documentales aplicados:** nota de cabecera de §9, §9.2/D1, §9.3/RF-10,
  §9.5.1 (nodo `¿Evento cancelado?` y total de 48), §9.5.2 (conexiones y delta),
  §9.5.3, §9.5.4 (historial, comportamiento vigente y T20-B), §9.5.5 (referencia),
  **§9.5.6** (tabla de decisión de cuatro resultados y diagrama), §9.5.7
  (**D-E14**; D-E13 marcada como superada en la interpretación), §9.6 (filas B/F),
  §9.7.2 (E2E-B y las tres ramas), §9.8 (**R5/R6**), §9.9 (**v5** y checklist),
  §9.10, §9.11 y esta constancia.
- **Ejecutado (2026-11-04):** T18 generó el JSON **v5** (48 nodos); T19 lo
  importó inactivo y se activó; **T20-B se repitió sobre la cita 32**
  (reenvío de `appointment.cancelled:32:v1`) con **PASS**. Ni la ejecución 13 ni
  los intentos con los JSON v2/v3/v4 cuentan como PASS.
- **Datos:** las filas de la ejecución 13 y de los intentos v2/v3/v4 quedan en
  `failed`; su saneamiento **no** se decide aquí (AGENTS.md: decisión explícita,
  respaldo y auditoría). Se anota en D-007-01 como pendiente fuera de alcance.
- **Acciones sobre `docs/defectos/D-007-01.md`:** actualizado por el coordinador
  (2026-11-04) con el cuarto hallazgo y D-E14; estado
  `CORREGIDO — PENDIENTE DE VALIDACIÓN` (pendiente solo la aceptación funcional).

#### Cuestiones abiertas — histórico (resueltas al cierre, 2026-11-04)

**Estado al cierre:** OQ-1..OQ-6 quedaron resueltas por el diseño implementado y
las aprobaciones registradas: OQ-1 se escriben en la fila X cuando no hay fila de
creación (escenario D PASS); OQ-2 `completed` + `not_found` (escenario B PASS);
OQ-3 `http_error_unknown` admitido y usado en los fallos reales; OQ-4 sin
saneamiento histórico; OQ-5 se acepta la limpieza del `calendar_event_id` (traza
en la ejecución de n8n); OQ-6 fuera de alcance. Se conservan los enunciados como
histórico.

- **[RESUELTA] OQ-1** — Ubicación de `cancellation_status`/
  `cancellation_detail` en el caso **sin fila de creación**: no existe fila de
  creación. Propuesta: escribirlas en la fila del evento `appointment.cancelled`.
  Alternativa: no registrarlas (incumpliría RF-11).
- **[RESUELTA] OQ-2** — Detalle en 404/410: D4 lista `not_found` pero
  también dice «vacío si completado». Propuesta: `completed` + `not_found` (D1).
  Alternativa: `completed` + vacío.
- **[RESUELTA] OQ-3** — Si n8n no expone el código HTTP en el error,
  ¿se admite el motivo `http_error_unknown` (propuesto) o se prefiere otro
  formato (`http_error_0`)? D4 solo fija `http_error_<code>`. **Nota
  (2026-11-02, corrección 3):** el nodo `googleCalendar` **oculta** el código
  (`calendar_http_code: null`), así que `http_error_unknown` pasa a ser el motivo
  **efectivo** de los fallos reales (lo asigna `Preparar borrado fallido`) y
  `not_found` se obtiene por la verificación del `status`/ausencia del evento
  (D-E14). La usuaria
  aprueba reutilizar `not_found` y `http_error_unknown` sin vocabulario nuevo
  (RF-12/D4 intactos); el uso de `http_error_unknown` quedó ratificado en la
  aprobación de la corrección 4 (2026-11-04).
- **[RESUELTA] OQ-4** — Filas históricas con
  `processing_status='cancelled'`: ¿se dejan como historia (propuesto, sin
  saneamiento) o se normalizan a `completed`? AGENTS.md exige decisión explícita
  y respaldo para tocar datos históricos.
- **[RESUELTA] OQ-5** — D1 limpia `calendar_event_id` y se pierde el
  ID del evento borrado en la data table. ¿Se acepta (la traza queda en la
  ejecución de n8n) o se añade una columna `calendar_deleted_event_id` (requiere
  nueva decisión y columna)?
- **[RESUELTA] OQ-6** — `Enrutar reintento por tipo` no tiene rama
  para `appointment.cancellation_email` (defecto previo): ¿se deja fuera de esta
  enmienda (propuesto) o se abre una corrección aparte?

#### Pendientes de otras fases (no bloquean esta enmienda)

- Actualización del plan 018 para filtrar por `event_type` al implementar
  RF-8..RF-10 de la 010 (anotado en `MEMORY.md`).
- Cualquier normalización histórica de la data table (OQ-4).
