# Plan 010 — Notificar la cancelación de una cita

> Trazabilidad: **HU-010 → Spec 010 (`specs/010_notificar-cancelacion/spec.md`) →
> este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs`.
> Etapa actual: **plan APROBADO (2026-10-13) y spec 010 ENMENDADA (T2,
> 2026-10-13)**. Decisiones de la usuaria
> (2026-10-13): trigger de cancelación **servicio mínimo sin UI** (Q1), canales
> **solo correo por ahora** con WhatsApp pendiente de Spec 009 (Q2), **literales
> propuestos en el plan** para su aprobación (Q3) y **el horario cancelado se
> libera** (Q4). Spec 010 **pendiente de enmienda** (D16): cerrar las dos dudas
> `[NECESITA ACLARACIÓN]` y fijar trigger, liberación de horario y migración.
> Baseline verificado en `main` (2026-10-13): **187 PASS / 0 FAIL**
> (`python -m pytest -q`).
>
> **Fase 2 — RF-8..RF-15 (enmienda 2 de la spec, aprobada por la usuaria
> 2026-10-23)**: los §9–§9.10 de este plan fueron **reescritos contra la
> enmienda 2** y **REAPROBADOS por la usuaria el 2026-10-23** («Apruebo»),
> con la fase 2 **dividida en 2A (T21–T25) y 2B (T26–T27)** («Divide la
> fase», 2026-10-23); la 2B queda pendiente del cierre de la 2A. T16–T20
> ya ejecutadas y commiteadas (hasta `223a43c`) contra el texto anterior de la
> spec; la corrección de alineación (registro transaccional y reproceso) es
> trabajo nuevo de esta fase (T21+). Baseline: `main` **204 PASS / 0 FAIL**;
> en la rama, tras T18–T20: **210 PASS / 0 FAIL**. El contenido de HU-010
> (§0–§8, D1–D16, TC-010-001..018) queda **íntegro y cerrado**.

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 010: que, cuando una cita cambie a
estado **Cancelada** y el cambio quede confirmado, el sistema envíe al paciente
una **notificación de cancelación** (RF-1) que **indique claramente** que la cita
fue cancelada (RF-2), **por los canales que correspondan** — hoy el correo
electrónico; WhatsApp queda pendiente de Spec 009 (RF-3) — y **sin duplicar** la
misma notificación sin causa válida (RF-4), con protección de datos personales,
trazabilidad del cambio y de las notificaciones y claridad del mensaje (RNF).

**Decisiones de alcance acordadas con la usuaria (2026-10-13)**:

- **Q1 — Trigger (servicio mínimo sin UI)**: la Spec 010 presupone un cambio de
  estado a «Cancelada» que hoy no existe (solo `confirmed`, sin endpoint ni
  servicio). Esta HU añade `cancel_appointment()` en la capa de servicio con
  transición `confirmed → cancelled`; **sin endpoint ni interfaz** (la UI de
  cancelación sería otra HU/spec). La demo invoca el servicio directamente.
- **Q2 — Canales**: un **único evento de correo** vía el webhook n8n ya
  operativo (mismo mecanismo que HU-008); el canal WhatsApp queda **pendiente de
  la Spec 009** (RF-3 «cuando corresponda» = cuando el canal esté implementado y
  configurado). No se crea evento de WhatsApp en esta HU.
- **Q3 — Contenido del aviso**: los literales se **proponen en §2.2** para su
  aprobación; después se fijan en la enmienda de la spec 010 y en el espejo
  `tests/expected_content.py`.
- **Q4 — Horario cancelado**: **se libera** para que otro paciente pueda
  reservarlo. Exige excluir `cancelled` de la disponibilidad y migrar el
  `UNIQUE (service, date, time)` a un **índice único parcial** (§2.1).

**Base existente (HU-001/002/003/016/004/005/006/007/008/015 aceptadas)**:

- `create_booking()` con doble comprobación + `UNIQUE (service, date, time)`
  (HU-004/006) y disparo best-effort de los eventos `appointment.confirmed`
  (HU-007) y `appointment.confirmation_email` (HU-008).
- HU-007/008 completas: `automation_events` con `UNIQUE(event_id)`,
  `insert_event`/`mark_sent`/`mark_skipped`/`mark_failed`,
  `automation_service._post_webhook()` (stdlib, timeout 3 s, auth header
  opcional), config `AUTOMATION_WEBHOOK_URL`/`AUTOMATION_TIMEOUT_SECONDS`/
  `AUTOMATION_WEBHOOK_AUTH_HEADER`.
- `email_service.send_confirmation()` con el patrón de composición
  (subject/text/html), dedup por `event_id` determinista y aislamiento total.
- Disponibilidad: `get_hours_with_status()`/`get_available_days()` sobre
  `list_booked_times*` (HU-005) + `GET /citas/horarios` y
  `GET /citas/disponibilidad`.
- **Baseline: `python -m pytest -q` → 187 PASS / 0 FAIL** (verificado en
  `main`, 2026-10-13; verificar al crear la rama).

Esta HU **no reescribe lo que funciona**: reserva, disponibilidad (salvo la
exclusión de `cancelled`), doble reserva, los eventos de HU-007/008 y el
contrato PRG `POST /citas → 303 → /citas/confirmada/<id>` quedan intactos
(RF-3, regresión). **Sin variables de entorno nuevas y sin dependencias nuevas**
(constitución #1).

**Fuera de alcance** (spec 010 + D15): endpoint o interfaz de cancelación;
WhatsApp (Spec 009, con sus propias dudas de proveedor/plantilla); reprogramación
automática; gestión de campañas; definición de políticas de cancelación;
tabla de auditoría de cambios de estado; panel de administración de envíos;
reintentos automáticos; cambios visibles en el sitio (sin capturas 1280/375).

**Interpretación fijada (pendiente de enmienda, D16)**:

- «el cambio sea confirmado» = el `UPDATE confirmed → cancelled` se **confirma
  en persistencia** (commit) antes de notificar.
- «cuando corresponda» = canal implementado y configurado (correo sí; WhatsApp,
  cuando exista la Spec 009).
- Quién cancela: operación interna del consultorio (el psicólogo/administrador
  invoca `cancel_appointment()`); sin autorización/roles porque no hay UI.

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Cita cambia a Cancelada y el cambio confirmado → notificación de cancelación | §3 `cancel_appointment()` (UPDATE condicional → `send_cancellation()`); §5 D1/D6/D7; §6 TC-010-001/003/009 |
| RF-2 | La notificación indica claramente que la cita fue cancelada | §2.2 literales «Cita cancelada»/«Cancelada» + espejo; §3 `build_cancellation_message()`; §5 D3; §6 TC-010-002/013 |
| RF-3 | Cuando corresponda, por correo electrónico y WhatsApp | §2.3 correo por webhook (`sent`/`skipped`); WhatsApp **pendiente Spec 009** (Q2); §2.4 config reutilizada; §5 D2/D8; §6 TC-010-001/003/016 |
| RF-4 | C ya notificada → sin duplicar sin causa válida | §2.1 `UPDATE … AND status='confirmed'` + `event_id` determinista con `UNIQUE(event_id)`; §3 dedup; §5 D6; §6 TC-010-006 |
| RNF-1 | Protección de datos personales | §2.2 payload con `to`+`patient_name` (excepción documentada en la enmienda), sin documento/teléfono; §5 D9; §6 TC-010-002/010 |
| RNF-2 | Trazabilidad del cambio y de las notificaciones | §2.1 `appointments.status='cancelled'` + `automation_events` con `appointment_id`; §5 D5/D6; §6 TC-010-001/014 |
| RNF-3 | Claridad del mensaje (sin ambigüedad) | §2.2 asunto/cuerpo con «Cancelada» y fecha legible; §5 D3; §6 TC-010-002/013 |
| CL-1 | Cita ya cancelada | §3 guardas: sin cambio y sin notificación; §6 TC-010-006 |
| CL-2 | Fallo de uno de los canales | §3 mapeo Timeout/URLError/no-2xx → `failed`, cancelación intacta; §5 D7/D10; §6 TC-010-004/005/009 |
| CL-3 | Datos de contacto incompletos | §3 chequeo defensivo → `failed`, sin POST; §6 TC-010-007/008 |
| CL-4 | Cancelación repetida | §2.1 transición atómica + `UNIQUE(event_id)`; §3 dedup; §5 D6; §6 TC-010-006 |
| Liberación del horario (enmienda Q4) | El horario de una cita cancelada vuelve a estar disponible | §2.1 disponibilidad excluye `cancelled` + índice único parcial y migración; §5 D4/D5; §6 TC-010-011/012/015/017 |
| Re-reserva del slot cancelado (enmienda Q4) | `POST /citas` sobre un horario cancelado → alta válida | §2.1 índice parcial; §3 `create_booking()` intacto; §5 D4; §6 TC-010-013/016 |
| Finalización | Tests en verde + demo manual de cancelación con notificación por los canales disponibles | §6 pirámide y evidencia + §8 secuencia |

> Nota: las filas «enmienda» (liberación y re-reserva) son consecuencia de la
> decisión Q4 de la usuaria y deben quedar fijadas en la **enmienda de la spec
> 010** (D16) antes de implementar (AGENTS.md: datos/índices → spec + plan).

---

## 1. Estructura de módulos

`[RF-1..RF-4][CL-1..CL-4][RNF-1..RNF-3]` — Constitución #3: la lógica vive en
`services/`, el acceso a datos en `persistence/` y la presentación no se toca;
sin dependencias nuevas (constitución #1: solo stdlib ya usada por HU-007/008).
**Sin cambios en `config.py`, en `web/` ni en plantillas/CSS/JS** (sin UI, D15).
Solo se muestran los **cambios sobre lo existente**:

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   ├── appointment_content.py   # + STATUS_CANCELLED="cancelled",
│   │   │                        #   STATUS_CANCELLED_LABEL="Cancelada",
│   │   │                        #   MSG_APPOINTMENT_NOT_FOUND          [RF-1]
│   │   └── email_content.py         # + literales de cancelación:
│   │                            #   asunto, cabecera, pie, HTML y
│   │                            #   motivos (§2.2)                     [RF-2][RNF-3]
│   ├── services/
│   │   ├── appointment_service.py   # + cancel_appointment() (transición
│   │   │                        #   confirmed→cancelled + notificación
│   │   │                        #   best-effort)                       [RF-1][RF-3][RF-4]
│   │   ├── email_service.py         # + EVENT_TYPE_CANCELLATION,
│   │   │                        #   build_cancellation_message(),
│   │   │                        #   build_cancellation_event(),
│   │   │                        #   send_cancellation() (nunca propaga)
│   │   │                        #   [RF-1][RF-2][RF-3][RF-4][CL-1..CL-4]
│   │   └── automation_service.py    # SIN CAMBIOS; _post_webhook reutilizado
│   │                            #   por referencia de módulo (D14)     [RF-1]
│   └── persistence/
│       ├── database.py              # SCHEMA: appointments SIN UNIQUE inline
│       │                        #   + migración idempotente con respaldo
│       │                        #   + índice único parcial (§2.1)
│       │                        #   [RF-1][RF-4][RNF-2]
│       └── appointments_repository.py  # + update_appointment_status()
│                                   #   (UPDATE condicional); is_slot_taken/
│                                   #   list_booked_times* excluyen
│                                   #   status='cancelled'              [RF-1][RF-4]
├── consultorio/web/                 # SIN CAMBIOS (sin endpoint de cancelación)
└── tests/
    ├── expected_content.py          # + espejo de los literales de §2.2   [RF-2]
    ├── test_cancellation_service.py # unit + integración (nuevo)
    │                              #   [RF-1..RF-4][CL-1..CL-4][RNF]
    └── test_hu_010.py               # migración, disponibilidad, HTTP,
                                   #   regresión (nuevo)                 [todos]
```

**Sin cambios**: esquema de `automation_events`, repositorios de eventos,
`availability.js`, plantillas, CSS, `base.html` (sin UI: no hay copy visible en
el sitio → sin capturas 1280/375).

Responsabilidades (solo módulos tocados):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/appointment_content.py` | Constantes: estado `cancelled`, etiqueta «Cancelada», mensaje de cita no encontrada | Contener lógica o acceder a la BD |
| `content/email_content.py` | Literales contractuales del aviso de cancelación (asunto, cabecera, pie, HTML, motivos) | Contener lógica o acceder a la BD |
| `services/appointment_service.py` | `cancel_appointment()`: transición atómica + invocar `send_cancellation()` | Crear endpoints; notificar sin que el cambio esté confirmado; reintentar |
| `services/email_service.py` | Componer el aviso, construir el evento, registrarlo y hacer el POST best-effort; traducir fallos a `failed`; **nunca propagar** | Cambiar el estado de la cita; contener credenciales; gestionar HTTP de la app |
| `persistence/appointments_repository.py` | `update_appointment_status()` (UPDATE condicional); excluir `cancelled` en la disponibilidad | Reglas de notificación ni llamadas HTTP |
| `persistence/database.py` | DDL nuevo (índice parcial) + migración idempotente con respaldo | Destruir datos; migrar dos veces |
| `web/` | — (sin cambios) | — |

---

## 2. Literales, modelo de datos y configuración

`[RF-1][RF-2][RF-3][RF-4][RNF-1][RNF-2][CL-4]` — Con **cambio de esquema
(§2.1)** respaldado por la enmienda de la spec 010 (D16; AGENTS.md: nada de
índices sin spec y plan), y literales de §2.2 **propuestos para aprobación**
(textos contractuales una vez fijados en la enmienda).

### 2.1 Modelo de datos — transición de estado e índice único parcial

**2.1.1 Estado de la cita**: `appointments.status` gana el valor **`cancelled`**
(«Cancelada»), junto al `confirmed` vigente (HU-004/enmienda 2026-10-11). El
cambio se hace **en el punto de persistencia** (constitución #5):

```sql
UPDATE appointments SET status = 'cancelled'
 WHERE id = ? AND status = 'confirmed';
```

- `rowcount = 1` → transición confirmada → se notifica (RF-1).
- `rowcount = 0` → la cita no existe o ya estaba cancelada → **sin cambio y sin
  notificación** (CL-1, CL-4).

**2.1.2 Liberación del horario (Q4)**: hoy `UNIQUE (service, date, time)` está
declarado **inline en la tabla** (`database.py` SCHEMA) y bloquearía re-reservar
un horario cancelado; además `is_slot_taken()`/`list_booked_times*()` cuentan
cualquier fila sin mirar el estado. Cambios:

- Disponibilidad: `AND status <> 'cancelled'` en `is_slot_taken`,
  `list_booked_times` y `list_booked_times_by_date` → el hueco cancelado vuelve
  a aparecer libre en `GET /citas/horarios` y `GET /citas/disponibilidad`.
- Unicidad: **migración** a índice único parcial (SQLite no permite eliminar un
  `UNIQUE` inline con `ALTER TABLE`; hace falta reconstruir la tabla):

```sql
CREATE TABLE appointments_new ( …mismas columnas…, SIN UNIQUE inline );
INSERT INTO appointments_new SELECT … FROM appointments;
DROP TABLE appointments;
ALTER TABLE appointments_new RENAME TO appointments;
CREATE UNIQUE INDEX IF NOT EXISTS ux_appointments_slot_open
    ON appointments(service, date, time) WHERE status <> 'cancelled';
