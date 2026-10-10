# Plan 007 — Automatización de reservas mediante n8n

> Trazabilidad: **HU-007 → Spec 007 (`specs/007_automatizacion-reservas/spec.md`) →
> este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs`.
> Etapa actual: **HU-007 ACEPTADA Y CERRADA** (2026-10-10); **enmienda 2
> (2026-10-10): cabecera de autenticación opcional `AUTOMATION_WEBHOOK_AUTH_HEADER`
>** (Q7, decisión D14) — pendiente de implementar/evidenciar (task T15). Decisiones
> Q1–Q5 respondidas por la usuaria (2026-10-10): webhook genérico a n8n, payload sin
> datos personales, POST síncrono con timeout corto, registro en tabla
> `automation_events` y sin reintento automático. **Enmienda de la spec 007
> confirmada (2026-10-10)**. QA **PASS** en `docs/evidencias/hu-007/qa-hu-007.md`
> (12/12 TC, suite **146 PASS / 0 FAIL**); merge a `main`.
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
