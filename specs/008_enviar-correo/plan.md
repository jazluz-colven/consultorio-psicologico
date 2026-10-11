# Plan 008 — Enviar confirmación por correo electrónico (vía n8n)

> Trazabilidad: **HU-008 → Spec 008 (enmendada 2026-10-10) →
> este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs`.
> Etapa actual: **plan revisado a mecanismo n8n** (2026-10-10). Decisiones de la
> usuaria (2026-10-10): contenido **HTML multipart con la paleta Serenidad
> Natural** (Q1), fallo de entrega **best-effort** (Q2), envío **vía el webhook
> n8n de HU-007** (Q3), registro en **`automation_events`** (Q4), payload con
> **email + nombre del paciente** (Q5/Q7) y **la app compone; n8n transporta**
> (Q6). Spec 008 **enmendada** con estos contratos. Baseline declarado en
> `MEMORY.md` (2026-10-10): **147 PASS / 0 FAIL**; verificar al crear la rama.

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 008: que, cuando una cita sea
registrada correctamente, el sistema envíe al paciente un **correo de
confirmación** (comprobante de la reserva) con fecha, hora, servicio y estado
(RF-2), **asociado a la cita que originó el envío** (RF-4), sin enviar nunca una
confirmación que represente como válida una reserva no registrada (RF-3), con
protección de los datos personales de la comunicación y entrega clara y legible
(RNF).

**Mecanismo (Q3, enmienda de la spec)**: la aplicación emite el evento
estructurado **`appointment.confirmation_email` (v1)** — con el mensaje ya
compuesto (Q6) — al **mismo webhook n8n de HU-007**; n8n transporta el correo.
El SMTP vive en n8n, no en la app (fuera de alcance: envío SMTP propio).

**Base existente (HU-001/002/003/016/004/005/006/007 aceptadas)**:
- `create_booking()` con doble comprobación + `UNIQUE (service, date, time)`
  (HU-004/006) y disparo best-effort de automatización n8n tras el INSERT
  (HU-007, `on_appointment_confirmed()`, nunca propaga).
- HU-007 completa: `automation_events` con `UNIQUE(event_id)`,
  `insert_event`/`mark_*`, `_post_webhook()` (stdlib, timeout 3 s, auth header
  opcional), config `AUTOMATION_WEBHOOK_URL`/`AUTOMATION_TIMEOUT_SECONDS`/
  `AUTOMATION_WEBHOOK_AUTH_HEADER` por variables de entorno.
- Patrón PRG `POST /citas → 303 → /citas/confirmada/<id>`; estado `pending`;
  `STATUS_PENDING_LABEL` = «Pendiente»; `SERVICES_CATALOG[...]["name"]`.
- **Baseline: `python -m pytest -q` → 147 PASS / 0 FAIL** (MEMORY.md,
  2026-10-10; verificar en la rama).

Esta HU **no reescribe lo que funciona**: reserva, disponibilidad, doble
reserva y el evento `appointment.confirmed` de HU-007 quedan intactos (RF-3,
regresión); solo se añade un **segundo evento independiente** con el mensaje del
correo. **Sin cambios de esquema, sin variables de entorno nuevas y sin cambios
en la firma de `create_booking()`** (la config de HU-007 ya es suficiente).

**Fuera de alcance** (spec 008): WhatsApp (Spec 009), cancelación (Spec 010),
campañas/correos masivos, panel de administración de envíos, reintentos
automáticos, envío SMTP propio desde la app, configuración del workflow de n8n
(vive en n8n), dependencias nuevas (constitución #1).

**Impacto documentado en HU-007 (D15)**: con webhook configurado, un
`POST /citas` emite **dos** POST a n8n (uno por evento). Las pruebas de HU-007
que cuentan POSTs a través de `create_booking()` (**TC-007-002 y TC-007-007**)
se adaptan para filtrar por `payload["event_type"] == "appointment.confirmed"`,
sin relajar ninguna garantía (los demás tests de HU-007 no se ven afectados:
verificado — TC-007-004/005/006 asientan sobre el evento confirmed;
TC-007-003/011 usan URL vacía → 0 POST).

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Cita registrada correctamente → confirmación por correo electrónico | §3 `send_confirmation()` tras el INSERT (evento a n8n); §5 D1/D2/D9; §6 TC-008-002/003/015 |
| RF-2 | La confirmación incluye fecha, hora, servicio y estado | §2.2 literales en `message.text`/`message.html`; §3 `build_confirmation_message()`; §5 D6/D7/D10; §6 TC-008-001/013 |
| RF-3 | Sin registro correcto → sin confirmación que represente la reserva como válida | §3 trigger solo post-INSERT + chequeo defensivo; §5 D11; §6 TC-008-004/007/008/009/016 |
| RF-4 | La confirmación se asocia a la cita que originó el envío | §2.1 `event_id` determinista + `UNIQUE(event_id)`; §3 dedup; §5 D3/D4; §6 TC-008-002/006/011 |
| RNF-1 | Protección de los datos personales en la comunicación | §2.2 payload con `to`+`patient_name` (excepción documentada), sin documento/teléfono; §2.4 auth header de HU-007; §5 D8; §6 TC-008-001/010/014 |
| RNF-2 | Entrega de información clara y legible | §2.2 asunto + multipart texto/HTML con fecha legible; §5 D6/D7/D11; §6 TC-008-001 |
| CL-1 | Correo del paciente inválido o ausente | §3 chequeo defensivo → sin envío; validación de HU-004 intacta; §6 TC-008-009/016 |
| CL-2 | Error de envío | §3 mapeo TimeoutError/URLError/no-2xx → `failed`, nunca propaga; §5 D2/D11; §6 TC-008-004/005 |
| CL-3 | Envío duplicado para una misma reserva | §2.1 `UNIQUE(event_id)` determinista; §3 dedup; §5 D3; §6 TC-008-006/011 |
| CL-4 | Datos de la cita incompletos | §3 chequeo previo al envío → `failed`; §6 TC-008-008 |
| Finalización | Tests en verde (incl. errores, dedup y regresión) + demo manual | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-4][CL-1..CL-4][RNF-1][RNF-2]` — Constitución #3: la lógica vive en
`services/`; sin dependencias nuevas (constitución #1: solo stdlib ya usada por
HU-007). **Sin cambios en `config.py` ni en `persistence/`** (se reutilizan los
de HU-007). Solo se muestran los **cambios sobre lo existente**:

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   └── email_content.py           # asunto, etiquetas, pie, HTML (paleta),
│   │                              #   meses/días en español, motivos nuevos    [RF-2][RNF-2]
│   ├── services/
│   │   ├── email_service.py           # build_confirmation_message(),
│   │   │                          #   build_event(), send_confirmation()
│   │   │                          #   (registro + POST vía
│   │   │                          #   automation_service._post_webhook;
│   │   │                          #   nunca propaga excepciones)
│   │   │                          #   [RF-1][RF-2][RF-3][RF-4][CL-1..CL-4]
│   │   ├── automation_service.py      # sin cambios de comportamiento;
│   │   │                          #   _post_webhook reutilizado por referencia
│   │   │                          #   de módulo (D14)                       [RF-1]
│   │   └── appointment_service.py     # create_booking(): 2º disparo tras el
│   │                              #   INSERT (firma INTACTA)                [RF-1][RF-3]
│   └── (config.py y persistence/ SIN CAMBIOS)
├── consultorio/web/appointments.py    # SIN CAMBIOS (la config de HU-007 ya se
│                                   #   inyecta; create_booking no cambia de
│                                   #   firma)                               [RF-1][RF-3]
└── tests/
    ├── expected_content.py          # + literales contractuales del correo     [RF-2]
    ├── test_email_service.py        # unit + integración (nuevo)             [RF-1..RF-4][CL-1..CL-4][RNF]
    ├── test_hu_008.py               # eventos, espejo, stdlib, HTTP,
    │                              #   regresión (nuevo)                      [todos]
    └── test_automation_service.py   # ADAPTACIÓN mínima: TC-007-002/007
                                   #   filtran POSTs por event_type (D15)
                                   #   [regresión]