```

- **Estrategia de respaldo/auditoría** (AGENTS.md): antes del `DROP`, copia del
  fichero de BD a `data/consultorio.db.bak-<timestamp>`; la migración corre en
  una transacción y se **aborta con error** si existieran duplicados entre citas
  **no canceladas** (sin pérdida silenciosa de datos). Idempotente: si el índice
  parcial ya existe, no hace nada (BDs creadas con el SCHEMA nuevo, como las
  temporales de test, no migran).
- `CREATE TABLE IF NOT EXISTS` del SCHEMA nuevo se mantiene para BDs frescas;
  la migración se ejecuta en `init_db()` después del `executescript`.
- Protección de doble reserva intacta (HU-006): el `INSERT` sigue chocando en el
  índice parcial para slots no cancelados → `sqlite3.IntegrityError` →
  `SLOT_TAKEN`; `create_booking()` **no cambia**.

**2.1.3 Trazabilidad (RNF-2)**: sin tabla de auditoría nueva (fuera de alcance);
el cambio queda en `appointments.status` y la notificación en `automation_events`
con `appointment_id` + `event_id` determinista + `created_at`/`sent_at`.

**2.1.4 Evento de la notificación** (reutiliza `automation_events`, sin
migración):

- `event_id` **determinista**
  `appointment.cancellation_email:{appointment.id}:v1` → el reproceso choca en el
  INSERT y se descarta **antes** de cualquier POST (RF-4, CL-4).
- `event_type = "appointment.cancellation_email"`, `event_version = 1`;
  `appointment_id` documenta el vínculo (RNF-2).
- Estados `pending` → `sent` | `skipped` | `failed` + `detail` en español
  (constitución #6). Coexiste con `appointment.confirmed` y
  `appointment.confirmation_email`: son tipos distintos con `event_id`s distintos.

### 2.2 Literales y plantilla (`content/email_content.py`)

> **Propuestos en este plan (Q3)** — contractuales tras la enmienda de la spec
> 010 (AGENTS.md «Textos contractuales»); espejo en `tests/expected_content.py`.
> Se reutilizan las etiquetas, el saludo, el remitente, la paleta y las fechas
> legibles ya aceptados en HU-008 (`EMAIL_LABEL_*`, `EMAIL_GREETING_TEMPLATE`,
> `EMAIL_SENDER_NAME`, `WEEKDAYS_ES`/`MONTHS_ES`, `EMAIL_HTML_TEMPLATE`).

```python
# Asunto y cabecera
CANCELLATION_EMAIL_SUBJECT_TEMPLATE: str = (
    "Cita cancelada — {service_name} · {date_label} · {time}"
)
CANCELLATION_EMAIL_BODY_HEADER: str = (
    "Tu cita ha sido cancelada. Estos son los datos de la cita cancelada:"
)

# Pie (diferente al de confirmación: invita a reagendar)
CANCELLATION_EMAIL_FOOTER: str = (
    "Si deseas agendar una nueva cita, puedes hacerlo desde la página "
    "del consultorio o contactándote con nosotros."
)

# Estado (reutiliza appointment_content)
STATUS_CANCELLED: str = "cancelled"
STATUS_CANCELLED_LABEL: str = "Cancelada"

# Motivos nuevos (español)
DETAIL_CANCELLATION_NOT_CONFIGURED: str = "Envío de correo no configurado."
# Reutilizados de email_content (mismo canal, copy ya aceptado):
# DETAIL_INVALID_RECIPIENT, MSG_APPOINTMENT_INCOMPLETE, DETAIL_TIMEOUT,
# DETAIL_UNAVAILABLE, DETAIL_UNEXPECTED, DETAIL_INVALID_RESPONSE_TEMPLATE
```

- **Texto plano**: remitente → saludo → `CANCELLATION_EMAIL_BODY_HEADER` →
  `Servicio: …` / `Fecha: …` (legible en español) / `Hora: …` /
  **`Estado: Cancelada`** / `Referencia de la cita: #id` →
  `CANCELLATION_EMAIL_FOOTER`.
- **HTML**: reutiliza `EMAIL_HTML_TEMPLATE` (misma estructura, misma paleta de
  6 hex inline, sin `<img>`/CSS externo/remoto) con los mismos placeholders; el
  copy de cabecera/pie y el estado «Cancelada» son los de arriba → **una sola
  plantilla parametrizada**, sin duplicar HTML (RNF-3).
- **Claridad (RF-2, RNF-3)**: asunto y cabecera contienen literalmente
  «Cita cancelada»/«cancelada» y el estado mostrado es «Cancelada»: sin
  ambigüedad posible con la confirmación (cuyo asunto empieza por
  «Confirmación de tu cita»).

### 2.3 Estados e incidencias (RF-1, RF-3, CL-2)

| Situación | `status` | `detail` (español) | RF/CL |
|---|---|---|---|
| Evento registrado, a punto de enviarse | `pending` | `NULL` | RF-1 |
| HTTP 2xx del webhook | `sent` | `NULL` + `sent_at` | RF-1 |
| Webhook no configurado (URL vacía) | `skipped` | `Envío de correo no configurado.` | RF-1, RF-3 |
| Cita con datos incompletos | `failed` | `Datos de la cita incompletos.` | CL-3 |
| Email ausente/inválido (defensivo) | `failed` | `Dirección de correo del paciente ausente o no válida.` | CL-3 |
| Timeout | `failed` | `Tiempo de espera agotado (timeout).` | CL-2 |
| `URLError` / conexión rechazada | `failed` | `Servicio de automatización no disponible.` | CL-2 |
| Respuesta no-2xx | `failed` | `Respuesta no válida del servicio (HTTP {code}).` | CL-2 |
| Otra excepción | `failed` | `Error inesperado durante la automatización.` | CL-2 |

Ningún `failed` **revierte la cancelación** (RF-1, D7): la cancelación ya está
commitada; la notificación es best-effort. Sin reintento automático: la
re-ejecución la decide el administrador y el `UNIQUE(event_id)` impide el
duplicado (RF-4).

### 2.4 Configuración (RF-3) — **sin variables nuevas**

| Variable (env, heredada de HU-007) | Uso en HU-010 |
|---|---|
| `AUTOMATION_WEBHOOK_URL` | Mismo webhook n8n (Q2); **vacía = evento `skipped`** «Envío de correo no configurado.»; el sistema opera igual |
| `AUTOMATION_TIMEOUT_SECONDS` | Mismo timeout del POST (3.0 s por defecto) |
| `AUTOMATION_WEBHOOK_AUTH_HEADER` | Misma cabecera opcional; el token es secreto de entorno, nunca en repo/docs/tests |

`cancel_appointment()` recibe url/timeout/auth como parámetros (mismo patrón DI
que `create_booking()`); la capa web no cambia porque no hay endpoint (D15).

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-4][CL-1..CL-4][RNF-1..RNF-3]`

```text
# --- persistence/appointments_repository.py ---------------------------
FUNCTION update_appointment_status(appointment_id, new_status, db) -> Appointment | None:
    TRY:
        cursor = UPDATE appointments SET status = ?
                 WHERE id = ? AND status = 'confirmed'       # transición atómica
        IF cursor.rowcount == 0: RETURN None                 # [RF-4][CL-1][CL-4]
        RETURN get_appointment_by_id(appointment_id, db)     # cita ya 'cancelled'
    # sqlite3.IntegrityError/OperationalError propagan (fallo real de la BD)

FUNCTION is_slot_taken(service, date, time, db) -> bool:
    SELECT 1 … WHERE service=? AND date=? AND time=? AND status <> 'cancelled'
                                                          # [Q4 liberación]
FUNCTION list_booked_times(service, date, db) / list_booked_times_by_date(…):
    … AND status <> 'cancelled'                             # [Q4]

# --- persistence/database.py ------------------------------------------
FUNCTION init_db(database_path):
    … mkdir + executescript(SCHEMA nuevo, sin UNIQUE inline) …
    _migrate_appointment_uniqueness(connection)             # [Q4][RNF-2]

FUNCTION _migrate_appointment_uniqueness(connection):
    IF EXISTS index ux_appointments_slot_open: RETURN       # idempotente
    IF table SQL has inline UNIQUE:                          # BD vieja
        backup = copy data/consultorio.db → .bak-<timestamp>   # respaldo
        IF EXISTS duplicados entre status <> 'cancelled': RAISE (aborta)
        BEGIN TRAN: CREATE appointments_new (sin UNIQUE) → COPY →
                    DROP old → RENAME → CREATE UNIQUE INDEX …
                    WHERE status <> 'cancelled'             # [RF-1][RF-4]
        COMMIT
    ELSE: CREATE UNIQUE INDEX IF NOT EXISTS …               # caso raro

# --- services/email_service.py ----------------------------------------
CANCELLATION_EVENT_TYPE: str = "appointment.cancellation_email"   # [RF-4]
CANCELLATION_EVENT_VERSION: int = 1

FUNCTION build_cancellation_message(appointment) -> dict[str, str]:
    service_name = SERVICES_CATALOG[appointment.service]["name"]
    date_label = format_spanish_date(appointment.date)      # reutilizado
    subject = CANCELLATION_EMAIL_SUBJECT_TEMPLATE.format(…)  # «Cita cancelada —»
    text = remitente + saludo + CANCELLATION_EMAIL_BODY_HEADER +
           Servicio/Fecha/Hora + "Estado: Cancelada" +       # [RF-2][RNF-3]
           "Referencia de la cita: #id" + CANCELLATION_EMAIL_FOOTER
    html = EMAIL_HTML_TEMPLATE.format(…, status=STATUS_CANCELLED_LABEL, …)
    RETURN {"subject": subject, "text": text, "html": html}

FUNCTION build_cancellation_event(appointment) -> dict:       # allowlist
    RETURN {                                               [RF-2][RF-4][RNF-1]
        "event_id": f"{CANCELLATION_EVENT_TYPE}:{appointment.id}:v1",
        "event_type": CANCELLATION_EVENT_TYPE, "event_version": 1,
        "occurred_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "recipient": {"to": appointment.email,
                      "patient_name": appointment.patient_name},
        "message": build_cancellation_message(appointment),
        "appointment": {"id": …, "service": …, "date": …, "time": …,
                        "status": appointment.status}}       # 'cancelled'

FUNCTION send_cancellation(appointment, db, url, timeout, auth_header="") -> None:
    # MISMO patrón que send_confirmation (HU-008); nunca propaga
    TRY:
        IF appointment MISSING campos: insert_event + mark_failed(
            MSG_APPOINTMENT_INCOMPLETE); RETURN             [CL-3]
        IF appointment.email EMPTY O inválida: insert_event + mark_failed(
            DETAIL_INVALID_RECIPIENT); RETURN               [CL-3]
        event = build_cancellation_event(appointment)
        IF NOT events_repository.insert_event(              # UNIQUE(event_id)
                event_id, CANCELLATION_EVENT_TYPE, 1, appointment.id, db):
            RETURN                                          # ya notificada [RF-4]
        IF NOT url: mark_skipped(event_id,
            DETAIL_CANCELLATION_NOT_CONFIGURED, db); RETURN [RF-1][RF-3]
        TRY: status_code = automation_service._post_webhook(    # referencia de
                url, event, timeout, auth_header)               # módulo [D14]
        CATCH TimeoutError:  mark_failed(…, DETAIL_TIMEOUT); RETURN      [CL-2]
        CATCH urllib.error.URLError: mark_failed(…, DETAIL_UNAVAILABLE); [CL-2]
        CATCH Exception: mark_failed(…, DETAIL_UNEXPECTED); RETURN
        IF 200 <= status_code < 300: mark_sent(event_id, db)  [RF-1]
        ELSE: mark_failed(…, DETAIL_INVALID_RESPONSE…)         [CL-2]
    CATCH Exception:
        RETURN   # jamás revierte la cancelación             [RF-1][CL-2]

# --- services/appointment_service.py ----------------------------------
APPOINTMENT_NOT_FOUND: str = "appointment_not_found"
ALREADY_CANCELLED: str = "already_cancelled"

FUNCTION cancel_appointment(appointment_id, database_path, url="", timeout=3.0,
                            auth_header="") -> Appointment | str:
    appointment = repository.get_appointment_by_id(appointment_id, database_path)
    IF appointment IS None: RETURN APPOINTMENT_NOT_FOUND      [CL-1]
    updated = repository.update_appointment_status(
        appointment_id, STATUS_CANCELLED, database_path)      # commit [RF-1]
    IF updated IS None:
        RETURN ALREADY_CANCELLED   # ya cancelada: SIN notificación [RF-4][CL-1]
    email_service.send_cancellation(                          # best-effort
        updated, database_path, url, timeout, auth_header)    # [RF-1][RF-3]
    RETURN updated

# create_booking() y web/: SIN CAMBIOS (firma e HTTP intactos)     [RF-3]
```

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor (BD existente) | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `python -m pytest -q` | Suite completa (187 previos + 17 nuevos = 204) | `204 passed` | `0` / `1` |
| `python -m pytest tests/test_hu_010.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-3]` — **sin endpoints nuevos**

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `POST` | `/citas` (válido y libre) | sin cambios; ahora también acepta un horario previamente **cancelado** (1 fila nueva) | **303** → **200** |
| `GET` | `/citas/horarios?service=&date=` | tras cancelar, la hora de la cita cancelada aparece `available` | **200** |
| `GET` | `/citas/disponibilidad?service=&month=` | tras cancelar, el día vuelve a aparecer con huecos | **200** |
| resto de rutas | sin cambios | como hasta ahora | 200/303/400/404/405 |

No hay ruta de cancelación (D15): el cambio se invoca desde la capa de servicio
(la UI sería otra HU).

**Contrato semántico (lo que verifican los tests):**

```text
[RF-1] cancel_appointment() sobre cita 'confirmed' → status 'cancelled' y,
       con webhook, evento cancellation_email 'sent' + 1 POST   → absent ⇒ FAIL
[RF-2] subject/text/html contienen «Cita cancelada», servicio (nombre),
       fecha legible, hora, «Cancelada» y #id; HTML ⊆ paleta de 6 hex,
       sin recursos remotos; sin documento ni teléfono          → absent ⇒ FAIL
[RF-3] URL vacía → cancelación OK + evento 'skipped' + 0 POST; sin
       variables nuevas; contrato HTTP de /citas intacto        → absent ⇒ FAIL
[RF-4] reproceso (2ª cancelación) → 0 eventos nuevos y 0 POST   → absent ⇒ FAIL
[Q4]  cancelar libera la hora en horarios/disponibilidad y
       POST /citas sobre esa hora → 303 con fila nueva; slot
       confirmado sigue → SLOT_TAKEN                            → absent ⇒ FAIL
[regresión] 187 previos intactos (HU-004/005/006/007/008/…)
                                                        → present ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Trigger = `cancel_appointment()` en capa de servicio, sin endpoint ni UI** (Q1) | La spec 010 exige un cambio de estado para notificar pero no especifica interfaz; alcance mínimo trazable, la UI de cancelación será otra HU/spec | *Endpoint/UI ahora*: alcance nuevo sin spec (autorización, roles, copy). *Solo notificación sin transición*: RF-1 quedaría sin disparador real y la demo sería simulada | RF-1 |
| D2 | **Solo canal de correo vía webhook n8n; WhatsApp pendiente de Spec 009** (Q2) | RF-3 es condicional («cuando corresponda»); el webhook y el patrón de HU-008 ya están operativos y probados en vivo; el proveedor/plantilla de WhatsApp son dudas abiertas de la Spec 009, que aquí no se resuelven | *Emitir ya un evento `cancellation_whatsapp`*: decidiría por la usuaria lo que la Spec 009 aún no define. *Ambos canales completos en esta HU*: absorber la spec 009 sin spec | RF-3 |
| D3 | **Literales contractuales propuestos en §2.2** (asunto «Cita cancelada — …», cabecera, pie de reagendado, «Estado: Cancelada») + espejo (Q3) | Cierra la duda de «contenido exacto» con copy coherente con HU-008 (misma plantilla HTML parametrizada y misma paleta); AGENTS.md «Textos contractuales» | *Copy inventado en el servicio*: rompe spec→test. *Reutilizar el asunto de confirmación*: ambiguo (RF-2) | RF-2, RNF-3 |
| D4 | **El horario cancelado se libera**: disponibilidad excluye `cancelled` + `UNIQUE` migrado a **índice único parcial** `WHERE status <> 'cancelled'` (Q4) | Decisión de la usuaria; una cita cancelada no debe bloquear la agenda; el índice parcial conserva la protección de doble reserva para citas vivas (constitución #5) | *Seguir bloqueando*: slot inútilmente ocupado (descartado por la usuaria). *Parchear solo el SELECT*: el INSERT chocaría igual en el UNIQUE inline → re-reserva imposible | RF-1 (enmienda) |
| D5 | **Migración por reconstrucción de tabla con respaldo previo, transacción y aborto si hay duplicados entre no-canceladas; idempotente** | SQLite no admite `DROP CONSTRAINT` (AGENTS.md: saneamiento con decisión, respaldo y pruebas); el respaldo `.bak-<timestamp>` cubre la auditoría; el guard del índice evita migrar BDs nuevas | *`ALTER TABLE`*: no existe para constraints. *Borrar filas canceladas*: destruye trazabilidad. *Migrar sin respaldo*: sin red de seguridad | RF-4, RNF-2 |
| D6 | **Doble capa de deduplicación**: UPDATE condicional `WHERE status='confirmed'` (transición atómica) + `event_id` determinista `appointment.cancellation_email:{id}:v1` con `UNIQUE(event_id)` | RF-4 «sin causa válida»: la transición garantiza que solo se notifica el primer cambio; el UNIQUE corta reintentos y reprocesos en el punto de persistencia (constitución #5) | *Solo chequeo previo (SELECT)*: carrera entre chequeo y UPDATE. *UUID por emisión*: cada reproceso reenviaría | RF-4, CL-1, CL-4 |
| D7 | **Orden: commit del cambio → notificación best-effort que nunca propaga ni revierte** | RF-1 («el cambio sea confirmado») + lección HU-007/008: un fallo del webhook no puede deshacer la cancelación ni impedirla | *Notificar antes de commitear*: se avisaría de cancelaciones que fallan. *Transacción conjunta*: un fallo de red tumbaría la cancelación | RF-1, RF-3, CL-2 |
| D8 | **Sin variables de entorno nuevas**: reutiliza `AUTOMATION_WEBHOOK_URL`/`_TIMEOUT_SECONDS`/`_WEBHOOK_AUTH_HEADER` | Mismo canal y mismo workflow (Q2); cero config nueva; el sitio opera igual sin webhook (evento `skipped`) | *`CANCELLATION_WEBHOOK_URL`*: duplica config y secretos sin ganancia | RF-1, RF-3 |
| D9 | **Payload con PII mínima: `recipient.to` + `patient_name`**; sin `document_type`/`document_number`/`phone`; auth header heredado | El aviso no puede llegar sin destinatario ni saludo; misma excepción ya documentada en Spec 008; la cancelación no necesita más datos | *Añadir teléfono (futuro WhatsApp)*: pertenece a Spec 009. *Payload sin destinatario*: n8n no podría enviar | RF-2, RNF-1 |
| D10 | **Estados y motivos reutilizados de HU-007/008**; solo `DETAIL_CANCELLATION_NOT_CONFIGURED` es nuevo (mismo texto que el de correo) | Mismo canal y mismo copy ya aceptado; distingue «no configurado» (`skipped`) de un error real | *Copys nuevos paralelos*: duplicidad textual sin necesidad | RF-3, CL-2 |
| D11 | **Sin restricción de fecha para cancelar** (cualquier cita `confirmed`); sin política de anticipación | La spec 010 deja las «políticas de cancelación» fuera de alcance; inventar plazos sería regla sin requisito | *Bloquear cancelaciones pasadas/cercanas*: política nueva sin spec | RF-1 |
| D12 | **Rama `feature/hu-010` desde `main`** (baseline 187) | AGENTS.md: aislamiento de HU por rama; `main` limpia | *Rama desde otra feature*: arrastra pendientes | regresión |
| D13 | **Identificadores en inglés; literales y `detail` en español**; sin copy visible en el sitio | Constitución #6 | *Mensajes en inglés*: rompe la constitución | todos |
| D14 | **Reutilizar `automation_service._post_webhook` por referencia de módulo** (`automation_service._post_webhook(…)`) y `send_confirmation` como patrón espejo | Un solo punto de parcheo en tests (hermeticidad HU-007/008); misma estrategia de demo con receptor local stdlib | *`from … import _post_webhook`*: rompe los parches existentes. *Copia de `_post_webhook`*: duplicación. *Proveedor real en tests*: frágil y con secretos | RF-1, CL-2 |
| D15 | **Sin UI ni cambios en `web/`, plantillas, CSS o JS**; demo invocando `cancel_appointment()` desde un script/REPL | Alcance mínimo de Q1; sin copy visible → sin capturas 1280/375 (como HU-007/008) | *Botón de cancelación en `/citas/confirmada`*: alcance sin spec | RF-1, RNF-3 |
| D16 | **Enmienda de la spec 010 previa y bloqueante** (cierra Q1–Q4: trigger, canales «cuando corresponda», contenido literal, liberación de horario + migración) | AGENTS.md: si el cambio afecta datos/API/UX/tests, actualizar primero la spec y el `plan.md`; no se implementa sobre dudas abiertas | *Implementar y luego enmendar*: la spec dejaría de ser la fuente de verdad | todos |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` · `python -m pytest tests/test_hu_010.py -v`.
Fixtures de `conftest.py` sin cambios (BD temporal por fixture; el `init_db()` de
la fixture crea ya la tabla nueva con índice parcial, sin migración). Punto de
parcheo único: `automation_service._post_webhook` (D14). Sin red real, sin
`sleep`, fechas relativas.

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-010-001 | `test_cancellation_service.py` | `cancel_appointment()` con webhook y `_post_webhook` parcheado (200) → cita `cancelled` + evento `appointment.cancellation_email` `sent` con `sent_at` + **1 POST** con `recipient.to`/`patient_name`, `message` completo y `appointment.status='cancelled'` | RF-1, RF-3, RNF-2 |
| TC-010-002 | `test_cancellation_service.py` | `build_cancellation_message()` → asunto «Cita cancelada — …», texto con servicio (nombre visible), fecha legible en español, hora, **«Cancelada»** y `#{id}`; HTML solo con los **6 hex** de la paleta, sin `<img>`/CSS externo/remoto; sin documento ni teléfono | RF-2, RNF-1, RNF-3 |
| TC-010-003 | `test_cancellation_service.py` | **No configurado:** sin URL → cita `cancelled` + evento `skipped` («Envío de correo no configurado.») + **0 POST** | RF-1, RF-3 |
| TC-010-004 | `test_cancellation_service.py` | **CL-2:** `URLError` → evento `failed` «Servicio de automatización no disponible.», **0 excepción** y la cita sigue `cancelled` | RF-1, CL-2 |
| TC-010-005 | `test_cancellation_service.py` | **CL-2:** `TimeoutError` → evento `failed` «Tiempo de espera agotado (timeout).» y la cita sigue `cancelled` | CL-2 |
| TC-010-006 | `test_cancellation_service.py` | **CL-1/CL-4/RF-4:** segunda llamada sobre la misma cita → `ALREADY_CANCELLED`, **1 evento** total (UNIQUE) y **1 POST** acumulado | RF-4, CL-1, CL-4 |
| TC-010-007 | `test_cancellation_service.py` | **CL-3:** `appointment.email` vacía o sin `@` (defensivo) → cita `cancelled` + **0 POST** + evento `failed` «Dirección de correo del paciente ausente o no válida.» | CL-3, RF-1 |
| TC-010-008 | `test_cancellation_service.py` | **CL-3:** `Appointment` con campos vacíos → **0 POST** + evento `failed` «Datos de la cita incompletos.» | CL-3 |
| TC-010-009 | `test_cancellation_service.py` | **Aislamiento:** repositorio de eventos parcheado con `RuntimeError` → `cancel_appointment()` **devuelve la `Appointment` `cancelled`** (el cambio no se revierte) | RF-1, CL-2 |
| TC-010-010 | `test_cancellation_service.py` | **Allowlist + RNF-1:** `event_id` determinista `appointment.cancellation_email:{id}:v1`, `event_version=1`; con `recipient`/`message`; **sin** `document_type`/`document_number`/`phone` (raíz y `appointment`) | RF-4, RNF-1 |
| TC-010-011 | `test_cancellation_service.py` | **Q4 liberación:** cancelar → `is_slot_taken()` = `False` y `get_hours_with_status()` marca la hora **libre** de nuevo | enmienda Q4 |
| TC-010-012 | `test_cancellation_service.py` | **Q4 regresión HU-006:** slot `confirmed` → `create_booking()` devuelve `SLOT_TAKEN` (índice parcial intacto, 0 filas nuevas) | RF-4, regresión |
| TC-010-013 | `test_hu_010.py` | **Q4 re-reserva:** tras cancelar, `create_booking()` con el mismo `service+date+time` devuelve **`Appointment`** (no `SLOT_TAKEN`) con 1 fila nueva; la cita cancelada permanece en la BD | enmienda Q4, RF-1 |
| TC-010-014 | `test_hu_010.py` | **Esquema/migración:** en una BD creada con el SCHEMA **antiguo** (UNIQUE inline, insertada a mano), `init_db()` migra → existe `ux_appointments_slot_open` **parcial**, los datos se conservan, **backup creado** y segunda ejecución = **sin cambios** (idempotente); con duplicados entre no-canceladas → aborta | RNF-2, RF-4 |
| TC-010-015 | `test_hu_010.py` | **HTTP:** crear cita → cancelar → `GET /citas/horarios` devuelve esa hora `available` y `GET /citas/disponibilidad` reabre el día (200); `POST /citas` sobre esa hora → **303** + fila nueva | enmienda Q4, RF-3 |
| TC-010-016 | `test_hu_010.py` | **Espejo + config:** `expected_content` == módulos de contenido (asunto, cabecera, pie, motivos, `STATUS_CANCELLED`/`_LABEL`); **sin** variables de entorno nuevas (`AUTOMATION_*` intactas) | RF-2, RF-3 |
| TC-010-017 | `test_hu_010.py` | **Regresión funcional HU-004/005/006/007/008/015/016/contraste:** reserva, disponibilidad, doble reserva, eventos `confirmed` y `confirmation_email` idénticos a su contrato; constitución #1 (sin imports de terceros en los módulos tocados) | RF-3, regresión |
| TC-010-018 | `test_hu_010.py` | **Regresión total:** `python -m pytest -q` → **0 FAIL** con los **187 previos** intactos | todos, finalización |

> **Nota de recuento**: TC-010-018 es la corrida de la suite; las funciones
> nuevas son **17** → total esperado **204** (187 + 17). **0 FAIL con los 187
> previos intactos** es la condición real de cierre.

### 6.2 Pirámide

1. **Unitarias** — `build_cancellation_message()`/`build_cancellation_event()`
   (asunto, partes, paleta, sin remotos, sin PII extra) y
   `update_appointment_status()` (transición condicional) sin Flask.
   `[RF-1][RF-2][RF-4][RNF-1][RNF-3]`
2. **Integración de servicio** — `cancel_appointment()` con `_post_webhook`
   parcheado: 2xx→`sent`, sin URL→`skipped`, `URLError`/`TimeoutError`/no-2xx→
   `failed`, reproceso→0 POST, aislamiento, liberación y re-reserva del slot.
   `[RF-1][RF-3][RF-4][CL-1..CL-4][Q4]`
3. **Migración y persistencia** — BD con esquema antiguo → `init_db()` migra con
   respaldo, idempotente, índice parcial presente y unicidad viva intacta.
   `[RF-4][RNF-2][Q4]`
4. **Regresión** — suite completa: 187 previos verdes sin enmiendas.
   `[todos]`
5. **Demo manual** — `python app.py` + **receptor local stdlib efímero** (JSON)
   con `AUTOMATION_WEBHOOK_URL` apuntando a él y llamando a
   `cancel_appointment()` desde un REPL/script: (a) cancelar → cita `cancelled`
   y el receptor captura **1 POST** con subject/text/html de §2.2; (b) evento
   `sent`; (c) **cancelar otra vez** → `already_cancelled` y **0 POST** nuevos;
   (d) **receptor apagado** → cancelación intacta + evento `failed` con motivo;
   (e) tras cancelar → la hora vuelve a estar libre en `/citas/horarios` y se
   puede **re-reservar** por el formulario (303). **Demo live (si la usuaria lo
   indica)**: webhook de n8n de HU-007/008 → correo real recibido. Sin cambios
   visuales → sin capturas 1280/375.
   `[RF-1..RF-4][CL-1..CL-4][Q4]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar (pytest-qa §1.2).
- Pruebas deterministas: `_post_webhook` parcheado, sin red real, sin `sleep`,
  BD temporal, fechas relativas; la migración se prueba con una BD vieja creada
  a mano dentro del test.

```text
HU: HU-010
Caso: TC-010-001
Comando: python -m pytest tests/test_cancellation_service.py -v
Resultado: PASS
Rama: feature/hu-010
Commit: <hash>
Evidencia: payload del evento cancellation_email capturado + dump de automation_events y de appointments.status (demo §6.2)
```

- Informe QA: `docs/evidencias/hu-010/qa-hu-010.md` con PASS/FAIL por TC y
  checkbox de aceptación (skill `pytest-qa`).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Duda implícita: ¿qué dispara el cambio a «Cancelada» si no existe ninguna cancelación en el sistema? | **`cancel_appointment()` en capa de servicio, sin endpoint ni UI** (§3, D1); la UI de cancelación será otra HU/spec. Respondida 2026-10-13. |
| Q2 | Duda de la spec: «siempre ambos canales o según preferencias» / Spec 009 sin implementar | **Solo correo vía webhook n8n (mismo de HU-008); WhatsApp pendiente de Spec 009**; «cuando corresponda» = canal implementado y configurado (§2.3/§2.4, D2). Respondida 2026-10-13. |
| Q3 | Duda de la spec: contenido exacto del aviso | **Literales de §2.2** (asunto «Cita cancelada — …», cabecera, pie de reagendado, «Estado: Cancelada», misma plantilla HTML/paleta de HU-008) + espejo (D3). **Aprobada por la usuaria el 2026-10-13 junto con el plan.** |
| Q4 | Libera o no el horario cancelado (índice `UNIQUE` y disponibilidad) | **Se libera**: disponibilidad excluye `cancelled` + migración a índice único parcial con respaldo (§2.1, D4/D5). Respondida 2026-10-13. |
| Q5 | Rama de trabajo | **`feature/hu-010` desde `main`** (D12), tras aprobar plan y enmienda. |
| Q6 | Relación con Specs 007/008/009 | Reutiliza el webhook, `automation_events`, `_post_webhook` y el patrón de correo de HU-007/008; **no toca** sus specs ni sus eventos. WhatsApp = Spec 009 (fuera de alcance). |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Aprobación de este `plan.md` (alcance, matriz RF, D1–D16, §2.2 literales,
      §2.1 migración) por la usuaria — **aprobado 2026-10-13 («Apruebo»/«Escribe
      task.md»)**.
- [x] **Enmienda de `specs/010_notificar-cancelacion/spec.md`** (D16, petición
      explícita): cerrar las dos dudas `[NECESITA ACLARACIÓN]` con Q2/Q3, fijar
      el trigger `confirmed → cancelled` sin UI (Q1), la liberación del horario
      y su migración (Q4) y el contenido literal del aviso — **cumplida
      2026-10-13** («Contratos fijados (enmienda 2026-10-13)»; suite verificada
      en 187 PASS / 0 FAIL).
- [x] Creación de `feature/hu-010` desde `main` (Q5) y verificación del baseline
      **187 PASS / 0 FAIL** — **cumplida 2026-10-13** (commit `9b6a850`).
- [x] Espejo + `appointment_content`/`email_content` + persistencia (estado,
      índice parcial, migración con respaldo) — **cumplida 2026-10-13** (suite
      187/187; dos aserciones de esquema de HU-004/006 adaptadas al índice
      parcial según la enmienda; los commits por fase quedan en T14).
- [x] Servicio `cancel_appointment()` + `send_cancellation()` con commits por
      fase — **cumplido 2026-10-13** (`d419d1e`).
- [x] Tests §6 en verde: **204 PASS / 0 FAIL** con los 187 previos intactos —
      **cumplido 2026-10-13** (commit `b2b31ee`).
- [x] Demo manual §6.2 (+ live n8n si la usuaria lo indica) + evidencia en
      `docs/evidencias/hu-010/` — **cumplida 2026-10-13** (demo pasos a–e con
      receptor stdlib local; live n8n pendiente si la usuaria lo pide).
- [x] Informe QA `qa-hu-010.md` con PASS/FAIL por TC y checkbox de aceptación
      — **cumplido 2026-10-13** (PASS 18/18; aceptación de la usuaria el
      2026-10-13).
- [x] Commit/Push por fases, `MEMORY.md` y aceptación de la HU — **cumplido
      2026-10-13** (commits `6eac5c6`…`d968ae7`, push sincronizado).
- [x] Servidor de revisión en marcha (AGENTS.md) y URL comunicada — **cumplido
      2026-10-13** (http://127.0.0.1:5000).

---

## 8. Secuencia de implementación

0. **Git**: verificar `main` limpia y baseline **187 PASS**; crear
   **`feature/hu-010` desde `main`** (Q5) — solo tras aprobar este plan.
1. **Spec primero** (bloqueante): enmienda de la spec 010 con Q1–Q4, el contenido
   literal de §2.2 y el contrato de la migración de §2.1 (D16).
2. **Plan**: este `plan.md` (aprobado por la usuaria, incl. literales Q3).
3. **Espejo**: `tests/expected_content.py` con los literales de §2.2.
4. **Contenido**: `appointment_content` (+`STATUS_CANCELLED`/`_LABEL`) y
   `email_content` (+literales y motivos de cancelación).
5. **Persistencia**: SCHEMA nuevo + `init_db()` con migración y respaldo +
   `update_appointment_status()` + disponibilidad sin `cancelled` →
   `test_hu_010.py` (TC-010-014) y TC-010-011/012.
6. **Servicio**: `email_service.send_cancellation()` (§3) →
   `test_cancellation_service.py` (TC-010-001…010).
7. **Disparo**: `appointment_service.cancel_appointment()` (firma con config
   inyectada; sin cambios en `create_booking()` ni en `web/`).
8. **Tests de HU**: `test_hu_010.py` (TC-010-013/015/016/017).
9. **Suite completa**: → **204 PASS / 0 FAIL** con los 187 previos intactos
   (TC-010-018).
10. **Evidencia**: demo §6.2 (receptor local: enviado, reproceso, fallo,
    liberación y re-reserva; + live n8n opcional) → `docs/evidencias/hu-010/` +
    `qa-hu-010.md`.
11. **Cierre**: commits por fase, push, `MEMORY.md`, aceptación y servidor de
    revisión en marcha (AGENTS.md).

---

## 9. Fase 2 — RF-8..RF-15: evento de negocio `appointment.cancelled` y reproceso (**REESCRITO CONTRA LA ENMIENDA 2 — APROBADO por la usuaria el 2026-10-23**)

> Trazabilidad: **HU-010 (enmienda 2 de la spec, aprobada 2026-10-23) → Spec 010
> RF-8..RF-15 (`specs/010_notificar-cancelacion/spec.md`) → §9 de este plan →
> código → tests TC-010-101..119 → evidencia → commit**
> Estado: la usuaria aprobó la enmienda 2 de la spec el 2026-10-23; **este §9,
> reescrito contra ese texto, fue reaprobado por la usuaria el 2026-10-23**
> («Apruebo»), junto con las tareas T21–T27 y con la **división de la fase en
> 2A (T21–T25) y 2B (T26–T27)** («Divide la fase»). La implementación se
> reanuda por la fase 2A; la 2B queda pendiente del cierre de la 2A.
> T16–T20 ya ejecutadas contra el texto anterior del plan (hasta `223a43c`);
> la corrección de alineación — registro transaccional (F2-D11) y
> `reprocess_automation_event()` (F2-D3 reescrito, F2-D12) — es trabajo nuevo
> de esta fase, sin reabrir T19/T20. **Hasta que se implemente, no afirmar que
> la atomicidad está garantizada por el código**: hoy `update_appointment_status`
> e `insert_event` abren conexiones separadas y el registro del evento es
> post-commit (desalineación aceptada como consecuencia del cambio de diseño,
> corregida en T22).
> Baseline: `main` **204 PASS / 0 FAIL**; rama `feature/hu-010-rf8-10`
> **210 PASS / 0 FAIL** (TC-010-101/102/103/104/108/109 añadidos en T19/T20).

### 9.1 Alcance y fuera de alcance

**Alcance** (RF-8..RF-15 de la spec 010, enmienda 2): que, cuando una
cancelación quede confirmada en persistencia, el sistema **registre y emita el
evento de negocio `appointment.cancelled` (v1)** de forma **independiente del
resultado del envío del correo de cancelación** (RF-8), con un **payload
versionado sin datos personales** conforme al contrato de la spec (RF-9), y
con el siguiente contrato de fiabilidad, según la enmienda 2:

- **Atomicidad (RF-11/RF-12)**: la transición de la cita a `cancelled` y el
  registro del evento en estado `pending` se confirman o se revierten como
  partes de **una única transacción de persistencia sobre la misma conexión**
  SQLite («sin traza local, sin cancelación confirmada»); el registro fallido
  **antes** del commit produce rollback completo (la cita no queda Cancelada,
  sin evento ni notificación derivada). La publicación (POST al webhook) se
  realiza **siempre después del commit**.
- **Fiabilidad de publicación (RF-10)**: un fallo del POST **después** del
  commit deja el evento `failed` con el motivo en español y la cancelación
  intacta; **sin reintentos automáticos**. El reproceso posterior se rige por
  RF-13..RF-15.
- **Reproceso (RF-13/RF-14)**: `reprocess_automation_event()` es una función
  de servicio (sin UI ni endpoint) que, por decisión explícita del
  administrador, reintenta la publicación de un evento `appointment.cancelled`
  en estado `failed`, conservando el mismo `event_id` y la misma fila, y
  trazando el resultado (`sent` | `failed` con detalle | `skipped` si la URL
  está vacía). Sobre `sent`, `skipped` y `pending` es **no-op**: sin POST y
  sin modificar el registro. Cuatro estados fijos, sin estados nuevos.
- **Exclusión de concurrencia (RF-15)**: la admisión del reproceso es una
  transición atómica condicionada al estado actual del evento; si dos
  solicitudes compiten, solo una realiza el intento.

Mismo modelo de fiabilidad que HU-007/008/010: registro en `automation_events`
con `event_id` determinista `appointment.cancelled:{appointment.id}:v1` y
`UNIQUE(event_id)`, un solo POST best-effort al webhook de automatización,
estados `pending → sent | skipped | failed`. **Límite de alcance**: el
reproceso y la atomicidad aplican **solo al evento `appointment.cancelled`**;
`appointment.cancellation_email` conserva su registro post-commit (limitación
conocida, documentada en F2-D11).

**Base existente reutilizada** (HU-007/008/010 aceptadas): tabla
`automation_events` con `UNIQUE(event_id)` y `insert_event`/`mark_sent`/
`mark_skipped`/`mark_failed`; `automation_service._post_webhook()` (stdlib,
timeout y auth header heredados); constantes `DETAIL_*` de
`content/automation_content.py`; `cancel_appointment()` con transición
atómica `confirmed → cancelled`. `build_event()` de `automation_service` ya
produce exactamente la forma de payload que RF-9 exige (mismas claves),
solo que con `EVENT_TYPE = "appointment.confirmed"`.

**Base ejecutada en esta rama (T18–T20, hasta `223a43c`)**: constantes
`CANCELLED_EVENT_TYPE`/`_VERSION`; `_build_automation_event()` +
`build_cancelled_event()` + `on_appointment_cancelled()` (con `insert_event`
y `UNIQUE` dedup **post-commit**); disparo en `cancel_appointment()` antes que
el correo (F2-D1). **Estado de ese código frente a la enmienda 2**:

| Pieza | Cumple la enmienda 2 | Acción |
|---|---|---|
| Constantes, `build_cancelled_event()`, allowlist RF-9 | Sí | Sin cambios |
| Orden de emisión negocio → correo (F2-D1) | Sí (la publicación sigue tras el commit) | Sin cambios |
| Registro del evento `pending` | **No**: es post-commit y en conexión separada (F2-D3 anterior); RF-11/RF-12 exigen la misma transacción que el UPDATE de la cita | **Corrección nueva (T22)**: transacción conjunta |
| Vía de reproceso del `failed` | **No**: no existía; RF-13..RF-15 exigen `reprocess_automation_event()` | **Función nueva (T24)** |
| Afirmar «atomicidad garantizada por el código» | **No verificable hoy** | No se afirma hasta implementar T22 |

**Fuera de alcance** de esta fase:

- `calendar_event_id` y borrado del evento en Google Calendar: **Spec 007,
  fase posterior** (su enmienda 2026-10-23 fija solo el contrato de consumo;
  este plan satisface el contrato de emisión, no la implementación de n8n).
- UI, endpoints o tokens de administración (cancelación de interfaz = Specs
  017/018; `reprocess_automation_event()` es función de servicio invocada
  internamente, como `cancel_appointment()`).
- Reintentos automáticos, colas, workers o cualquier infraestructura nueva;
  el único reproceso posible es el **explícito del administrador** sobre
  eventos `failed` (RF-13).
- Estados nuevos en `automation_events` o marcas de «en curso»; los cuatro
  estados (`pending`, `sent`, `skipped`, `failed`) son fijos (decisión de la
  usuaria). Consecuencia aceptada: un evento `pending` huérfano (proceso
  interrumpido tras el commit y antes del POST) **puede permanecer `pending`
  indefinidamente y, con el mecanismo actual, no habrá vía de recuperación**;
  limitación operativa explícita en la spec y en F2-D11.
- Cambios en `appointment.cancellation_email`, `send_cancellation()` ni en el
  contenido del correo (su registro post-commit queda como limitación
  conocida).
- Dependencias nuevas, variables de entorno nuevas (se reutilizan
  `AUTOMATION_WEBHOOK_URL`/`AUTOMATION_TIMEOUT_SECONDS`/
  `AUTOMATION_WEBHOOK_AUTH_HEADER`) y cambios de esquema (la tabla
  `automation_events` ya existe con su UNIQUE).
- Cambios en `tests/expected_content.py`: **sin cambios** por esta enmienda
  (decisión de la usuaria 2026-10-23; los literales visibles de correo y
  estados no cambian — F2-D13).
- Implementación de la Spec 007 (data table y workflow de n8n) y actualización
  del plan 018 (se anota como pendiente del coordinador, F2-D4).

### 9.2 Matriz de cobertura RF (fase 2, enmienda 2)

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-8 | Cancelación confirmada → se registra y emite `appointment.cancelled` v1, independiente del correo, `event_id` determinista + UNIQUE | §9.3 transacción (registro `pending`) + publicación post-commit en `cancel_appointment()`; §9.6; §9.8.1 TC-010-101/103/104/109; **CA-1, CA-3** |
| RF-9 | Payload con `event_id`, `event_type`, `event_version` (1), `occurred_at`, `appointment{id,service,date,time,status:"cancelled"}`; sin PII ni `recipient`/`message` | §9.4 contrato JSON + `build_cancelled_event()` (allowlist); §9.8.1 TC-010-102/111; **CA-2** |
| RF-10 | Fallo de publicación **tras el commit** → `failed` con motivo en español; sin reintentos automáticos; cancelación intacta; URL vacía → `skipped` | §9.5 estados + «nunca propaga» de la publicación; §9.8.1 TC-010-105/106/107; **CA-4** |
| RF-11 | Transición y registro `pending` en la misma conexión/transacción («sin traza local, sin cancelación confirmada»); publicación tras el commit | §9.3 (función transaccional) + §9.6; §9.8.1 TC-010-101/115; **CA-5** |
| RF-12 | Registro `pending` fallido antes del commit → rollback completo (cita sin Cancelar, sin evento, sin POST) | §9.3 + §9.5 matriz de fallos; §9.8.1 TC-010-110; **CA-5** |
| RF-13 | Reproceso de un `failed`: mismo `event_id`, misma fila, 1 POST, resultado trazado (`sent`/`failed`/`skipped`) | §9.3 `reprocess_automation_event()`; §9.6; §9.8.1 TC-010-113/114/115/118; **CA-6** |
| RF-14 | Reproceso sobre `sent`/`skipped`/`pending` → no-op, sin POST y sin modificar el registro | §9.6 tabla de 4 estados; §9.8.1 TC-010-108 (guarda de transición) + TC-010-116; **CA-7** |
| RF-15 | Reprocesos concurrentes → únicamente uno realiza el intento (transición atómica condicionada al estado) | §9.3 `claim_failed_event()`; §9.7 F2-D12; §9.8.1 TC-010-117; **CA-8** |
| RF-16 | Respuesta HTTP no-2xx → `failed` con el literal vigente; 4xx permanentes (excepto 429) no readmitidos; 429/5xx, timeout, `URLError` y excepción inesperada readmitidos | §9.3 `claim_failed_event()` + helper de clasificación; §9.5 tabla por código; §9.8.1 TC-D010-01..16; **CA-D010-01…14** |
| RNF (spec) | Minimización de datos, trazabilidad, atomicidad de la traza, sin colas | §9.4 allowlist sin PII; `automation_events` con `appointment_id`; F2-D5/D6/D11/D12 |
| CL «Webhook no configurado» | Evento `skipped`; la cancelación no depende de la automatización | §9.5; TC-010-104 y reproceso TC-010-114 (URL vacía) |
| CL «pending huérfano» | Queda `pending`; sin vía de recuperación en esta fase (limitación aceptada) | §9.1 fuera de alcance + F2-D11; sin test de recuperación (explícitamente fuera) |
| Compatibilidad Spec 007 (contrato de consumo) | n8n identifica la cita por `appointment_id` | El payload incluye `appointment.id`; el `event_id` de cancelación no se usa para localizar Calendar (RF-9 de la 007 es responsabilidad de n8n) |

### 9.3 Módulos a tocar (responsabilidades y «NO debe hacer»)

Se cambian **los módulos de código listados** (persistencia incluida por la
enmienda 2) y los tests; sin esquema, sin `config.py`, sin `web/`:

| Módulo | Cambio y responsabilidad | NO debe hacer |
|---|---|---|
| `consultorio/content/automation_content.py` | `CANCELLED_EVENT_TYPE = "appointment.cancelled"`, `CANCELLED_EVENT_VERSION = 1` (ya en la rama, T18). **D-010-01 (T3/T6, DP-01/DP-02)**: `DETAIL_INVALID_RESPONSE_PREFIX`, `DETAIL_PERMANENT_REJECTION_PATTERN` (4xx permanente) y `DETAIL_RETRYABLE_REJECTION_PATTERN` (excepción 429), **derivados** de `DETAIL_INVALID_RESPONSE_TEMPLATE`; el literal vigente no cambia | Contener lógica; duplicar los `DETAIL_*` existentes (se reutilizan); retipar a mano el prefijo o los patrones |
| `consultorio/services/automation_service.py` | **ya en la rama**: `_build_automation_event()`, `build_event()` delega sin cambiar su firma pública, `build_cancelled_event()`. **Nuevo (T22)**: `publish_cancelled_event()` (solo publicación: `skipped`/`failed`/`sent` sobre un registro `pending` ya existente, **nunca propaga**). **Nuevo (T24)**: `reprocess_automation_event()` (RF-13..RF-15: admisión atómica del `failed` → recuperar payload/registro → POST → `mark_*`). **D-010-01 (T3/T4, DP-04/DP-05)**: helper único `_register_publication_failure(event_id, error, database_path)` y captura ordenada `TimeoutError → HTTPError → URLError → Exception` en `publish_cancelled_event()`, `reprocess_automation_event()` y `on_appointment_confirmed()` (`HTTPError` antes de `URLError`: es subclase) | Mezclar composición de mensajes de correo; tocar `_post_webhook`; reintentar automáticamente; crear el registro `pending` fuera de la transacción de la cancelación; duplicar el mapeo excepción → `detail` |
| `consultorio/services/appointment_service.py` | `cancel_appointment()`: usar la **nueva operación transaccional** de persistencia (UPDATE cita + INSERT evento `pending`, misma conexión) y, tras el commit, publicar el negocio (F2-D1) antes que el correo | Cambiar la firma o el contrato de `cancel_appointment()`/`create_booking()`; crear endpoints; revertir la cancelación por fallo de publicación; registrar el evento en conexión separada |
| `consultorio/persistence/appointments_repository.py` | **Nuevo (T22)**: operación transaccional `update_appointment_status_with_pending_event()` (o combinación de menor superficie equivalente en los repositorios) que ejecuta el `UPDATE … AND status='confirmed'` y el `INSERT … status='pending'` del evento en **la misma conexión/transacción**; devuelve la cita actualizada o `None`. `update_appointment_status()` existente **se conserva** (call sites HU-010 cerrados) | Reglas de publicación ni llamadas HTTP; exponer transacciones abiertas al servicio |
| `consultorio/persistence/automation_events_repository.py` | **Nuevo (T24)**: `claim_failed_event(event_id, database_path, permanent_pattern=None, retryable_pattern=None)` — transición atómica de admisión del reproceso. **D-010-01 (T6, DP-02)**: el mismo `UPDATE` añade `AND (detail IS NULL OR detail NOT LIKE <4xx permanente> OR detail LIKE <429>)`; sin `SELECT` previo, `rowcount == 1`, sin columnas, índices ni migraciones; los patrones los pasa el servicio (la política no vive en persistencia). `insert_event`/`mark_*` existentes sin cambios de firma | Abrir la transacción de la cancelación; decidir políticas de reproceso; consultar el `detail` en un `SELECT` previo |
| `consultorio/services/email_service.py` | **D-010-01 (T4, DP-04)**: `send_confirmation()` y `send_cancellation()` aplican la misma captura ordenada (`TimeoutError → HTTPError → URLError → Exception`) y delegan el `detail` en `automation_service._register_publication_failure()`; el registro post-commit y la limitación de F2-D11 se mantienen | Clasificar a mano ni duplicar el mapeo; cambiar el literal; alterar el registro post-commit del correo |
| `consultorio/persistence/database.py` | **SIN CAMBIOS** (sin esquema nuevo: `automation_events` ya existe con su UNIQUE) | — |
| `tests/test_cancellation_service.py` | TC-010-101/102/103/104/108/109 **ya en la rama**; se redefinen/adapta el bloque pendiente 105..117 (§9.8.1). **D-010-01 (T1/T5/T7)**: bloque `TC-D010-01..11/15` con `HTTPError` real (400/422/429/500), patrón derivado del template y no-op por estado/tipo (§9.8.1). Los TC-010-001..018 cerrados **no se modifican** (filtran por `event_id`/`event_type`, precedente D15) | Relajar o eliminar aserciones cerradas |

### 9.4 Contrato del evento (RF-9; idéntico al de la spec)

```json
{
  "event_id": "appointment.cancelled:34:v1",
  "event_type": "appointment.cancelled",
  "event_version": 1,
  "occurred_at": "2026-10-23 12:34:56",
  "appointment": { "id": 34, "service": "individual", "date": "2026-10-15", "time": "10:00", "status": "cancelled" }
}
```

- Campos obligatorios exactos: los cinco de arriba; `appointment` con
  `id`, `service`, `date`, `time` y `status` (`"cancelled"` — garantizado
  porque el payload se construye con la `Appointment` devuelta por la
  transición, cuyo estado ya es `cancelled`).
- **Excluidos**: `patient_name`, `email`, `phone`, `document_type`,
  `document_number` y también `recipient` y `message` (exclusivos del correo
  de cancelación; Spec 007 RF-13 distingue negocio vs. acción técnica).
- `event_id` determinista `appointment.cancelled:{appointment.id}:v1`; un
  cambio de forma del payload elevaría `event_version` (misma regla que la
  Spec 007). Registro en `automation_events` con `appointment_id` para
  trazabilidad; **sin migraciones**.
- Compatibilidad con el contrato de consumo de la Spec 007: n8n localiza la
  fila de creación por **`appointment_id`** (presente en el payload como
  `appointment.id`); el `event_id` de este evento no sirve para localizar el
  evento de Google Calendar (lo gestiona n8n en su data table).

### 9.5 Estados, matriz de fallos e incidencias (RF-8, RF-10..RF-12; `detail` en español)

| Situación | `status` | `detail` (reutilizado de `automation_content`) | ¿Admite reproceso? |
|---|---|---|---|
| Evento registrado en la transacción de la cancelación, a punto de enviarse | `pending` | `NULL` | No (no-op, RF-14) |
| HTTP 2xx del webhook | `sent` | `NULL` + `sent_at` | No (no-op, RF-14) |
| `AUTOMATION_WEBHOOK_URL` vacía (flujo normal o reproceso) | `skipped` | `Automatización no configurada.` | No (no-op, RF-14) |
| Timeout (`TimeoutError`) | `failed` | `Tiempo de espera agotado (timeout).` | Sí (transitorio) |
| `HTTPError` 4xx permanente: 400, 401, 403, 404, 405, 409, 422 y demás 4xx **excepto 429** | `failed` | `Respuesta no válida del servicio (HTTP {code}).` | **No** (permanente, DP-05) |
| `HTTPError` **429 Too Many Requests** | `failed` | `Respuesta no válida del servicio (HTTP 429).` | Sí (transitorio, excepción expresa) |
| `HTTPError` 5xx | `failed` | `Respuesta no válida del servicio (HTTP {code}).` | Sí (transitorio, fallo del servidor) |
| `URLError` sin `HTTPError` / conexión rechazada | `failed` | `Servicio de automatización no disponible.` | Sí (transitorio) |
| Otra excepción | `failed` | `Error inesperado durante la automatización.` | Sí (transitorio) |

**Clasificación por código (D-010-01, RF-16; DP-01/DP-05).** El literal vigente
es **«Respuesta no válida del servicio (HTTP {code}).»** y no cambia (DP-01
descarta el literal alternativo propuesto). La captura es **ordenada**:
`TimeoutError → HTTPError → URLError → Exception`; `HTTPError` debe ir **antes**
de `URLError` porque es su subclase (causa raíz del defecto). El helper único
`automation_service._register_publication_failure()` traduce la excepción al
`detail` en las cinco funciones (`publish_cancelled_event`,
`reprocess_automation_event`, `on_appointment_confirmed`,
`email_service.send_confirmation`, `email_service.send_cancellation`). Los 5xx
se consideran transitorios; el 429 se exceptúa expresamente; el resto de 4xx son
permanentes. **No hay reintentos automáticos**: la clasificación solo decide si
el administrador puede reprocesar el evento (RF-13..RF-15). La no
reintentabilidad se decide por el `detail` persistido dentro del **mismo
`UPDATE` atómico** de `claim_failed_event()` (`detail IS NULL OR detail NOT LIKE
<patrón 4xx> OR detail LIKE <patrón 429>`), sin `SELECT` previo ni cambios de
esquema.

**Matriz de fallos (RF-10, RF-11, RF-12; idéntica a la spec):**

| Fallo | Cancelación de la cita | Evento `appointment.cancelled` |
|---|---|---|
| El registro del evento falla **antes** del commit (fallo de la transacción) | **No queda confirmada**: rollback de la operación completa; la cita conserva su estado anterior | No se crea ningún registro |
| El commit se completa pero falla el POST al webhook | **Permanece confirmada** (RF-10) | Queda `failed` con el motivo; reprocesable vía `reprocess_automation_event()` (RF-13) |
| Webhook no configurado (URL vacía) | **Permanece confirmada** (RF-8) | Queda `skipped` con su detalle |

Ningún fallo de **publicación** altera la cita: la cancelación ya está
commitada (RF-10). Sin reintentos automáticos. Cuatro estados fijos
(`pending`, `sent`, `skipped`, `failed`); `UNIQUE(event_id)` garantiza un
único registro por cancelación (RF-8). Durante el reproceso, la admisión
atómica transiciona `failed → pending` (F2-D12); si el proceso se
interrumpiera en ese intervalo, el evento quedaría `pending` — **misma
limitación operativa del `pending` huérfano, aceptada en esta fase** (§9.1).
Sin literales nuevos (F2-D10).

### 9.6 Algoritmo en pseudocódigo (fase 2, enmienda 2)

```text
# --- content/automation_content.py ------------------------------------
CANCELLED_EVENT_TYPE: str = "appointment.cancelled"        # [RF-8][RF-9] (ya en rama)
CANCELLED_EVENT_VERSION: int = 1
DETAIL_INVALID_RESPONSE_PREFIX = DETAIL_INVALID_RESPONSE_TEMPLATE.split("{status_code}")[0]
DETAIL_PERMANENT_REJECTION_PATTERN = DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code="4__")
DETAIL_RETRYABLE_REJECTION_PATTERN = DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code="429")
                                                          # [RF-16] derivados (DP-01/DP-02)