```

**Sin cambios**: esquema (`appointments`, `automation_events`), repositorios,
`availability.js`, plantillas, CSS, `base.html` (sin UI: no hay copy visible en
el sitio).

Responsabilidades (solo módulos tocados):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/email_content.py` | Constantes: asunto, etiquetas, pie, plantilla HTML (paleta), motivos | Contener lógica o acceder a la BD |
| `services/email_service.py` | Componer subject/text/html; construir el payload; registrar el evento y hacer el POST best-effort; traducir fallos a `failed`; **nunca propagar** | Cambiar el evento de HU-007, gestionar HTTP de la app, contener credenciales |
| `services/appointment_service.py` | Tras el INSERT, invocar `send_confirmation()` además de `on_appointment_confirmed()` | Bloquear o condicionar la reserva; cambiar su firma |
| `web/appointments.py` | — (sin cambios) | — |

---

## 2. Literales, modelo de datos y configuración

`[RF-2][RF-4][RNF-1][RNF-2][CL-3]` — **Sin cambios de esquema (§2.1)** y con
los literales de §2.2 **fijados en la spec 008 enmendada** (textos contractuales).

### 2.1 Modelo de datos — sin cambios (reutiliza `automation_events`)

Las tablas `appointments` y `automation_events` (con `UNIQUE(event_id)`) de
HU-004/HU-007 se reutilizan tal cual; no hay migraciones (Q4, D3):

- `event_id` del correo: **determinista**
  `appointment.confirmation_email:{appointment.id}:v1` → el reproceso choca en
  el INSERT y se descarta **antes** de cualquier POST (RF-4, CL-3).
- `event_type = "appointment.confirmation_email"`, `event_version = 1`;
  `appointment_id` documenta el vínculo con la cita (RF-4).
- Estados `pending` → `sent` | `skipped` | `failed` + `detail` en español
  (constitución #6). El evento `appointment.confirmed` de HU-007 coexiste: una
  reserva con webhook configurado genera **dos** filas con `event_id`s distintos.

### 2.2 Literales y plantilla (`content/email_content.py`)

> Contractuales (spec enmendada §«Contenido del mensaje», Q1); espejo en
> `tests/expected_content.py`. Estado reutilizado: `STATUS_PENDING_LABEL`
> («Pendiente», HU-004). Nombre del servicio: `SERVICES_CATALOG[id]["name"]`.

```python
# Asunto y remitente
EMAIL_SUBJECT_TEMPLATE: str = "Confirmación de tu cita — {service_name} · {date_label} · {time}"
EMAIL_SENDER_NAME: str = "Carolina Gómez"

# Cuerpo (parte texto plano; la parte HTML usa las mismas etiquetas)
EMAIL_BODY_HEADER: str = "Tu cita ha sido registrada. Estos son los datos de la reserva:"
EMAIL_LABEL_SERVICE: str = "Servicio"
EMAIL_LABEL_DATE: str = "Fecha"
EMAIL_LABEL_TIME: str = "Hora"
EMAIL_LABEL_STATUS: str = "Estado"
EMAIL_LABEL_REFERENCE: str = "Referencia de la reserva"
EMAIL_FOOTER: str = ("Guarda este correo como comprobante de tu reserva. "
                     "Si necesitas modificar o cancelar tu cita, "
                     "contáctate con el consultorio.")

# Plantilla HTML (constante con {placeholders}; estilos inline, sin CSS externo)
EMAIL_HTML_TEMPLATE: str = "…"   # §2.2.1

# Fechas legibles en español (RNF-2)
WEEKDAYS_ES: tuple[str, ...] = ("lunes", "martes", …)
MONTHS_ES: tuple[str, ...] = ("enero", "febrero", …)

# Motivos nuevos (español; D4)
MSG_APPOINTMENT_INCOMPLETE: str = "Datos de la cita incompletos."
DETAIL_EMAIL_NOT_CONFIGURED: str = "Envío de correo no configurado."
DETAIL_INVALID_RECIPIENT: str = "Dirección de correo del paciente ausente o no válida."
# Reutilizados de content/automation_content.py (mismo canal, mismo copy ya
# aceptado): DETAIL_TIMEOUT, DETAIL_UNAVAILABLE, DETAIL_UNEXPECTED,
# DETAIL_INVALID_RESPONSE_TEMPLATE
```

Fecha legible (RNF-2): `WEEKDAYS_ES[weekday] + ", " + day + " de " +
MONTHS_ES[month-1] + " de " + year` → «martes, 15 de octubre de 2026».

#### 2.2.1 Plantilla HTML (Q1: paleta Serenidad Natural)

- **Multipart** (campo `message` del payload): parte `text/plain` (mismos
  campos) + parte `text/html` — legible en cualquier cliente (RNF-2).
- HTML con **estilos inline** (los clientes de correo no aplican hojas
  externas); **solo los 6 hex de la paleta** (AGENTS.md):
  fondo `#F7F3EA`, banda de cabecera `#B8D8CE` con texto `#30454B`, etiquetas en
  `#30454B`, acento `#D99A7A` como línea/borde de la tarjeta de datos, apoyo
  `#E8D5B5` en el bloque de referencia; tipografía del sistema
  (`Segoe UI, Helvetica, Arial, sans-serif`) — no se embeben fuentes externas.
- **Sin `<img>`, sin CSS externo, sin recursos remotos** (entregabilidad,
  privacidad, constitución #1): el nombre del consultorio es texto en la banda.
- Estructura: cabecera «Carolina Gómez» → saludo «Hola {patient_name}:» →
  `EMAIL_BODY_HEADER` → tarjeta con Servicio / Fecha / Hora / Estado
  («Pendiente») / Referencia `#{id}` → `EMAIL_FOOTER`.

### 2.3 Estados e incidencias (RF-3, CL-2)

| Situación | `status` | `detail` (español) | RF/CL |
|---|---|---|---|
| Evento registrado, a punto de enviarse | `pending` | `NULL` | RF-1 |
| HTTP 2xx del webhook | `sent` | `NULL` + `sent_at` | RF-1 |
| Webhook no configurado (URL vacía) | `skipped` | `Envío de correo no configurado.` (`DETAIL_EMAIL_NOT_CONFIGURED`) | RF-1, RF-3 |
| Cita con datos incompletos | `failed` | `Datos de la cita incompletos.` | RF-3, CL-4 |
| Email del paciente ausente/inválido (defensivo) | `failed` | `Dirección de correo del paciente ausente o no válida.` | CL-1, RF-3 |
| Timeout | `failed` | `Tiempo de espera agotado (timeout).` (reusa `automation_content.DETAIL_TIMEOUT`) | CL-2 |
| `URLError` / conexión rechazada | `failed` | `Servicio de automatización no disponible.` (reusa `DETAIL_UNAVAILABLE`) | CL-2 |
| Respuesta no-2xx | `failed` | `Respuesta no válida del servicio (HTTP {code}).` (reusa `DETAIL_INVALID_RESPONSE_TEMPLATE`) | CL-2 |
| Otra excepción | `failed` | `Error inesperado durante la automatización.` (reusa `DETAIL_UNEXPECTED`) | RF-3, CL-2 |

Ningún `failed` invalida la cita (RF-3, Q2). Sin reintento automático: la
re-ejecución la decide el administrador y el `UNIQUE(event_id)` impide el
duplicado (CL-3).

### 2.4 Configuración (RF-1, RF-3, RNF-1) — **sin variables nuevas**

| Variable (env, heredada de HU-007) | Uso en HU-008 |
|---|---|
| `AUTOMATION_WEBHOOK_URL` | Mismo webhook (Q3); **vacía = evento `skipped`** «Envío de correo no configurado.»; el sistema opera igual |
| `AUTOMATION_TIMEOUT_SECONDS` | Mismo timeout del POST (3.0 s por defecto) |
| `AUTOMATION_WEBHOOK_AUTH_HEADER` | Misma cabecera opcional (enmienda 2 HU-007); el token es secreto de entorno, nunca en repo/docs/tests |

`create_booking()` **no cambia de firma**: ya recibe url/timeout/auth de
automatización; el servicio de correo reutiliza esos mismos valores (D9).

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-4][CL-1..CL-4][RNF-1][RNF-2]`

```text
# --- services/email_service.py -----------------------------------------
EVENT_TYPE: str = "appointment.confirmation_email"      # [RF-4]
EVENT_VERSION: int = 1

FUNCTION _format_spanish_date(iso) -> str:              # «martes, 15 de
    # WEEKDAYS_ES/MONTHS_ES de email_content            #  octubre de 2026»
    RETURN str                                          [RF-2][RNF-2]

FUNCTION build_confirmation_message(appointment) -> dict[str, str]:
    service_name = SERVICES_CATALOG[appointment.service]["name"]
    date_label = _format_spanish_date(appointment.date)
    fields = {service_name, date_label, appointment.time,
              STATUS_PENDING_LABEL, appointment.id}       [RF-2]
    text = EMAIL_* + campos de §2.2 (texto plano)
    html = EMAIL_HTML_TEMPLATE.format(...)                # paleta, inline,
                                                          # sin recursos remotos
    RETURN {"subject": EMAIL_SUBJECT_TEMPLATE.format(...),
            "text": text, "html": html}                   [RF-2][RNF-2]

FUNCTION build_event(appointment) -> dict:                # allowlist de la spec
    message = build_confirmation_message(appointment)
    RETURN {                                              [RF-2][RF-4][RNF-1]
        "event_id": f"{EVENT_TYPE}:{appointment.id}:v{EVENT_VERSION}",
        "event_type": EVENT_TYPE, "event_version": EVENT_VERSION,
        "occurred_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "recipient": {"to": appointment.email,
                      "patient_name": appointment.patient_name},
        "message": message,
        "appointment": {"id": …, "service": …, "date": …, "time": …,
                        "status": appointment.status}}