# --- services/automation_service.py -----------------------------------
FUNCTION _register_publication_failure(event_id, error, database_path) -> None:
    # único punto de traducción excepción → detail [RF-16]
    IF isinstance(error, TimeoutError):        detail = DETAIL_TIMEOUT
    ELIF isinstance(error, urllib.error.HTTPError):
        detail = DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=error.code)
    ELIF isinstance(error, urllib.error.URLError): detail = DETAIL_UNAVAILABLE
    ELSE:                                      detail = DETAIL_UNEXPECTED
    events_repository.mark_failed(event_id, detail, database_path)

FUNCTION _build_automation_event(appointment, event_type, event_version) -> dict:
    RETURN {                                             # allowlist sin PII [RF-9]
        "event_id": f"{event_type}:{appointment.id}:v{event_version}",
        "event_type": event_type,
        "event_version": event_version,
        "occurred_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "appointment": {"id": appointment.id, "service": appointment.service,
                        "date": appointment.date, "time": appointment.time,
                        "status": appointment.status}}   # 'cancelled' tras la transición

FUNCTION build_event(appointment):                        # firma pública INTACTA
    RETURN _build_automation_event(appointment, EVENT_TYPE, EVENT_VERSION)

FUNCTION build_cancelled_event(appointment) -> dict:      # [RF-9]
    RETURN _build_automation_event(
        appointment, CANCELLED_EVENT_TYPE, CANCELLED_EVENT_VERSION)