FUNCTION send_confirmation(appointment, db, url, timeout, auth_header="") -> None:
    TRY:                                                  # nunca propaga
        IF appointment MISSING campos (id, email, service, date, time):
            IF appointment.id: insert_event(...) + mark_failed(
                MSG_APPOINTMENT_INCOMPLETE); RETURN      [RF-3][CL-4]
        IF appointment.email EMPTY O inválida:           # defensivo post-INSERT
            insert_event(...) + mark_failed(DETAIL_INVALID_RECIPIENT); RETURN
                                                          [CL-1][RF-3]
        event = build_event(appointment)
        IF NOT events_repository.insert_event(           # UNIQUE(event_id)
                event_id, EVENT_TYPE, EVENT_VERSION, appointment.id, db):
            RETURN                                 # ya gestionada [RF-4][CL-3]
        IF NOT url:
            mark_skipped(event_id, DETAIL_EMAIL_NOT_CONFIGURED, db); RETURN
                                                          [RF-1][RF-3]
        TRY:
            status_code = automation_service._post_webhook(   # por referencia
                url, event, timeout, auth_header)             # de módulo [D14]
        CATCH TimeoutError:
            mark_failed(event_id, DETAIL_TIMEOUT, db); RETURN       [CL-2]
        CATCH urllib.error.URLError:
            mark_failed(event_id, DETAIL_UNAVAILABLE, db); RETURN   [CL-2]
        CATCH Exception:
            mark_failed(event_id, DETAIL_UNEXPECTED, db); RETURN
        IF 200 <= status_code < 300:
            mark_sent(event_id, db)                      [RF-1][RF-4]
        ELSE:
            mark_failed(event_id, DETAIL_INVALID_RESPONSE…, db)    [CL-2]
    CATCH Exception:
        RETURN   # jamás invalida la reserva             [RF-3][Q2]