FUNCTION publish_cancelled_event(appointment, database_path,
                                 url="", timeout=3.0, auth="") -> None:
    # SOLO publicación; el registro `pending` YA existe (misma transacción
    # que la cancelación, RF-11). Nunca propaga [RF-10].  POST tras commit.
    TRY:
        event = build_cancelled_event(appointment)
        event_id = str(event["event_id"])
        IF NOT url:
            events_repository.mark_skipped(event_id, DETAIL_NOT_CONFIGURED,
                                           database_path); RETURN   # [RF-8]
        TRY: status_code = _post_webhook(url, event, timeout, auth)
        CATCH TimeoutError:     _register_publication_failure(event_id, error, database_path); RETURN
        CATCH urllib.error.HTTPError: _register_publication_failure(event_id, error, database_path); RETURN
        CATCH urllib.error.URLError:  _register_publication_failure(event_id, error, database_path); RETURN
        CATCH Exception:        _register_publication_failure(event_id, error, database_path); RETURN
        IF 200 <= status_code < 300: mark_sent(event_id, database_path)
        ELSE: mark_failed(… DETAIL_INVALID_RESPONSE_TEMPLATE.format(…))
    CATCH Exception:
        RETURN   # un fallo de publicación jamás afecta la cancelación [RF-10]

FUNCTION reprocess_automation_event(event_id, database_path,
                                    url="", timeout=3.0, auth="") -> bool:
    # Reproceso explícito del administrador sobre un evento
    # `appointment.cancelled` en estado `failed` [RF-13]; sin UI ni endpoint.
    TRY:
        # Admisión atómica condicionada al estado [RF-15]: solo una solicitud
        # concurrente transiciona failed → pending; el resto ve rowcount 0.
        # D-010-01 (RF-16): los 4xx permanentes no se readmiten dentro del mismo
        # UPDATE; 429 y 5xx sí (patrones derivados del literal, DP-02/DP-05).
        admitted = events_repository.claim_failed_event(
            event_id, database_path,
            permanent_pattern=DETAIL_PERMANENT_REJECTION_PATTERN,
            retryable_pattern=DETAIL_RETRYABLE_REJECTION_PATTERN)
        IF NOT admitted: RETURN False                    # no-op [RF-14]
        event_row = events_repository.get_by_event_id(event_id, database_path)
        appointment = appointments_repository.get_appointment_by_id(
            event_row.appointment_id, database_path)
        event = build_cancelled_event(appointment)       # mismo event_id [RF-13]
        IF NOT url:
            mark_skipped(event_id, DETAIL_NOT_CONFIGURED, database_path)
            RETURN True                                  # [RF-8] misma semántica
        TRY: status_code = _post_webhook(url, event, timeout, auth)
        CATCH TimeoutError:     _register_publication_failure(event_id, error, database_path); RETURN True
        CATCH urllib.error.HTTPError: _register_publication_failure(event_id, error, database_path); RETURN True
        CATCH urllib.error.URLError:  _register_publication_failure(event_id, error, database_path); RETURN True
        CATCH Exception:        _register_publication_failure(event_id, error, database_path); RETURN True
        IF 200 <= status_code < 300: mark_sent(event_id, database_path)
        ELSE: mark_failed(… DETAIL_INVALID_RESPONSE_TEMPLATE.format(…))
        RETURN True
    CATCH Exception:
        RETURN False   # jamás propaga; el registro queda trazado

# --- persistence/appointments_repository.py ----------------------------
FUNCTION update_appointment_status_with_pending_event(
        appointment_id, new_status, event_id, event_type, event_version,
        database_path) -> Appointment | None:             # [RF-11][RF-12]
    # MISMA conexión y transacción: o ambas confirmadas o ninguna.
    TRY:
        connection = get_connection(database_path)
        TRY:
            cursor = connection.execute(
                UPDATE appointments SET status = ?
                 WHERE id = ? AND status = 'confirmed',    # transición atómica
                (new_status, appointment_id))
            IF cursor.rowcount == 0:
                connection.rollback(); RETURN None         # sin evento, sin cambio
            connection.execute(
                INSERT INTO automation_events (
                    event_id, event_type, event_version, appointment_id, status)
                VALUES (?, ?, ?, ?, 'pending'),            # registro conjuntante
                (event_id, event_type, event_version, appointment_id))
            connection.commit()                            # «sin traza local,
                                                           #  sin cancelación
                                                           #  confirmada»
        CATCH:
            connection.rollback()                          # [RF-12] rollback
            RAISE                                          # cita SIN cancelar
        FINALLY: connection.close()
        RETURN get_appointment_by_id(appointment_id, database_path)
    # sqlite3.IntegrityError/OperationalError propagan al servicio (fallo real)

# --- services/appointment_service.py ----------------------------------
APPOINTMENT_NOT_FOUND: str = "appointment_not_found"
ALREADY_CANCELLED: str = "already_cancelled"

FUNCTION cancel_appointment(appointment_id, database_path, url="", timeout=3.0,
                            auth_header="") -> Appointment | str:
    appointment = repository.get_appointment_by_id(appointment_id, database_path)
    IF appointment IS None: RETURN APPOINTMENT_NOT_FOUND
    event_id = f"{CANCELLED_EVENT_TYPE}:{appointment_id}:v{CANCELLED_EVENT_VERSION}"
    TRY:                                                   # [RF-11][RF-12]
        updated = repository.update_appointment_status_with_pending_event(
            appointment_id, STATUS_CANCELLED, event_id,
            CANCELLED_EVENT_TYPE, CANCELLED_EVENT_VERSION, database_path)
    CATCH (sqlite3.IntegrityError, sqlite3.OperationalError):
        RAISE   # registro fallido → rollback; la cita NO queda Cancelada (RF-12)
    IF updated IS None:
        RETURN ALREADY_CANCELLED   # ya cancelada: SIN emisiones [RF-4][CL-1]
    automation_service.publish_cancelled_event(          # [RF-8] POST tras
        updated, database_path, url, timeout, auth_header)  # commit; primero (F2-D1)
    email_service.send_cancellation(                      # después (F2-D1)
        updated, database_path, url, timeout, auth_header)
    RETURN updated