# --- services/appointment_service.py (firma INTACTA) ------------------
FUNCTION create_booking(data, db, automation_url="", automation_timeout=3.0,
                        automation_auth_header=""):
    # … resto sin cambios (HU-004/006/007) …
    automation_service.on_appointment_confirmed(…)        # intacto (HU-007)
    email_service.send_confirmation(                      # nuevo [RF-1][RF-3]
        appointment, db, automation_url, automation_timeout,
        automation_auth_header)
    RETURN appointment
# web/appointments.py: SIN CAMBIOS
```

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor (BD existente) | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `python -m pytest -q` | Suite completa (147 previos + 16 nuevos = 163) | `163 passed` | `0` / `1` |
| `python -m pytest tests/test_hu_008.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-3]` — **sin cambios de endpoints**

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `POST` | `/citas` (válido y libre) | redirige a la confirmación; 1 fila en `appointments` +, si hay webhook, **2 eventos** en `automation_events` (`appointment.confirmed` y `appointment.confirmation_email`) | **303** → **200** |
| resto de rutas | sin cambios | como hasta ahora | 200/303/400/404/405 |

**Contrato semántico (lo que verifican los tests):**

```text
[RF-1] POST /citas válido con webhook → evento confirmation_email 'sent'
       y 1 POST cuyo payload es el contrato de la spec   → absent ⇒ FAIL
[RF-2] message.text y message.html contienen servicio, fecha legible,
       hora, «Pendiente» y #{id}; HTML ⊆ paleta de 6 hex, sin remoto
                                                             → absent ⇒ FAIL
[RF-3] validación con error / SLOT_TAKEN / webhook caído → 0 correos que
       representen la reserva; 303 intacto tras INSERT correcto
                                                             → absent ⇒ FAIL
[RF-4] reproceso → 1 evento confirmation_email y 1 POST (UNIQUE event_id)
                                                             → absent ⇒ FAIL
[regresión] 147 previos intactos (TC-007-002/007 adaptados por D15,
       sin relajar garantías)                                → present ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Envío vía evento `appointment.confirmation_email` al mismo webhook n8n de HU-007** (Q3) | Reutiliza transporte, auth header, timeout y workflow ya operativos y probados en vivo (HU-007); la app no necesita SMTP ni secrets nuevos; la spec 007 permanece intacta (evento propio) | *SMTP stdlib en la app*: duplica transporte y exige `SMTP_*` + credenciales en la app (decisión previa, descartada por la usuaria). *Webhook nuevo y separado*: más config y credenciales sin ganancia | RF-1 |