# create_booking() y web/: SIN CAMBIOS (firma e HTTP intactos)     [RF-3]
```

> **Nota sobre `on_appointment_cancelled()` (T19, ya en la rama)**: la función
> actual registra el evento con `insert_event` **post-commit**, en conexión
> separada — diseño del plan previo, **desalineado con RF-11/RF-12**. En T22
> se reemplaza por la transacción de `update_appointment_status_with_pending_event()`
> + `publish_cancelled_event()` (solo publicación). El orden F2-D1 (negocio
> antes que correo) y el contrato público de `cancel_appointment()` se
> conservan; los TC-010-101..109 ya verdes deben seguir pasando sin relajarse
> (ver §9.8.1).

### 9.7 Decisiones técnicas (fase 2)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| F2-D1 | **Orden de emisión: evento de negocio `appointment.cancelled` PRIMERO, correo `appointment.cancellation_email` DESPUÉS**, ambos tras el commit y ambos best-effort | (a) Precedente exacto de HU-007/008 en `create_booking()`: evento de negocio (`appointment.confirmed`) antes que la acción técnica de correo (`confirmation_email`). (b) RF-8 exige independencia del resultado del correo: emitiéndolo primero se cumple trivialmente — un fallo total del envío del correo no puede condicionarlo. (c) Semántica de la Spec 007 RF-13: el evento de negocio es «la cita fue cancelada» (hecho confirmado) y es el que activa el borrado de Calendar; el correo es una acción técnica posterior. | *Correo primero*: invierte el precedente de HU-007/008 y haría que el hecho de negocio dependiera en el tiempo de una acción técnica, contrario al espíritu de RF-8. *Emitirlos en paralelo/ambos al final*: complejidad nueva sin ganancia (son síncronos, secuenciales y baratos); el orden entre dos best-effort independientes no altera su semántica de fallo individual | RF-8 |
| F2-D2 | **Funciones nuevas en `automation_service.py`**: composición del payload con el helper privado `_build_automation_event()` (allowlist única) y `build_cancelled_event()` (ya en la rama); **publicación** del evento en `publish_cancelled_event()` (enmienda 2: el registro `pending` vive en la transacción de la cancelación, F2-D11) y **reproceso** en `reprocess_automation_event()` (F2-D3); constantes en `automation_content.py`; `build_event()` conserva su firma pública | El evento de negocio pertenece al dominio de automatización (mismo módulo que `appointment.confirmed`); la Spec 007 RF-13 exige distinguirlo del correo, y `email_service` es el dominio de la composición de mensajes. El helper evita dos copias del allowlist (deriva de contrato). El patrón «una función por evento que nunca propaga» es el precedente aceptado HU-007 → HU-008 → HU-010. La separación registro-transaccional (repositorio) / publicación-post-commit (servicio) es la que RF-11/RF-12 exigen | *Ponerlo en `email_service`*: mezcla dominios (RF-13) y contradice la separación de responsabilidades del §9.3. *Duplicar `build_event()` íntegro*: dos allowlists que pueden divergir. *Parametrizar `on_appointment_confirmed(event_type=…)`*: renombra semánticamente un flujo cerrado y aceptado, mayor superficie de regresión sin ganancia. *Mantener `on_appointment_cancelled()` con `insert_event` interno* (estado de la rama): incumple RF-11 al registrar en conexión separada | RF-8, RF-9, RF-11, RF-13 |
| F2-D3 | **Reproceso del evento `failed`: función de servicio `reprocess_automation_event()` (RF-13..RF-15)** — sin UI ni endpoint, invocada únicamente por decisión explícita del administrador; admite solo eventos `appointment.cancelled` en estado `failed`, transiciona atómicamente `failed → pending` como admisión, recupera el payload (reconstruido deterministamente con el mismo `event_id`) y el registro existente, realiza **un único** nuevo POST y traza el resultado (`sent` \| `failed` con detalle en español \| `skipped` si la URL está vacía). Sobre `sent`, `skipped` y `pending`: no-op sin POST ni modificación (RF-14). Sin reintentos automáticos | Resolución aprobada por la usuaria (enmienda 2) de la contradicción del texto anterior («choca en el INSERT y se descarta» vs. «reintento sin duplicados» vs. «lo decide el administrador»): el administrador decide y el mecanismo es programático, reutilizando la fila y el `UNIQUE(event_id)`; mismo patrón de servicio sin UI que `cancel_appointment()` (F2-D1/D15) | *POST manual del admin con payload reconstruido* (F2-D3 anterior): sin traza en la app y propenso a error. *Reinvocar `publish_cancelled_event()`/`on_appointment_cancelled()`*: no-op o doble registro según la versión, no es reproceso. *Reintentos automáticos/colas/workers*: infraestructura nueva, fuera de alcance. *Almacenar el payload JSON en la tabla*: cambio de esquema sin requisito (el payload es reconstruible y determinista). *Nuevos estados o marcas de «en curso»*: la usuaria fijó cuatro estados y postergó la extensión | RF-13, RF-14, RF-15 |
| F2-D11 | **Atomicidad transaccional del registro con la cancelación (RF-11/RF-12)**: nueva operación de persistencia (propuesta: `update_appointment_status_with_pending_event()` en `appointments_repository`, de la menor superficie posible) que ejecuta el `UPDATE … AND status='confirmed'` y el `INSERT` del evento `pending` en **la misma conexión y transacción** SQLite; commit conjuntivo («sin traza local, sin cancelación confirmada»); fallo del INSERT → **rollback y la cita no queda Cancelada** (RF-12), sin evento ni notificación derivada. El `update_appointment_status()` existente se conserva para no romper call sites cerrados. **Limitación reconocida y aceptada por la usuaria**: si el proceso termina después del commit y antes del POST, el evento puede permanecer `pending` indefinidamente y, con el mecanismo actual, no habrá vía de recuperación (sin estados nuevos en esta fase; el reproceso cubre solo `failed`) | Corrige la desalineación del código de T19/T20 (registro `insert_event` post-commit en conexión separada), aceptada como consecuencia del cambio de diseño y no como defecto; hasta implementarla no se afirma que la atomicidad está garantizada por el código. Hoy `update_appointment_status` e `insert_event` abren conexiones distintas: entre el commit del UPDATE y el INSERT hay una ventana sin traza local que RF-11 prohíbe. La publicación (POST) se queda tras el commit, igual que hasta ahora | *Dejar el registro post-commit* (estado actual): incumple RF-11/RF-12 y la matriz de fallos aprobada. *Transacción que incluya también el POST*: un fallo de red tumbaría la cancelación (contra RF-10). *Dos UPDATEs en transacciones separadas*: no es atomicidad. *Tabla o estados nuevos para el pending huérfano*: la usuaria fijó cuatro estados y aceptó la limitación para esta fase | RF-11, RF-12, RF-8, RF-10 |
| F2-D12 | **Exclusión de concurrencia del reproceso (RF-15)**: la admisión se garantiza con una **transición atómica condicionada al estado**, `UPDATE automation_events SET status='pending', detail=NULL WHERE event_id=? AND status='failed' AND event_type='appointment.cancelled' AND (detail IS NULL OR detail NOT LIKE <4xx permanente> OR detail LIKE <429>)` (`claim_failed_event()`; la condición por `detail` es de D-010-01/RF-16, DP-02); solo la solicitud que obtiene `rowcount = 1` realiza el intento; las demás son no-op (RF-14) sin POST ni modificación | SQLite serializa escrituras: el UPDATE condicional es un cierre natural de admisión sin colas, workers ni estados nuevos; mismo patrón de «transición condicional como exclusión» que el `UPDATE … AND status='confirmed'` de la cancelación (D6) | *SELECT previo + POST*: carrera entre chequeo y publicación (doble POST). *Bloqueo optimista con nueva columna `claimed_at`*: esquema nuevo y estados de facto nuevos. *Bloqueos explícitos/`BEGIN IMMEDIATE` en el servicio*: complejidad innecesaria para el volumen y sin requisito | RF-15, RF-16 |
| F2-D4 | **Coordinación con Spec 018 (y 017): cada cancelación emitirá DOS eventos al mismo webhook** (`appointment.cancelled` + `appointment.cancellation_email`). Riesgo anotado para **TC-018-005** (plan 018 §6.1: «1 evento `sent`» de `cancellation_email`), TC-018-007 y TC-018-012, y para los futuros tests de la 017: sus verificaciones deberán **filtrar por `event_type`** (precedente D15 de HU-008, ya aplicado dentro de los propios TC-010-001..007, que por eso **no se rompen**) | Tras esta fase, contar eventos o POSTs de una cancelación sin filtrar daría 2 en vez de 1 → falsos fallos en 017/018 al implementarlos. La adaptación de 018 es **spec-backed** (enmiendas 010 y 007 aprobadas) pero pertenece al plan de la 018; este plan solo documenta el riesgo y la dirección de la solución | *Adaptar el plan 018 desde aquí*: fuera del alcance de esta fase (cada spec planifica sus tests); *no filtrar y aceptar recuentos globales*: frágil y contrario al precedente D15 | RF-8, regresión |
| F2-D5 | **Sin dependencias ni variables de entorno nuevas**; se reutilizan `AUTOMATION_WEBHOOK_URL`/`AUTOMATION_TIMEOUT_SECONDS`/`AUTOMATION_WEBHOOK_AUTH_HEADER` (mismo webhook; URL vacía → `skipped`) | Mismo canal que HU-007/008/010 (D8 cerrado); constitución #1; cero config nueva | *`CANCELLED_WEBHOOK_URL` propio*: duplica config y secretos sin ganancia | RF-8, RF-10 |
| F2-D6 | **Sin cambios de esquema**: se reutiliza `automation_events` con su `UNIQUE(event_id)` y su ciclo `pending → sent \| skipped \| failed` | El modelo de fiabilidad pedido por RF-8/RF-10 ya existe; la unicidad en el punto de persistencia es constitución #5 | *Tabla nueva `business_events`*: duplica infraestructura sin requisito | RF-8, RF-10 |
| F2-D7 | **Rama `feature/hu-010-rf8-10` desde `main`** (baseline 204) | Aislamiento por HU/fase (AGENTS.md); `main` limpia tras el cierre de HU-010 | *Rama desde otra feature*: arrastra pendientes | regresión |
| F2-D8 | **Numeración de tests: bloque TC-010-101…** (tras la enmienda 2: funciones 101–118; 119 = corrida de suite — el antiguo 112 «corrida» migra al 119 para ceder el 112 a la función de atomicidad positiva; **ningún ID ya usado se reutiliza**: los 101–110 del plan previo conservan su ID, con redefinición explícita del 110) | Los TC-010-001..018 están cerrados y referenciados en la evidencia de HU-010; el bloque 019–100 queda reservado para futuras enmiendas del alcance cerrado; el salto a 101 deja colisión imposible | *Continuar en TC-010-019*: correries con enmiendas futuras del alcance cerrado. *Reutilizar el 110 sin redefinir*: confundiría la aserción antigua (aislamiento) con la nueva (rollback RF-12) | trazabilidad |
| F2-D9 | **Los tests se mantienen en `tests/test_cancellation_service.py`** (reutilizando `_future_weekday`, `_booking_data`, `_count_events`, `_cancelled_posts()`; auxiliares nuevos solo si hacen falta para el reproceso, p. ej. un helper que fuerce un estado `failed`) | Mismo dominio (cancelación), mismas fixtures y precedente de filtrado; sin duplicar helpers | *Fichero nuevo `test_cancelled_event.py`*: duplicaría helpers y dispersaría el dominio de la cancelación | RF-8..RF-15 |
| F2-D10 | **Sin literales nuevos**: `skipped` reutiliza `DETAIL_NOT_CONFIGURED` («Automatización no configurada.») y los `failed` los `DETAIL_*` ya aceptados en HU-007/008/010 | Mismo canal, mismo copy ya probado; el evento no tiene mensajes visibles ni subject (constitución #6 se cumple con los `detail` existentes en español) | *Literal de cancelación nuevo para el `skipped`*: duplicidad textual sin necesidad (el de correo ya tiene el suyo propio en `email_content`) | RF-10 |
| F2-D13 | **`tests/expected_content.py` sin cambios por la enmienda 2** (decisión de la usuaria 2026-10-23) y **límite de alcance transaccional**: solo `appointment.cancelled` obtiene atomicidad y reproceso; `appointment.cancellation_email` conserva su registro post-commit con su ventana de fallo conocida | Los textos reescritos de la enmienda 2 (RF, contratos, tablas) no alteran literales visibles de correo ni de estados: los valores de `email_content`/`appointment_content` y sus espejos siguen siendo los de HU-010; no existe tarea de sincronización que crear. La atomicidad del correo exigiría tocar `send_cancellation()` (código cerrado de HU-010) sin requisito que lo respalde: la usuaria mantuvo el correo sin cambios | *Sincronizar `expected_content.py` «por si acaso»*: tarea falsa que toca un fichero de tests cerrado sin cambio de requisito. *Extender la transacción al correo de cancelación*: amplía alcance sin spec; la ventana post-commit del correo queda como limitación conocida (spec: duda RESUELTA de la enmienda 2) | RF-8, RF-11, trazabilidad |

### 9.8 Estrategia de tests (fase 2, enmienda 2)

Ejecución: `python -m pytest -q` (esperado **222 PASS / 0 FAIL** =
204 previos + 18 funciones TC-010-101..118) ·
`python -m pytest tests/test_cancellation_service.py -v`.
Estado posterior a **D-010-01** (2026-10-30, T8): `python -m pytest -q` →
**300 PASS / 0 FAIL**; el bloque TC-D010-01..16 se detalla al final de §9.8.1.
Punto de parcheo único del POST: `automation_service._post_webhook` (mismo
patrón que HU-007/008/010, hermeticidad). Para el caso de **registro
fallido (RF-12)** se parchea el punto de inserción de la transacción en la
persistencia (nunca se usa red real). Sin `sleep`, BD temporal por fixture,
concurrencia simulada de forma determinista (re-entrancia, ver TC-010-117).

**Estado real de los tests en la rama (tras T19/T20)**: TC-010-101, 102, 103,
104, 108 y 109 están **implementados y verdes** (210 PASS). Todos ejercitan
`cancel_appointment()` de extremo a extremo o `build_cancelled_event()`, por lo
que **no se modifican**: son la red de regresión que debe seguir en verde
tras el rediseño transaccional de T22–T24. **Los TC-010-001..018 cerrados de
HU-010 tampoco se modifican** (filtran POSTs y eventos por
`event_id`/`event_type`, precedente D15; helpers `_cancellation_posts()` y
`_count_events(event_id, …)`).

**Tests de T19/T20 afectados por el cambio transaccional (verificación
realizada sobre el código)**:

| TC | ¿Toca el registro? | Efecto del rediseño | Acción |
|---|---|---|---|
| TC-010-101 | No (solo aserciones de resultado) | Ninguno: el POST y el `sent` siguen tras el commit | Sin cambios; debe seguir verde |
| TC-010-102 | No (unitario de `build_cancelled_event`) | Ninguno | Sin cambios |
| TC-010-103 | No | Ninguno | Sin cambios |
| TC-010-104 | No (consulta `get_by_event_id`) | Ninguno: `publish_cancelled_event()` sigue marcando `skipped` | Sin cambios |
| TC-010-108 | No | Ninguno: la guarda `confirmed → cancelled` devuelve `ALREADY_CANCELLED` antes de registrar | Sin cambios; **reinterpretado** (ver nota) |
| TC-010-109 | No | Ninguno (orden negocio → correo preservado) | Sin cambios |
| TC-010-110 (definición antigua) | Sí (parcheaba `insert_event` esperando cancelación intacta) | **Invertido por RF-12**: un fallo del registro ahora debe producir rollback y cancelación NO confirmada | **Redefinido** (ver tabla) |
| TC-010-105/106/107 (sin implementar) | No (parchean solo `_post_webhook`) | Son ya el aislamiento RF-10 correcto: fallo de **publicación** tras commit → cita intacta | Se conservan; implementar en T25 |
| TC-010-009 (HU-010, cerrado) | Parchea `insert_event` del repositorio de eventos | El registro del negocio deja de pasar por `insert_event`; el test solo verifica que la cancelación no se revierte por el correo, así que sigue verde | Sin cambios; verificar en T22 |

> **Nota sobre TC-010-108**: su aserción original (segunda
> `cancel_appointment()` → `ALREADY_CANCELLED`, 1 fila y 1 POST) se mantiene
> como cobertura de la **guarda de transición** (RF-14 vía cancelación: no
> hay reproceso automático). La cobertura del **reproceso real** de un
> `failed` mediante `reprocess_automation_event()` es de los tests nuevos
> TC-010-113..118.

#### 9.8.1 Casos de prueba (fase 2)

| ID | Estado | Archivo | Objetivo y resultado esperado | RF/CA |
|---|---|---|---|---|
| TC-010-101 | **En rama** | `test_cancellation_service.py` | Cancelar con webhook y `_post_webhook` parcheado (200) → **1 POST de tipo `appointment.cancelled`** (filtrado), evento `sent` con `sent_at`, cita `cancelled`; el POST de `cancellation_email` también ocurre (1, filtrado por su tipo) | RF-8, CA-1 |
| TC-010-102 | **En rama** | `test_cancellation_service.py` | **Allowlist RF-9:** claves raíz exactas `{event_id, event_type, event_version, occurred_at, appointment}`; `event_id == "appointment.cancelled:{id}:v1"`; `event_version == 1`; claves de `appointment` exactas `{id, service, date, time, status}` y `status == "cancelled"`; **sin** `patient_name`, `email`, `phone`, `document_type`, `document_number`, `recipient`, `message` (raíz y `appointment`) | RF-9, CA-2 |
| TC-010-103 | **En rama** | `test_cancellation_service.py` | **Independencia del correo:** cita con `email` vacía → evento `appointment.cancelled` **`sent`** (1 POST de su tipo) mientras `appointment.cancellation_email` queda `failed`; la cita queda `cancelled` | RF-8, CA-1 |
| TC-010-104 | **En rama** | `test_cancellation_service.py` | **URL vacía:** cancelar sin webhook → evento `appointment.cancelled` `skipped` («Automatización no configurada.»), **0 POST** y cita `cancelled` | RF-8, RF-10, CA-3 |
| TC-010-105 | Por implementar (T25) | `test_cancellation_service.py` | **URLError** (publicación tras commit) → evento `appointment.cancelled` `failed` «Servicio de automatización no disponible.», **0 excepción** y cita sigue `cancelled` | RF-10, CA-4 |
| TC-010-106 | Por implementar (T25) | `test_cancellation_service.py` | **TimeoutError** → evento `failed` «Tiempo de espera agotado (timeout).» y cita intacta | RF-10, CA-4 |
| TC-010-107 | Por implementar (T25) | `test_cancellation_service.py` | **HTTP 500** → evento `failed` «Respuesta no válida del servicio (HTTP 500).» y cita intacta | RF-10, CA-4 |
| TC-010-108 | **En rama** (reinterpretado) | `test_cancellation_service.py` | **Guarda de transición:** segunda `cancel_appointment()` → `ALREADY_CANCELLED`, **1 fila** con `event_id = appointment.cancelled:{id}:v1` (UNIQUE) y **1 POST** acumulado de ese tipo; sin registro nuevo ni emisión derivada | RF-8, RF-14, CA-1/CA-7 |
| TC-010-109 | **En rama** | `test_cancellation_service.py` | **Orden F2-D1:** en `post.call_args_list` el POST de `appointment.cancelled` **precede** al de `appointment.cancellation_email` | RF-8 |
| TC-010-110 | **Redefinido** (T23) | `test_cancellation_service.py` | **Atomicidad RF-12:** parchear el punto de inserción del evento dentro de la transacción con `RuntimeError` → `cancel_appointment()` **propaga el error** (no devuelve la cita), la cita **sigue `confirmed`** (rollback), **0 filas** de `appointment.cancelled` y **0 POST** | RF-11, RF-12, CA-5 |
| TC-010-111 | Por implementar (T25) | `test_cancellation_service.py` | **Regresión/constitución:** `build_event()` sigue produciendo las 5 claves con `appointment.confirmed` (firma intacta); `automation_content.EVENT_TYPE` inalterado; sin imports de terceros en los módulos tocados; sin variables de entorno nuevas; `tests/expected_content.py` sin cambios (F2-D13) | RF-8, regresión |
| TC-010-112 | **Nuevo** (T23) | `test_cancellation_service.py` | **Atomicidad positiva RF-11:** `_post_webhook` con `side_effect` que, en el momento del POST, verifica en BD que la cita ya es `cancelled` **y** el evento `appointment.cancelled` está `pending` (traza conjunta confirmada antes de publicar); después el POST 200 lo deja `sent` | RF-11, CA-5 |
| TC-010-113 | **Nuevo** (T25) | `test_cancellation_service.py` | **Reproceso RF-13:** cancelar con `_post_webhook` → `URLError` (evento `failed`); llamar `reprocess_automation_event()` con POST 200 → **exactamente 1 POST del reproceso**, mismo `event_id`, **misma fila** (mismo `id` en `automation_events`), estado final `sent` con `sent_at` | RF-13, CA-6 |
| TC-010-114 | **Nuevo** (T25) | `test_cancellation_service.py` | **Reproceso con URL vacía (RF-13):** evento `failed` + `reprocess_automation_event()` sin URL → **0 POST**, estado `skipped` con «Automatización no configurada.» (misma semántica de URL vacía que el flujo normal) | RF-13, CA-6 |
| TC-010-115 | **Nuevo** (T25) | `test_cancellation_service.py` | **Reproceso que vuelve a fallar (RF-13):** `reprocess_automation_event()` con `URLError` → **1 POST**, estado `failed` con el detalle en español, sin excepción propagada | RF-13, CA-6 |
| TC-010-116 | **Nuevo** (T25) | `test_cancellation_service.py` | **No-op RF-14 (tabla de 4 estados):** sobre un evento `sent`, otro `skipped` y un `pending` huérfano simulado, `reprocess_automation_event()` en los tres → **0 POST** y el registro **sin modificación** (status y detail intactos); el reproceso solo se admite sobre `failed` | RF-14, CA-7 |
| TC-010-117 | **Nuevo** (T26) | `test_cancellation_service.py` | **Concurrencia RF-15:** evento `failed`; el `side_effect` del `_post_webhook` del primer reproceso invoca **re-entrantemente** un segundo `reprocess_automation_event()` sobre el mismo `event_id` → el segundo es no-op; total **1 POST** y un único cambio de estado (`sent`) | RF-15, CA-8 |
| TC-010-118 | **Nuevo** (T25) | `test_cancellation_service.py` | **Ámbito del reproceso (RF-13):** `claim_failed_event()`/`reprocess_automation_event()` sobre un evento fallido de **otro tipo** (`appointment.cancellation_email` o `appointment.confirmed`) → no admitido, **0 POST**, registro sin modificación; sobre un `appointment.cancelled` `failed` → admitido | RF-13, RF-14 |
| TC-010-119 | Corrida, no función | — | `python -m pytest -q` → **222 PASS / 0 FAIL** con los **204 previos** y los **6 TC de la rama** intactos | todos, finalización |

**Casos D-010-01 — clasificación HTTP y no reintentabilidad (RF-16; T1..T8):**

| ID | Estado | Archivo | Objetivo y resultado esperado | RF/CA |
|---|---|---|---|---|
| TC-D010-01 | En rama (T1) | `test_cancellation_service.py` | `HTTPError` **400** real en la publicación inicial → evento `appointment.cancelled` `failed` con «Respuesta no válida del servicio (HTTP 400).»; cita `cancelled`; sin excepción | RF-10, RF-16, CA-D010-01/02/08 |
| TC-D010-02 | En rama (T1) | `test_cancellation_service.py` | `HTTPError` **500** real → `failed` con «Respuesta no válida del servicio (HTTP 500).»; cita intacta | RF-10, RF-16, CA-D010-01/02/09 |
| TC-D010-03 | Cubierto por TC-010-105 (detalle) y TC-010-113/117 + TC-D010-11(b) (readmisión) | `test_cancellation_service.py` | `URLError` sin `HTTPError` → `failed` «Servicio de automatización no disponible.» (acreditado por TC-010-105); la **readmisión** la acreditan TC-010-113/117 y TC-D010-11(b). La readmisión específica de `URLError` **no tiene test dedicado**: verificada por inspección del SQL y sonda QA del revisor (cobertura automatizada parcial) | RF-10, RF-16, CA-D010-06 |
| TC-D010-04 | Cubierto por TC-010-106 (detalle) y TC-010-113/117 + TC-D010-11(b) (readmisión) | `test_cancellation_service.py` | `TimeoutError` → `failed` «Tiempo de espera agotado (timeout).» (acreditado por TC-010-106); la **readmisión** la acreditan TC-010-113/117 y TC-D010-11(b). La readmisión específica de excepción inesperada **no tiene test dedicado**: verificada por inspección del SQL y sonda QA del revisor (cobertura automatizada parcial) | RF-10, RF-16, CA-D010-05 |
| TC-D010-05 | En rama (T2) | `test_automation_service.py` | Contrato real: `urlopen` parcheado eleva `HTTPError(400)`; `_post_webhook()` lo propaga conservando `code == 400` | RF-10, RF-16 |
| TC-D010-06 | En rama (T5) | `test_cancellation_service.py` | `failed` con `detail` de **HTTP 400** → `claim_failed_event()` devuelve `False`; **0 POST**; `status`/`detail` intactos; misma fila | RF-13, RF-14, RF-16, CA-D010-04/12/13 |
| TC-D010-07 | En rama (T5) | `test_cancellation_service.py` | `failed` con `detail` de **HTTP 422** → igual que TC-D010-06 | RF-13, RF-14, RF-16, CA-D010-04/12/13 |
| TC-D010-08 | En rama (T5) | `test_cancellation_service.py` | `failed` con `detail` de **HTTP 429** → admitido (transitorio); **1 POST**; `sent`; misma fila | RF-13, RF-16, CA-D010-12 |
| TC-D010-09 | En rama (T5) | `test_cancellation_service.py` | `failed` con `detail` de **HTTP 500** → admitido (transitorio); **1 POST**; `sent`; misma fila | RF-13, RF-16, CA-D010-12 |
| TC-D010-10 | Cubierto por TC-010-113/115/117 y TC-D010-11 | `test_cancellation_service.py` | Reproceso de `failed` por `TimeoutError`/`URLError`: admisión `failed → pending`, 1 POST y estado trazado | RF-13, RF-15, RF-16, CA-D010-07 |
| TC-D010-11 | En rama (T7) | `test_cancellation_service.py` | Concurrencia: un `failed` por 400 **nunca** se readmite; un `failed` por timeout se admite **una sola vez** (re-entrancia determinista) | RF-14, RF-15, RF-16, CA-D010-04/07 |
| TC-D010-12 | En rama (T4) | `test_automation_service.py` | `on_appointment_confirmed()` con `HTTPError(400)` → `appointment.confirmed` `failed` con el literal vigente; reserva intacta | RF-10, RF-16, CA-D010-11 |
| TC-D010-13 | En rama (T4) | `test_email_service.py` | `send_confirmation()` con `HTTPError(400)` → `appointment.confirmation_email` `failed` con el literal vigente; reserva intacta | RF-10, RF-16, CA-D010-11 |
| TC-D010-14 | En rama (T4) | `test_email_service.py` | `send_cancellation()` con `HTTPError(400)` → `appointment.cancellation_email` `failed` con el literal vigente; cancelación intacta | RF-10, RF-16, CA-D010-11 |
| TC-D010-15 | En rama (T7) | `test_cancellation_service.py` | No-op: `sent`, `skipped`, `pending` y `failed` de **otro tipo** → **0 POST** y registro sin modificación | RF-14, RF-16 |
| TC-D010-DP02 | En rama (T6) | `test_cancellation_service.py` | El prefijo y los patrones (4xx permanente / 429) se derivan de `DETAIL_INVALID_RESPONSE_TEMPLATE`; un cambio de copy rompe la prueba en vez de la clasificación | RF-16, CA-D010-13 |
| TC-D010-16 | Corrida (T8) | — | `python -m pytest -q` → **300 PASS / 0 FAIL**, sin red real y sin cambios de literales ni de `tests/expected_content.py` | todos, finalización |

> **Alcance de la corrección (D-010-01):** el defecto no añade estados,
> columnas, tablas, índices ni migraciones; el `detail` persistido es el único
> criterio de reintentabilidad y la exclusión de 4xx permanentes se aplica en el
> **mismo `UPDATE` atómico** de `claim_failed_event()` (RF-15). Los 5xx y el 429
> son transitorios; el resto de 4xx son permanentes. El literal vigente se
> conserva (DP-01) y no se modifican las Specs/planes 007/008 ni
> `tests/expected_content.py`.

> **Nota de recuento**: TC-010-119 es la corrida de la suite; las funciones
> del bloque son **18** (TC-010-101..118; 6 ya en la rama + 12 por
> implementar) → total esperado **222** (204 + 18). **0 FAIL con los 204
> previos y los 6 TC de T19/T20 sin enmiendas** es la condición real de
> cierre. La numeración anterior (TC-010-112 como corrida) queda
> reasignada: el 112 pasa a función (atomicidad positiva) y la corrida
> migra al 119, sin reutilizar ningún ID ya usado.
>
> **Bloque D-010-01 (RF-16)**: los TC-D010-01..16 se añaden sin reutilizar IDs
> del bloque TC-010-*; tras T8 la corrida real es **300 PASS / 0 FAIL**
> (2026-10-30).

#### 9.8.2 Pirámide y evidencia

1. **Unitarias** — `build_cancelled_event()` (allowlist, event_id, versión,
   sin PII), `build_event()` intacto y `claim_failed_event()` (admisión
   condicionada). `[RF-9][RF-15]`
2. **Integración de persistencia** — transacción UPDATE+INSERT: registro
   fallido → rollback (cita sin cancelar, 0 eventos, 0 POST); registro
   correcto → traza conjunta verificada en el momento del POST.
   `[RF-11][RF-12]`
3. **Integración de servicio** — `cancel_appointment()` y
   `reprocess_automation_event()` con `_post_webhook` parcheado:
   2xx→`sent`, sin URL→`skipped`, `URLError`/`TimeoutError`/no-2xx→`failed`
   (clasificación por código: 4xx permanentes, 429/5xx transitorios, RF-16),
   orden de emisión, independencia del correo, no-op sobre no-`failed`,
   reproceso → misma fila, concurrencia re-entrante → 1 intento.
   `[RF-8][RF-10][RF-13][RF-14][RF-15][RF-16]`
4. **Regresión** — suite completa: 204 previos + 6 TC de la rama verdes sin
   enmiendas. `[todos]`
5. **Demo manual** — servidor `python app.py` + **receptor local stdlib
   efímero** (patrón HU-010) con `AUTOMATION_WEBHOOK_URL` apuntando a él y
   `cancel_appointment()`/`reprocess_automation_event()` desde un
   REPL/script: (a) cancelar → receptor captura **2 POST**
   (`appointment.cancelled` y `appointment.cancellation_email`) y ambos
   eventos `sent`; (b) **URL vacía** → ambos `skipped`, 0 POST;
   (c) **receptor apagado** → ambos `failed` con motivo y la cita permanece
   `cancelled`; (d) **`cancel_appointment()` repetida** → `already_cancelled`
   y 0 POST nuevos; (e) **`reprocess_automation_event()`** sobre el evento
   `failed` con el receptor encendido → **1 POST nuevo**, misma fila,
   estado `sent`; (f) verificar en `automation_events` la fila
   `appointment.cancelled:{id}:v1`. Live n8n opcional solo si la usuaria lo
   indica (con workflow activo y URL de producción; el token solo en entorno).
   Sin cambios visuales → sin capturas 1280/375.
6. **Informe QA** — `docs/evidencias/hu-010/qa-hu-010-rf8-10.md` (añadido,
   sin tocar el `qa-hu-010.md` cerrado) con PASS/FAIL por TC, checkbox de
   aceptación y trazabilidad **RF-8..RF-15 / CA-1..CA-8** (skill `pytest-qa`).
   Prohibido eliminar/`skip`/relajar aserciones para pasar.

### 9.9 Secuencia de implementación (fase 2, enmienda 2)

> Los pasos de código de T16–T20 (constantes, `build_cancelled_event`,
> disparo inicial) ya están **commiteados en la rama** (hasta `223a43c`)
> contra el texto previo; la corrección es trabajo nuevo. La secuencia
> corregida corresponde a las tareas **T21–T27** de `task.md`, agrupadas en
> **2A = pasos 0–4 (T21–T25)** y **2B = pasos 5–6 (T26–T27)** (división
> aprobada por la usuaria el 2026-10-23; la 2B se inicia tras cerrar la 2A):

0. **T21 — Reaprobación bloqueante** — **cumplida 2026-10-23** («Apruebo» +
   «Divide la fase»): reaprobación de este §9 (enmienda 2) y de las tareas
   T21–T27 por la usuaria; división 2A/2B decidida.
1. **T22 — Corrección transaccional**: `update_appointment_status_with_pending_event()`
   (UPDATE cita + INSERT `pending`, misma conexión; rollback ante fallo del
   registro) en el repositorio + `publish_cancelled_event()` (solo
   publicación post-commit) en el servicio + `cancel_appointment()` usa la
   operación transaccional; conservar orden F2-D1 y firmas públicas →
   TC-010-101..109 verdes sin enmiendas.
2. **T23 — Tests de atomicidad**: TC-010-110 (redefinido, rollback RF-12) y
   TC-010-112 (traza conjunta en el momento del POST, RF-11).
3. **T24 — Reproceso (código)**: `claim_failed_event()` (admisión atómica) +
   `reprocess_automation_event()`.
4. **T25 — Tests de reproceso y fallo de publicación**: TC-010-105/106/107
   (fallos de publicación), TC-010-111 (regresión/constitución) y
   TC-010-113..116, TC-010-118 (reproceso).
5. **T26 — Concurrencia y suite completa**: TC-010-117 (re-entrante
   determinista) → **222 PASS / 0 FAIL** (TC-010-119).
6. **T27 — Evidencia y cierre**: demo §9.8.2 (incluye el paso del reproceso
   sobre un `failed`) + informe `qa-hu-010-rf8-10.md`; commits por fase,
   push, `MEMORY.md`, aceptación de la usuaria y servidor de revisión en
   marcha; **registro del pendiente F2-D4** para el coordinador (anotar el
   filtro por `event_type` en el plan 018 cuando se autorice).

### 9.10 Pendientes y aprobaciones (bloquean declarar COMPLETADO)

- [x] **Aprobación del plan §9 en su versión previa a la enmienda 2
      (F2-D1..F2-D10) por la usuaria** — aprobada 2026-10-23. **Queda
      superada** por la reaprobación inferior una vez reescrito §9 contra la
      enmienda 2.
- [x] **Aprobación de las tareas T16–T25 de `task.md` en su versión previa**
      — aprobada 2026-10-23. **Queda superada** por la reaprobación de las
      tareas redefinidas (T21–T27).
- [x] Enmienda de la spec 010 con RF-8..RF-10 — **cumplida 2026-10-23**
      (commit `1b63e5a`, aprobada por la usuaria).
- [x] **Enmienda 2 de la spec 010 (RF-8 ajustado, RF-10 reescrito,
      RF-11..RF-15 nuevos) — APROBADA por la usuaria 2026-10-23.**
- [x] Baseline de la fase 2 verificado — 2026-10-23: `main` **204 PASS /
      0 FAIL**; rama `feature/hu-010-rf8-10` **210 PASS / 0 FAIL** tras
      T18–T20.
- [x] T16–T20 ejecutadas y commiteadas — hasta `223a43c` (constantes,
      `build_cancelled_event()`, `on_appointment_cancelled()` post-commit,
      disparo antes del correo).
- [x] **Reaprobación por la usuaria de este §9 reescrito (F2-D1..F2-D13) y
      de las tareas T21–T27 de `task.md`** (T21 de `task.md`) — **aprobada
      2026-10-23 («Apruebo»)**, junto con la **división de la fase en
      2A (T21–T25) y 2B (T26–T27)** («Divide la fase»); la 2B queda
      pendiente del cierre de la 2A. Recuerda: hasta implementar T22 no
      afirmar que la atomicidad está garantizada por el código (T19/T20
      quedan desalineadas hasta entonces).
- [ ] Implementación T22–T27, tests (**222 PASS / 0 FAIL**), demo e informe
      QA `qa-hu-010-rf8-10.md` con PASS.
- [ ] Aceptación de la usuaria y cierre (commits, push, `MEMORY.md`,
      servidor de revisión).
- [ ] **Pendiente del coordinador (fuera de esta fase)**: anotar en
      `specs/018_cancelar-reprogramar-citas/plan.md` que TC-018-005/007/012
      deberán filtrar por `event_type` (F2-D4); lo mismo aplica a los tests
      futuros de la Spec 017.