| D2 | **Síncrono best-effort tras el INSERT, 1 intento, sin reintentos** (Q2) | Mismo razonamiento D3/D6 plan 007: el INSERT ya está commitado; el 303 no depende del evento; determinista y testeable | *Reintentos con backoff*: alcance extra sin requisito | RF-1, RF-3, CL-2 |
| D3 | **Reutilizar `automation_events` con `event_id` determinista `appointment.confirmation_email:{id}:v1`** (Q4) | RF-4 + constitución #5: dedup en el punto de persistencia; trazabilidad `pending/sent/skipped/failed` ya aceptada; sin tablas nuevas ni migraciones | *Tabla `confirmation_emails`*: duplica registro (decisión previa, descartada). *Sin registro*: sin garantía de persistencia ni diagnóstico | RF-4, CL-3 |
| D4 | **Estados y motivos reutilizados de HU-007**; solo `DETAIL_EMAIL_NOT_CONFIGURED` es nuevo («Envío de correo no configurado.») | Mismo canal y mismo copy ya aceptado; distingue «no configurado» (`skipped`) de un error real | *Copys nuevos paralelos*: duplicidad textual sin necesidad | RF-1, RF-3, CL-2 |
| D5 | **La app compone el mensaje (subject/text/html) y lo envía en el payload; n8n solo transporta** (Q6) | El copy queda en el repo, es contractual (spec + espejo) y testeable con pytest (constitución #4); el workflow de n8n es trivial (nodo de email) | *n8n compone la plantilla*: copy fuera del repo, sin tests ni trazabilidad spec→test | RF-2, RNF-2 |
| D6 | **Multipart texto + HTML con paleta Serenidad Natural, estilos inline, sin recursos remotos** (Q1) | Elección de la usuaria; parte texto garantiza legibilidad en cualquier cliente; paleta = restricción (AGENTS.md) | *Solo texto*: incumple Q1. *CSS externo/remoto*: los clientes lo descartan | RF-2, RNF-2 |
| D7 | **Fecha en español legible** (`WEEKDAYS_ES`/`MONTHS_ES`) | RNF-2: «martes, 15 de octubre de 2026» se entiende mejor que el ISO | *Fecha ISO*: menos legible. *Locale del sistema*: variable según máquina | RF-2, RNF-2 |
| D8 | **Payload con PII mínima: `recipient.to` + `patient_name`** (Q7); sin `document_type`/`document_number`/`phone`; auth header heredado de HU-007 | El correo no puede llegar sin destinatario ni saludo; es excepción **documentada en la spec 008** a la minimización de HU-007, y no toca el evento `appointment.confirmed` (que sigue sin PII) | *Payload solo datos y plantilla en n8n*: descartado en Q6. *Incluir documento/teléfono*: excede lo necesario | RF-2, RNF-1 |
| D9 | **Sin variables de entorno nuevas**: reutiliza `AUTOMATION_WEBHOOK_URL`/`_TIMEOUT_SECONDS`/`_WEBHOOK_AUTH_HEADER` y la firma intacta de `create_booking()` | Q3 (mismo webhook); cero config nueva; el sitio sigue operando sin webhook (evento `skipped`) | *`CONFIRMATION_EMAIL_WEBHOOK_URL`*: duplica config/secretos sin ganancia. *`SMTP_*`*: ya no aplica | RF-1, RF-3 |
| D10 | **Literales contractuales en `email_content.py` + espejo en `expected_content.py`** (junto con la enmienda) | AGENTS.md «Textos contractuales»; trazabilidad spec → test | *Copy hardcodeado en el servicio*: rompe el espejo | RF-2 |
| D11 | **El correo jamás invalida la reserva** (try/except completo, trigger solo tras INSERT correcto) (Q2) | RF-3 y lección D6 plan 007: un fallo del webhook no puede tumbar la reserva ni el 303 | *Condicionar la reserva al correo*: reescribe el PRG. *Dejar propagar*: 500 sobre reserva creada | RF-1, RF-3, CL-2 |
| D12 | **Rama `feature/hu-008` desde `main`** (baseline 147) | AGENTS.md: aislamiento de HU por rama; `main` limpia | *Rama desde otra feature*: arrastra pendientes | regresión |
| D13 | **Identificadores en inglés; literales y `detail` en español**; sin UI ni copy visible en el sitio | Constitución #6 | *Copy en inglés en el correo*: rompe la constitución | todos |
| D14 | **Reutilizar `automation_service._post_webhook` por referencia de módulo** (`automation_service._post_webhook(…)`); tests deterministas parcheando ese único punto; demo con **receptor local stdlib efímero** (JSON, sin TLS) y prueba live opcional con la n8n de la usuaria | Un solo punto de parcheo: los parches existentes de HU-007 cubren ambos eventos (hermeticidad); misma estrategia de demo/pytest-qa que HU-007 | *Import del nombre (`from … import _post_webhook`)*: rompe los parches existentes y dejaría POSTs reales en tests. *Copia de `_post_webhook` en email_service*: duplicación y doble punto de parcheo. *Proveedor real en los tests*: frágil y con secretos | RF-1, CL-2 |
| D15 | **Adaptación de TC-007-002 y TC-007-007** (verificado en código): cuentan `post.call_count` sobre `create_booking()`; con el segundo evento habrá 2 POST → se filtra por `payload["event_type"] == "appointment.confirmed"` | La adaptación es consecuencia de un comportamiento **nuevo especificado** (dos eventos independientes por reserva); no relaja ninguna garantía de HU-007 (1 evento confirmed + 1 POST por tipo, dedup intacto). TC-007-003/004/005/006/011/014 no se ven afectados (verificado) | *Contar 1 POST total*: sería falso con dos eventos. *No emitir el evento cuando hay webhook*: contradice RF-1 | RF-1, regresión |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` · `python -m pytest tests/test_hu_008.py -v`.
Fixtures de `conftest.py` sin cambios. Punto de parcheo único:
`automation_service._post_webhook` (D14). Sin red real, sin `sleep`, BD temporal,
fechas relativas.

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-008-001 | `test_email_service.py` | `build_confirmation_message()` → `subject`/`text`/`html` que contienen servicio (nombre visible), fecha legible en español, hora, «Pendiente» y `#{id}`; HTML solo con los **6 hex** de la paleta, sin `<img>`/CSS externo/remoto; sin documento ni teléfono | RF-2, RNF-1, RNF-2 |
| TC-008-002 | `test_email_service.py` | `create_booking()` con webhook y `_post_webhook` parcheado (200) → 1 fila + evento `appointment.confirmation_email` `sent` con `sent_at` + **1 POST** de ese `event_type` con `recipient.to` = email de la cita, `recipient.patient_name`, `message` completo y `appointment.id` | RF-1, RF-4 |
| TC-008-003 | `test_email_service.py` | **No configurado:** sin URL → reserva OK + evento `skipped` («Envío de correo no configurado.») + **0 POST** | RF-1, RF-3 |
| TC-008-004 | `test_email_service.py` | **CL-2:** `URLError` → evento `failed` «Servicio de automatización no disponible.», **0 excepción**, cita intacta | RF-3, CL-2 |
| TC-008-005 | `test_email_service.py` | **CL-2:** `TimeoutError` → evento `failed` «Tiempo de espera agotado (timeout).» y cita intacta | CL-2 |
| TC-008-006 | `test_email_service.py` | **CL-3:** segunda llamada de `send_confirmation()` con la misma cita → **1 evento** (UNIQUE) y **1 POST** acumulado del tipo | RF-4, CL-3 |
| TC-008-007 | `test_email_service.py` | **Aislamiento:** repositorio de eventos parcheado con `RuntimeError` → `create_booking()` **devuelve la `Appointment`** y el 303 no se ve afectado | RF-3, CL-2 |
| TC-008-008 | `test_email_service.py` | **CL-4:** `Appointment` con campos vacíos → **0 POST** y evento `failed` «Datos de la cita incompletos.» | RF-3, CL-4 |
| TC-008-009 | `test_email_service.py` | **CL-1:** `appointment.email` vacía o sin `@` (defensivo) → **0 POST** y evento `failed` «Dirección de correo del paciente ausente o no válida.» | CL-1, RF-3 |
| TC-008-010 | `test_email_service.py` | **Allowlist del payload:** `event_id` determinista `appointment.confirmation_email:{id}:v1`, `event_version=1`; con `recipient`/`message`; **sin** `document_type`/`document_number`/`phone` (raíz y `appointment`) | RF-4, RNF-1 |
| TC-008-011 | `test_hu_008.py` | **Registro:** tras flujo completo con webhook, `automation_events` tiene **2 filas** (`appointment.confirmed` + `appointment.confirmation_email`), `COUNT(*)=1` por `event_id` y `appointment_id` enlaza la cita | RF-4, CL-3 |
| TC-008-012 | `test_hu_008.py` | **Config:** sin variables `SMTP_*` nuevas; `AUTOMATION_WEBHOOK_URL=""`, `AUTOMATION_TIMEOUT_SECONDS=3.0` y `AUTOMATION_WEBHOOK_AUTH_HEADER=""` por defecto intactos | RF-1, RF-3 |
| TC-008-013 | `test_hu_008.py` | **Espejo:** `expected_content` == `email_content` (asunto, etiquetas, pie, motivos); `STATUS_PENDING_LABEL` = «Pendiente» | RF-2 |
| TC-008-014 | `test_hu_008.py` | **Constitución #1:** inspección estática de `email_service.py` → sin `smtplib` ni imports de terceros; usa stdlib y `automation_service` | todos, D1 |
| TC-008-015 | `test_hu_008.py` | **HTTP end-to-end:** `POST /citas` con webhook de prueba → **303** → `/citas/confirmada/<id>` **200** + evento `confirmation_email` `sent` | RF-1, RF-4 |
| TC-008-016 | `test_hu_008.py` | **Regresión funcional HU-004/005/006/007** (incluye TC-007-002/007 ya adaptados por D15): validación, horarios, disponibilidad, doble reserva, evento `appointment.confirmed` y evento de correo **idénticos** a su contrato; email inválido → 200 de validación y 0 eventos de correo | RF-3, CL-1, regresión |
| TC-008-017 | `test_hu_008.py` | **Regresión total:** `python -m pytest -q` → **0 FAIL** con los **147 previos** intactos (tras la adaptación D15) | todos, finalización |

> **Nota de recuento**: TC-008-017 es la corrida de la suite; las funciones
> nuevas son **16** → total esperado **163** (147 + 16). **0 FAIL con los 147
> previos intactos** es la condición real de cierre.

### 6.2 Pirámide

1. **Unitarias** — `build_confirmation_message()` (asunto, partes, paleta, sin
   remotos, sin PII extra) y allowlist de `build_event()` sin Flask.
   `[RF-2][RF-4][RNF-1][RNF-2]`
2. **Integración de servicio** — `create_booking()` + `send_confirmation()` con
   `_post_webhook` parcheado: 2xx→`sent`, sin URL→`skipped`,
   `URLError`/`TimeoutError`/no-2xx→`failed`, duplicados→1 POST, aislamiento.
   `[RF-1][RF-3][RF-4][CL-1..CL-4]`
3. **Regresión** — suite completa: 147 previos verdes (TC-007-002/007 adaptados
   por D15 sin relajar garantías). `[todos]`
4. **Demo manual** — `python app.py` + **receptor local stdlib efímero** (JSON
   sobre el webhook) y `AUTOMATION_WEBHOOK_URL` apuntando a él: (a) reservar en
   `/citas` → 303/200 y el receptor captura **2 POST** (`appointment.confirmed`
   y `appointment.confirmation_email` con subject/text/html de §2.2); (b) ambos
   eventos `sent`; (c) receptor apagado → reserva intacta + eventos `failed`
   con su motivo; (d) reproceso → **sin POST adicionales**. **Demo live (si la
   usuaria lo indica)**: con el workflow de n8n de HU-007 ampliado con un nodo
   de email que enruta por `event_type` (contrato de integración de la spec) →
   correo real recibido en su bandeja (auth header y SMTP en n8n, fuera del
   repo). Sin cambios visuales → sin capturas 1280/375.
   `[RF-1][RF-2][RF-3][RF-4][CL-2][RNF-2]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar (pytest-qa §1.2); la
  adaptación D15 es un **filtro por `event_type`**, no una relajación.
- Pruebas deterministas: `_post_webhook` parcheado, sin red real, sin `sleep`,
  BD temporal, fechas relativas.

```text
HU: HU-008
Caso: TC-008-002
Comando: python -m pytest tests/test_email_service.py -v
Resultado: PASS
Rama: feature/hu-008
Commit: <hash>
Evidencia: payload del evento confirmation_email capturado + dump de automation_events (demo §6.2)
```

- Informe QA: `docs/evidencias/hu-008/qa-hu-008.md` con PASS/FAIL por TC y
  checkbox de aceptación (skill `pytest-qa`).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Contenido y formato del mensaje (duda de la spec) | **Multipart texto + HTML con paleta Serenidad Natural, estilos inline, fecha legible en español, Referencia `#{id}`**; la app compone (§2.2/§2.2.1, D5/D6/D7/D10). Fijado en la enmienda. |
| Q2 | Fallo de entrega (duda de la spec) | **Best-effort: evento `failed` con motivo, reserva intacta, sin reintentos** (§2.3, D2/D11). Fijado en la enmienda. |
| Q3 | Mecanismo de envío | **Evento `appointment.confirmation_email` al mismo webhook n8n de HU-007; SMTP en n8n, no en la app** (D1/D9). Respondida 2026-10-10. |
| Q4 | Registro y deduplicación | **Reutilizar `automation_events` con `event_id` determinista y `UNIQUE`** (D3/D4). Respondida 2026-10-10. |
| Q5 | Rama de trabajo | **`feature/hu-008` desde `main`** (D12). |
| Q6 | Quién compone el correo | **La app compone subject/text/html; n8n solo transporta** (D5). Respondida 2026-10-10. |
| Q7 | PII en el payload | **`recipient.to` + `patient_name`** (excepción documentada en la spec 008; spec 007 intacta); sin documento/teléfono (D8). Respondida 2026-10-10. |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Aprobación de este `plan.md` revisado (alcance, matriz RF, D1–D15, §2–§3)
      por la usuaria — **aprobado 2026-10-10 («Confirmo»)**.
- [x] **Escritura de la spec 008 enmendada** («Contratos fijados»: mecanismo
      n8n, payload, contenido, fallo de entrega, contrato de integración) —
      petición explícita de la usuaria («Modifiquemos la spec») —
      **2026-10-10**.
- [x] Creación de `feature/hu-008` desde `main` (Q5) y verificación del baseline
      **147 PASS / 0 FAIL**.
- [x] Espejo + `email_content.py` + `email_service.py` + disparo en
      `create_booking()` con commits por fase.
- [x] Adaptación D15 de TC-007-002/TC-007-007 (filtro por `event_type`) y tests
      §6 en verde: **163 PASS / 0 FAIL**.
- [x] Demo manual §6.2 (+ live n8n si la usuaria lo indica) + evidencia en
      `docs/evidencias/hu-008/`.
- [x] Informe QA `qa-hu-008.md` con PASS/FAIL por TC y checkbox de aceptación.
- [x] Commit/Push por fases, `MEMORY.md` y aceptación de la HU.
- [x] Servidor de revisión en marcha (AGENTS.md) y URL comunicada.

---

## 8. Secuencia de implementación

0. **Git**: verificar `main` limpia y baseline 147 PASS; crear **`feature/hu-008`
   desde `main`** (Q5) — solo tras aprobar este plan.
1. **Spec primero**: escritura de la spec 008 enmendada (bloqueante) —
   **cumplida 2026-10-10**.
2. **Plan**: este `plan.md` revisado (aprobado por la usuaria 2026-10-10).
3. **Espejo**: `tests/expected_content.py` con los literales del correo.
4. **Contenido**: `email_content.py` (§2.2/§2.2.1, motivos, reutilizando
   `automation_content` donde aplica).
5. **Servicio**: `email_service.py` (§3, D14) → `test_email_service.py`
   (TC-008-001…010).
6. **Disparo**: `create_booking()` con el 2º disparo (firma intacta).
7. **Adaptación D15**: TC-007-002/TC-007-007 con filtro por `event_type` →
   verificación de HU-007 en verde.
8. **Tests de HU**: `test_hu_008.py` (TC-008-011…016).
9. **Suite completa**: → **163 PASS / 0 FAIL** con los 147 previos intactos
   (TC-008-017).
10. **Evidencia**: demo §6.2 (+ live n8n opcional) → `docs/evidencias/hu-008/` +
    `qa-hu-008.md`.
11. **Cierre**: commits por fase, push, `MEMORY.md`, aceptación y servidor de
    revisión en marcha.
