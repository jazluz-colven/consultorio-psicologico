# Plan 004 — Agendar una cita

> Trazabilidad: **HU-004 → Spec 004 (`specs/004_agendar-cita/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs` (Q5).
> Etapa actual: **PLAN APROBADO + LITERALES Q9 APROBADOS** (2026-10-09): alcance,
> decisiones Q1–Q9 y catálogo de horas (30 min, 08:00–12:00 / 14:00–17:00 como horas
> de fin, solo lunes–viernes) aprobados por la usuaria. **Implementación autorizada:**
> fijar literales en la spec 004 (§8.1) y codificar según §1–§6.
> Ramas: **`main` tras integrar `feature/identidad-buscador`** (HU-016 aceptada) y
> **`feature/hu-004`** nacida de `main` (Q6).

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 004: el flujo completo de reserva en
`/citas` — seleccionar un horario disponible, registrar los datos del paciente y
confirmar la reserva — con validación completa, persistencia y página de confirmación.

**Fuera de alcance**: confirmaciones por correo (Spec 008) o WhatsApp (Spec 009),
automatización n8n (Spec 007), cancelación de citas, agenda interna del psicólogo
(Specs 011/012), registro/login de pacientes, concurrencia avanzada y estado «en
curso» del botón (Spec 006), calendario completo de disponibilidad con navegación de
fechas y distinción visual de estados (Spec 005 — ver delimitación en Q10/§7.1).

**Primera persistencia del proyecto**: se crea `consultorio/persistence/` con SQLite de
la librería estándar (Q4). Se activan la constitución #5 (persistencia íntegra) y la
decisión pendiente de `MEMORY.md` («`persistence/` se crea con la primera HU con BD»).
Sin dependencias nuevas: `sqlite3` es stdlib (constitución #1).

**Dudas de la spec resueltas** (2026-10-09, usuaria):
- **Q1 — datos obligatorios**: tipo de documento (CC, TI, CE, Pasaporte, RC), número de
  documento, nombre y apellido, correo electrónico y celular. Se cierran en la spec 004
  en el paso 1 de la secuencia (§8.1).
- **Q2 — estado inicial**: `pending` («Pendiente»).

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Horarios disponibles + datos completos → registra y muestra confirmación | §2 esquema/`BOOKING_HOURS`; §3 `create_booking()`; §4 `POST /citas` → 303 → confirmación; §5 D7/D8/D10; §6 TC-004-005/008/012/015/016/026 |
| RF-2 | Dato obligatorio ausente o inválido → no registra e indica qué corregir | §3 `validate_booking()`; §4 contrato semántico de errores; §5 D6/D11/D12/D13; §6 TC-004-009/010/017/018 |
| RF-3 | Horario deja de estar disponible antes de confirmar → rechaza y pide otro | §3 SELECT previo + UNIQUE (D4/D9); §4 literal RF-3; §5 D4/D7/D9; §6 TC-004-006/013/014/019/021 |
| RF-4 | Cita asociada a paciente, servicio, fecha, hora y estado | §2 tabla `appointments`; §5 D3/D5; §6 TC-004-004/005/007/016 |
| RF-5 | El servicio debe ser ofrecido por el consultorio | §3 validación vs `SERVICES_CATALOG`; §4 `POST` y `GET /citas/horarios`; §5 D… (servicio ∈ catálogo); §6 TC-004-011/020 |
| RNF-1 | Solo los datos necesarios para el flujo | §2 formulario de 8 campos; §5 D6; §6 TC-004-025 |
| RNF-2 | Comprensible y usable en escritorio y móvil | §1 plantillas + `.appointment-*` + `availability.js`; §5 D14; §6 TC-004-024 y evidencia visual |
| CL-1 | Datos obligatorios vacíos | §3 validación por campo; §6 TC-004-009/017 |
| CL-2 | Datos inválidos | §3 formatos y reglas (D12/D13); §6 TC-004-010/018 |
| CL-3 | Horario pasa de disponible a ocupado antes de confirmar | §3 doble comprobación (SELECT + UNIQUE); §6 TC-004-013/014/019 |
| CL-4 | Dos intentos de reserva sobre el mismo horario | §3/§5 D4/D9; §6 TC-004-006/007/014/019 |
| CL-5 | Servicio no válido | §3/§4 validación en POST y en `/citas/horarios`; §6 TC-004-011/020 |
| Finalización | Tests en verde + demo manual | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-5][CL-1..CL-5][RNF-1][RNF-2]` — Constitución #3: contenido, lógica,
persistencia y presentación separadas; la plantilla y el JS no contienen reglas de
negocio. Se conserva la estructura por capas (D1/Q2 del plan 001) y el patrón de
blueprint ya validado en HU-002/003/016.

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   └── appointment_content.py   # BOOKING_HOURS (14 slots), DOCUMENT_TYPES,
│   │                             # BOOKING_PAGE_TITLE, mensajes literal de error/éxito
│   │                             #   [RF-1][RF-2][RF-3][RNF-1]
│   ├── persistence/                 # NUEVO (Q4) — constitución #5
│   │   ├── database.py              # get_connection(), init_db(app): esquema +
│   │   │                         # índice UNIQUE (service, date, time)   [RF-3][RF-4]
│   │   └── appointments_repository.py  # insert_appointment(), get_appointment_by_id(),
│   │                                 # is_slot_taken(), list_available_hours()
│   │                                 #   [RF-1][RF-3][RF-4]
│   ├── services/
│   │   └── appointment_service.py   # validate_booking(), create_booking(),
│   │                             # get_available_hours()  [RF-1..RF-5][CL-1..CL-5]
│   └── web/
│       ├── appointments.py          # blueprint "appointments": GET/POST /citas,
│       │                         # GET /citas/horarios, GET /citas/confirmada/<id>
│       │                         #   [RF-1..RF-5]
│       └── placeholders.py          # retira /citas; conserva /articulos, /contacto
│                                 #   [regresión HU-001/002/003]
├── templates/
│   └── appointments/
│       ├── index.html               # h1 «Agendar cita» + <form> de 8 campos en
│       │                         # 2 columnas (datos del paciente ‖ datepicker
│       │                         # + bloques Mañana/Tarde) + «Volver al inicio»
│       │                         #   [RF-1][RF-2][RF-5][RNF-1][RNF-2][D19]
│       └── confirmation.html        # «Cita registrada» + resumen + estado «Pendiente»
│                                 #   [RF-1][RF-4]
├── static/
│   ├── css/main.css                 # .appointment-* mobile-first; paleta intacta
│   │                             #   [RNF-2]
│   └── js/availability.js           # vanilla: datepicker con días agendables
│                                 # diferenciados + fetch /citas/horarios al
│                                 # cambiar servicio/día y rellena los bloques
│                                 # Mañana/Tarde (D19)  [RF-1][RF-3][RNF-2]
├── consultorio/config.py            # + DATABASE_PATH (data/consultorio.db)
│                                 #   [RF-1][RF-4]
└── tests/
    ├── conftest.py                  # fixture app con BD temporal por test  [todos]
    ├── expected_content.py          # + BOOKING_HOURS, DOCUMENT_TYPES, mensajes
    │                             # (espejo único); PLACEHOLDER_SECTIONS sin /citas
    │                             # (en el paso §8.7)                      [RF-1..RF-5]
    ├── test_appointment_content.py  # catálogo de horas, tipos de documento, espejo
    │                             #   [RF-1][RF-2][RNF-1]
    ├── test_appointment_persistence.py  # esquema, UNIQUE, insert/recuperación
    │                             #   [RF-3][RF-4][CL-4]
    ├── test_appointment_service.py  # validación por campo, disponibilidad, rechazos
    │                             #   [RF-1..RF-5][CL-1..CL-5]
    ├── test_appointment_routes.py   # contrato HTTP + JSON + regresión
    │                             #   [RF-1..RF-5][regresión]
    └── test_hu_004.py               # RNF + E2E + fuera de alcance          [todos]
```

Responsabilidades (sin solaparse):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/appointment_content.py` | Declarar horas, tipos de documento y literales de mensajes | Contener lógica ni acceder a la BD |
| `persistence/database.py` | Conexión, `init_db()`, esquema e índice UNIQUE | Validar datos de negocio ni generar HTML |
| `persistence/appointments_repository.py` | Insertar/recuperar citas y leer horas ocupadas | Decidir reglas de validación ni manejar request/response |
| `services/appointment_service.py` | Validar, comprobar disponibilidad, orquestar el registro | Escribir HTML, manejar status codes |
| `web/appointments.py` | Método/ruta, status codes, parseo del form, `render_template`/`jsonify`/`redirect` | Contener reglas de validación ni consultar la BD directamente |
| `templates/appointments/*` | Marco semántico del formulario y de la confirmación | Condicionales de negocio |
| `static/js/availability.js` | Refrescar el `<select>` de horas vía `fetch` | Validar datos ni registrar la cita (doble comprobación en el servidor) |

`create_app()` registra `appointments_bp` junto a `about_bp`, `home_bp`, `sections_bp`,
`search_bp` y `services_bp`, y ejecuta `init_db(app)`. `base.html` y `nav.js` no
cambian: la navegación se sirve desde `get_home_view()` (el enlace «Agendar cita» →
`/citas` ya existe en `NAV_LINKS`).

---

## 2. Modelo de datos, catálogo de horas y literales

`[RF-1][RF-3][RF-4][RNF-1]` — Esquema versionado en el repositorio (las migraciones y
su estrategia se documentan aquí antes de tocar tablas; AGENTS.md).

### 2.1 Esquema (`persistence/database.py`)

```sql
CREATE TABLE IF NOT EXISTS appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type   TEXT NOT NULL,   -- CC | TI | CE | PASSPORT | RC
    document_number TEXT NOT NULL,
    patient_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    service         TEXT NOT NULL,   -- clave de SERVICES_CATALOG
    date            TEXT NOT NULL,   -- ISO YYYY-MM-DD
    time            TEXT NOT NULL,   -- HH:MM
    status          TEXT NOT NULL DEFAULT 'pending',  -- «Pendiente» (Q2)
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (service, date, time)     -- integridad en el punto de persistencia (D4)
);
```

- **Una sola tabla** con los datos del paciente (D3): RF-4 asocia la cita al paciente
  almacenando su identificación; ninguna spec pide una entidad `patients`
  reutilizable (constitución #1).
- **Unicidad por `service + date + time`** desde HU-004 (Q5), coherente con Spec 006
  RF-2 («la misma combinación de servicio, fecha y hora»); la Spec 005 plantea esa
  misma regla en sus dudas abiertas.
- `data/consultorio.db` fuera de git (`.gitignore`); tests con BD temporal por fixture.

### 2.2 `consultorio/content/appointment_content.py`

```python
BOOKING_PAGE_TITLE = "Agendar cita"          # h1 literal (etiqueta de NAV_LINKS)

BOOKING_HOURS: list[str] = [                 # aprobado 2026-10-09 (Q7): bloques de
    # mañana, fin de bloque a las 12:00       30 min; 12:00–14:00 libre (almuerzo)
    "08:00", "08:30", "09:00", "09:30",
    "10:00", "10:30", "11:00", "11:30",
    # tarde, fin de bloque a las 17:00
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30",
]                                           # 14 slots exactos

DOCUMENT_TYPES: list[tuple[str, str]] = [    # aprobado 2026-10-09 (Q1)
    ("CC",        "Cédula de ciudadanía"),
    ("TI",        "Tarjeta de identidad"),
    ("CE",        "Cédula de extranjería"),
    ("PASSPORT",  "Pasaporte"),
    ("RC",        "Registro civil"),
]

# Literales de mensaje (propuestos — Q9, se fijan en la spec antes de codificar)
MSG_REQUIRED_SERVICE   = "Selecciona un servicio."
MSG_INVALID_SERVICE    = "Selecciona un servicio válido."
MSG_REQUIRED_DATE      = "Selecciona una fecha."
MSG_INVALID_DATE       = "Selecciona una fecha válida de lunes a viernes, no anterior a hoy."
MSG_REQUIRED_TIME      = "Selecciona una hora."
MSG_INVALID_TIME       = "Selecciona una hora válida."
MSG_REQUIRED_DOC_TYPE  = "Selecciona un tipo de documento."
MSG_REQUIRED_DOC_NUMBER = "Ingresa el número de documento."
MSG_INVALID_DOC_NUMBER = "El número de documento debe tener entre 4 y 20 dígitos."
MSG_REQUIRED_NAME      = "Ingresa tu nombre y apellidos."
MSG_INVALID_NAME       = "El nombre debe tener entre 3 y 120 caracteres."
MSG_REQUIRED_EMAIL     = "Ingresa tu correo electrónico."
MSG_INVALID_EMAIL      = "Ingresa un correo electrónico válido."
MSG_REQUIRED_PHONE     = "Ingresa tu celular."
MSG_INVALID_PHONE      = "Ingresa un celular válido (entre 7 y 15 dígitos)."
MSG_SLOT_TAKEN         = "Ese horario ya no está disponible. Selecciona otro horario."   # RF-3
MSG_NO_HOURS           = "No hay horarios disponibles para esta fecha."                  # base Spec 005 RF-4
MSG_INVALID_PARAMS     = "Parámetros inválidos."                    # GET /citas/horarios 400
BOOKING_BLOCK_MORNING  = "Mañana"                  # bloque 08:00–11:30 (D19)
BOOKING_BLOCK_AFTERNOON = "Tarde"                  # bloque 14:00–16:30 (D19)
MSG_SELECT_DATE_HINT   = "Selecciona una fecha para ver las horas disponibles."
CONFIRMATION_TITLE     = "Cita registrada"
STATUS_PENDING_LABEL   = "Pendiente"         # etiqueta en español de status="pending"
BOOKING_HELPER         = ("Si el paciente es menor de edad, registra los datos del "
                          "representante con su documento; si es extranjero, puede usar "
                          "pasaporte o cédula de extranjería.")
```

### 2.3 Reglas de negocio (base de validación)

| Campo (`name` en el form) | Regla |
|---|---|
| `service` | Obligatorio; clave de `SERVICES_CATALOG` (RF-5) |
| `date` | Obligatorio; ISO `YYYY-MM-DD`; fecha válida de calendario; **≥ hoy** y **de lunes a viernes** (Q8) |
| `time` | Obligatorio; ∈ `BOOKING_HOURS` |
| `document_type` | Obligatorio; ∈ códigos de `DOCUMENT_TYPES` |
| `document_number` | Obligatorio; `^[0-9]{4,20}$` (solo dígitos, enmienda 2026-10-09) |
| `patient_name` | Obligatorio; 3–120 caracteres tras `strip()` |
| `email` | Obligatorio; `^[^@\s]+@[^@\s]+\.[^@\s]+$` |
| `phone` | Obligatorio; `^[0-9]{7,15}$` (solo dígitos, enmienda 2026-10-09) |

**Disponibilidad**: horas libres = `BOOKING_HOURS` − horas con una cita para el mismo
`(service, date)`. Solo se consulta/muestra para fechas laborables ≥ hoy; una fecha de
fin de semana devuelve lista vacía (sin error).

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-5][CL-1..CL-5]`

```text
# --- capa web -------------------------------------------------------------
FUNCTION handle_booking_page(request):                    # GET /citas
    IF request.method != "GET": RETURN error_405()        # PUT/DELETE → 405
    view = get_home_view()                                # nav idéntica al resto
    today = next_weekday(today())                         # lun–vie ≥ hoy
    hours = get_available_hours(service=DEFAULT_SERVICE, date=today)   # RF-1
    RETURN render("appointments/index.html", view=view,
                  services=get_services_view(), document_types=DOCUMENT_TYPES,
                  hours=hours, values={}, errors={})      # HTTP 200

FUNCTION handle_availability(request):                    # GET /citas/horarios
    service = request.args.get("service", "")
    date    = request.args.get("date", "")
    IF service NOT IN SERVICES_CATALOG OR NOT valid_iso(date):
        RETURN jsonify(error="Parámetros inválidos."), 400        # RF-5
    hours = get_available_hours(service, date)            # [] si finde o pasada
    RETURN jsonify(available=hours), 200                  # RF-1, RF-3

FUNCTION handle_create(request):                          # POST /citas
    IF request.method != "POST": RETURN error_405()
    data   = parse(request.form)                          # 8 campos
    errors = validate_booking(data)                       # RF-2, RF-5 (§2.3)
    IF errors NOT EMPTY:
        RETURN render(form, values=data, errors=errors), 200      # CL-1, CL-2: 0 inserts
    result = create_booking(data)
    IF result == SLOT_TAKEN:                              # RF-3, CL-3, CL-4
        RETURN render(form, values=data,
                      errors={time: MSG_SLOT_TAKEN}), 200        # 0 inserts
    RETURN redirect(f"/citas/confirmada/{result.id}", 303)        # RF-1 (PRG, D10)

FUNCTION handle_confirmation(cita_id):                    # GET /citas/confirmada/<id>
    appointment = get_appointment_by_id(cita_id)
    IF appointment IS NULL: RETURN error_404()
    RETURN render("appointments/confirmation.html",
                  appointment=appointment), 200          # RF-1, RF-4

# --- capa de servicio -----------------------------------------------------
FUNCTION validate_booking(data):
    errors = {}
    FOR field, rule IN RULES(§2.3):
        IF data[field] VACÍO:    errors[field] = MSG_REQUIRED_*
        ELIF NOT rule(data[field]): errors[field] = MSG_INVALID_*
    RETURN errors                                       # nunca lanza excepciones

FUNCTION get_available_hours(service, date):
    IF date EN FIN DE SEMANA O PASADA: RETURN []
    booked = repository.list_booked_times(service, date)
    RETURN [h FOR h IN BOOKING_HOURS IF h NOT IN booked]           # RF-1

FUNCTION create_booking(data):
    IF repository.is_slot_taken(service, date, time):
        RETURN SLOT_TAKEN                               # SELECT previo (D9)
    TRY:
        RETURN repository.insert_appointment(data, status="pending")   # RF-4
    CATCH IntegrityError (UNIQUE service+date+time):
        RETURN SLOT_TAKEN                               # segunda capa (D4/D9)
```

**CL-3 / CL-4 (doble comprobación, D9)**: el `SELECT` previo da el mensaje normal;
el índice `UNIQUE` protege la ventana entre ambos en el punto de persistencia
(AGENTS.md: la comprobación previa no sustituye a la protección de persistencia).
Ambos caminos producen el mismo literal `MSG_SLOT_TAKEN` y **ninguna fila nueva**.

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor (crea `data/consultorio.db` si no existe) | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `python -m pytest -q` | Suite completa (74 actuales + ~27 nuevos) | `N passed` | `0` / `1` |
| `python -m pytest tests/test_hu_004.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-1..RF-5]`

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `GET` | `/citas` | `appointments/index.html` con h1 «Agendar cita», `<form>` de 8 campos en 2 columnas (paciente ‖ datepicker + horas en bloques Mañana/Tarde) y «Volver al inicio» | **200** |
| `POST` | `/citas` (válido y libre) | redirige a la confirmación | **303** → **200** |
| `POST` | `/citas` (dato faltante/inválido/servicio no válido) | formulario con mensajes, **0 filas** nuevas | **200** |
| `POST` | `/citas` (horario ocupado) | formulario con `MSG_SLOT_TAKEN`, **0 filas** nuevas | **200** |
| `GET` | `/citas/horarios?service=…&date=…` | JSON `{"available": ["08:00", …]}` (vacío si finde/pasada/todas ocupadas) | **200** |
| `GET` | `/citas/horarios` sin parámetros o con servicio/fecha inválidos | JSON `{"error": "Parámetros inválidos."}` | **400** |
| `POST/PUT/DELETE` | `/citas/horarios` | `errors/405.html` | **405** |
| `GET` | `/citas/confirmada/<id>` | `appointments/confirmation.html` (resumen + «Pendiente») | **200**; **404** si no existe |
| `PUT/DELETE` | `/citas` | `errors/405.html` | **405** |
| `GET` | `/articulos`, `/contacto` | siguen en `sections/under_construction.html` | **200** (regresión HU-001) |
| `GET` | `/`, `/nosotros`, `/servicios`, `/buscar…` y resto | sin cambios | 200 / 404 / 405 |

**Contrato semántico (lo que verifican los tests):**

```text
[RF-1] GET /citas → h1 «Agendar cita» + <form> con exactamente los 8 campos
       y «Volver al inicio»                              → absent ⇒ FAIL
[RF-1] POST válido → 303 → confirmación «Cita registrada» con
       servicio, fecha, hora y estado «Pendiente»        → absent ⇒ FAIL
[RF-2] POST con cada dato obligatorio vacío → 200 con su
       mensaje literal y 0 filas nuevas                  → absent ⇒ FAIL
[RF-2] POST con formato inválido (correo/celular/documento/
       fecha pasada o finde/hora fuera de catálogo) → 200 con
       mensaje y valores conservados en el form          → absent ⇒ FAIL
[RF-3] POST sobre horario ocupado → 200 con «Ese horario ya no
       está disponible…» y exactamente 1 fila             → absent ⇒ FAIL
[RF-3] tras registrar, GET /citas/horarios ya NO incluye esa
       hora para ese servicio/fecha                      → absent ⇒ FAIL
[RF-4] fila con document_type, document_number, patient_name,
       email, phone, service, date, time y status='pending'
                                                       → ausente ⇒ FAIL
[RF-5] servicio fuera del catálogo → rechazado en POST con
       mensaje y 400 en GET /citas/horarios              → absent ⇒ FAIL
[RNF-1] <form> sin campos adicionales (sin dirección, motivo,
       teléfono fijo ni textarea)                        → presente ⇒ FAIL
[RNF-2] <meta viewport>, ≥1 @media (max-width…), paleta ⊆ 6 hex,
       párrafos justify + hyphens:none, sin desborde a 375 px
                                                       → absent ⇒ FAIL
[horas] HTML/JSON con exactamente los 14 slots
       08:00–11:30 y 14:00–16:30 repartidos en los bloques Mañana/Tarde;
       finde → lista vacía                       → absent ⇒ FAIL
[D19]  datepicker propio (sin `type="date"`), 2 columnas ≥768 px y días
       agendables (lun–vie ≥ hoy) diferenciados  → absent ⇒ FAIL
[regresión] /citas ∉ PLACEHOLDER_SECTIONS; /articulos y /contacto con
       «Sección en construcción.»; nav de 6 hrefs → 200 con
       «Volver al inicio»                                → absent ⇒ FAIL
[alcance] /citas sin textos de correo/WhatsApp/cancelación;
       portada y /servicios sin <form> de reserva        → presente ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Blueprint propio `appointments`**; la ruta `/citas` sale de `placeholders.py` | Frontera por HU (patrón D1 del plan 003 / D11 del plan 001); `placeholders.py` queda solo para secciones no implementadas | *Mantener la ruta en `placeholders.py`*: mezcla sección implementada con placeholders y obliga a condicionar el módulo genérico | RF-1..5 |
| D2 | **SQLite con `sqlite3` de la stdlib y capa `persistence/` nueva, sin ORM** | Q4 + constitución #1 (sin dependencias) y #5 (integridad en persistencia); `MEMORY.md` ya preveía crear `persistence/` con la primera HU con BD | *Flask-SQLAlchemy*: dependencia nueva sin aprobación. *Guardar en sesión/memoria*: RF-1/RF-4 exigen registro duradero | RF-1, RF-4 |
| D3 | **Tabla única `appointments` con las columnas del paciente** (sin tabla `patients`) | RF-4 asocia la cita al paciente; ninguna spec pide identificar o reutilizar pacientes (constitución #1) | *Tabla `patients` separada*: normalización sin requisito que la exija; migración posterior si una HU la pide | RF-4 |
| D4 | **Índice `UNIQUE (service, date, time)` desde HU-004** (Q5) | AGENTS.md exige proteger la integridad en el punto de persistencia; la constitución #5 prohíbe confiar solo en comprobaciones previas; base sobre la que HU-006 añadirá concurrencia | *Solo `SELECT` previo*: ventana sin protección hasta HU-006. *Unicidad solo por fecha+hora*: contradice Spec 006 RF-2 (combinación servicio+fecha+hora) | RF-3, RF-4, CL-4 |
| D5 | **Estado inicial `pending` («Pendiente»)** (Q2) | Duda abierta de la spec cerrada por la usuaria; valor técnico en inglés y etiqueta en español (constitución #6); deja margen a estados posteriores (007/010) | *«Confirmada»*: implicaría confirmación que aún no existe (correo/WhatsApp son specs aparte) | RF-4 |
| D6 | **5 datos obligatorios: tipo y nº de documento, nombre y apellido, correo y celular** (Q1) | Decisión de la usuaria; cubre lo que necesitarán HU-008 (correo) y HU-009 (celular); satisface el RNF «limitarse a los datos necesarios» | *Menos campos*: dejaría a 008/009 sin dato obligatorio. *Añadir dirección/motivo*: datos sin requisito que los use | RF-1, RF-2, RNF-1 |
| D7 | **Select de horas con disponibilidad en vivo: `GET /citas/horarios` + `availability.js`** (Q3) | La usuaria lo eligió; además RF-3 exige que el horario «haya estado disponible» antes de confirmar; la lógica vive en `services/`+`persistence/` y el JS solo pinta (constitución #3); HU-005 reutilizará el endpoint | *Horas fijas sin estado*: el paciente elegiría a ciegas. *Sin JS, recarga por submit*: peor UX y no actualiza al cambiar servicio/fecha (AGENTS.md frontend) | RF-1, RF-3, RNF-2 |
| D8 | **`BOOKING_HOURS` en `content/`: 14 bloques de 30 min, 08:00–12:00 y 14:00–17:00 como horas de fin** (Q7) | Decisión de la usuaria 2026-10-09; literales versionados y testeables; 12:00–14:00 queda libre (almuerzo); ampliable por HU-005/012 actualizando spec primero | *Horas de inicio hasta 12:00/17:00*: produciría bloques que terminan a las 12:30/17:30 (descartada por la usuaria). *Frecuencia de 1 h*: descartada | RF-1 |
| D9 | **Doble comprobación de horario: `SELECT` previo + captura de `IntegrityError`, mismo literal** | RF-3/CL-4: el SELECT da el camino normal; el UNIQUE protege la ventana concurrente en la capa de persistencia; un único mensaje para el usuario | *Solo SELECT*: incumple AGENTS.md. *Solo UNIQUE*: error crudo 500 en lugar del comportamiento definido por la spec | RF-3, CL-3, CL-4 |
| D10 | **Patrón PRG: `POST` → `303` → `GET /citas/confirmada/<id>`** | Refrescar la confirmación no reenvía el formulario (que chocaría con el UNIQUE y mostraría un falso error RF-3); separa registro de presentación (constitución #3) | *Renderizar en el `POST`*: F5 repite el envío. *Confirmación en `/citas` con query*: confunde con el formulario | RF-1, RF-4 |
| D11 | **Errores de validación en `200` re-renderizando el formulario con los valores conservados** | Patrón de la casa (200 para estados de usuario); no existen plantillas 400/422; RF-2 pide «indicar la información que debe corregirse», no un código HTTP | *400/422*: exigiría plantillas y códigos nuevos sin requisito. *Redirigir con flash*: añade sesión/estado sin necesidad | RF-2 |
| D12 | **Solo lunes–viernes y fecha ≥ hoy** (Q8) | Decisión de la usuaria; materializa «dato inválido» de la spec sin inventar días de atención adicionales (011/012 podrán ampliarlos) | *Cualquier fecha*: permitiría reservar sábados/domingos. *Rango máximo de anticipación*: regla no solicitada | RF-2, CL-2 |
| D13 | **Validaciones de formato sin dependencias** (regex simples de correo/documento, celular 7–15 dígitos, nombre 3–120) | RF-2 «dato inválido»; stdlib puro (constitución #1); mensajes específicos por campo (RF-2: «indicará la información que debe corregirse») | *Solo comprobación de no vacío*: no cubre CL-2. *Librería `email-validator`*: dependencia sin aprobación | RF-2, CL-2 |
| D14 | **CSS `.appointment-*` mobile-first en `main.css` + JS nuevo `availability.js` (vanilla)** | RNF-2; mismo criterio que `.about-*`/`.services-page-*`/`.search-*` (D10/D7 de planes anteriores); JS vanilla exigido por la constitución #1 | *Archivo CSS nuevo*: fragmenta la hoja. *framework JS*: dependencia sin aprobación | RNF-2 |
| D15 | **Identificadores en inglés, mensajes en español; espejo único en `expected_content.py`** | Constitución #6 y AGENTS.md (textos contractuales: spec y espejo cambian juntos) | *Todo en español* / *literales solo en código*: ambos rompen la trazabilidad spec → test | todos |
| D16 | **Retirada de `/citas` de `placeholders.py` y de `PLACEHOLDER_SECTIONS`** (junto con la ruta) | Patrón D6/D11 de los planes 002/003: los tests que iteran el espejo se ajustan solos | *Tocar las specs 001/003*: su CL es genérica («aún no implementada»), no requiere enmienda | regresión |
| D17 | **Sin estado «en curso», sin deshabilitar el botón ni transacciones de concurrencia en esta HU** | Eso es RF-5 y la concurrencia de la Spec 006; AGENTS.md solo exige esos estados «cuando así lo establezca la especificación» | *Anticipar el comportamiento de 006*: funcionalidad sin spec propia (AGENTS: nada por conveniencia) | fuera de alcance |
| D18 | **La disponibilidad se calcula por `(service, date)`** | Coherente con la unicidad de D4 y con Spec 006 RF-2; Spec 005 deja su duda equivalente abierta y podrá ampliarla | *Agenda única por fecha (todas las citas)*: impediría dos servicios a la misma hora, contradiciendo 006 RF-2 | RF-1, RF-3 |
| D19 | **Layout en 2 columnas (datos del paciente ‖ calendario + horas en bloques)** y **datepicker propio vanilla** con días disponibles diferenciados (usuaria, 2026-10-09, modificación visual posterior a la primera entrega) | Petición explícita de la usuaria; materializa RNF-2 (comprensible y usable en escritorio y móvil); el calendario distingue visualmente días agendables (lun–vie ≥ hoy, D12) de no agendables; las horas se muestran en dos bloques diferenciados **Mañana** (08:00–11:30) y **Tarde** (14:00–16:30) siguiendo el catálogo D8; JS vanilla (constitución #1) y paleta intacta | *`<input type="date">` nativo*: no permite diferenciar días disponibles/no disponibles. *Librería de calendario (flatpickr etc.)*: dependencia sin aprobación. *Select único de horas*: estado anterior, menos comprensible por bloques. *Marcar días con citas libres/ocupadas*: eso es el estado por día de HU-005 (Q10); aquí solo se aplica la regla D12 | RNF-2, RF-1 |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` (suite) · `python -m pytest tests/test_hu_004.py -v`
(HU). Fixtures: `conftest.py` — `app` y `client` **ampliados con BD temporal por test**
(`DATABASE_PATH` en directorio temporal, borrada al cierre) sin romper los fixtures
actuales. Arrange/Act/Assert, sin dependencia del orden. `tests/expected_content.py`
concentra los literales de la spec 004 (espejo único, se actualiza junto con la spec —
D15).

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-004-001 | `test_appointment_content.py` | `BOOKING_HOURS` = exactamente los 14 slots (08:00–11:30 y 14:00–16:30), ordenados, formato `HH:MM`, sin duplicados | RF-1, RNF-1 |
| TC-004-002 | `test_appointment_content.py` | `DOCUMENT_TYPES` = exactamente CC, TI, CE, PASSPORT, RC con sus etiquetas en español | RF-2 |
| TC-004-003 | `test_appointment_content.py` | Espejo: mensajes/títulos de `expected_content` idénticos a `appointment_content` y a los literales de la spec | RF-1, RF-2, RF-3 |
| TC-004-004 | `test_appointment_persistence.py` | `init_db()` crea `appointments` con las 11 columnas y el índice `UNIQUE (service, date, time)` | RF-4 |
| TC-004-005 | `test_appointment_persistence.py` | `insert_appointment()` persiste con `status='pending'`; `get_appointment_by_id()` recupera todos los campos | RF-1, RF-4 |
| TC-004-006 | `test_appointment_persistence.py` | **CL-4:** segundo insert con la misma combinación servicio+fecha+hora → `IntegrityError`, queda 1 fila | RF-3, CL-4 |
| TC-004-007 | `test_appointment_persistence.py` | Misma fecha/hora con **servicio distinto** → insert permitido (unicidad por la terna) | RF-4, CL-4 |
| TC-004-008 | `test_appointment_service.py` | `validate_booking()` con datos válidos → `{}` (sin errores) | RF-1, RF-2 |
| TC-004-009 | `test_appointment_service.py` | **CL-1:** cada campo obligatorio vacío → su mensaje literal exacto, sin excepciones | RF-2, CL-1 |
| TC-004-010 | `test_appointment_service.py` | **CL-2:** formatos inválidos (correo, celular, documento, nombre corto, fecha pasada, sábado/domingo, hora fuera de catálogo) → mensaje específico por campo | RF-2, CL-2 |
| TC-004-011 | `test_appointment_service.py` | **CL-5:** servicio inexistente o no catálogo → `MSG_INVALID_SERVICE`; nunca se registra | RF-5, CL-5 |
| TC-004-012 | `test_appointment_service.py` | `get_available_hours()` = catálogo − ocupadas para (servicio, fecha); fin de semana/pasada → `[]`; sin citas → los 14 slots | RF-1, RF-3 |
| TC-004-013 | `test_appointment_service.py` | **CL-3:** tras `create_booking()`, esa hora desaparece de la disponibilidad | RF-3, CL-3 |
| TC-004-014 | `test_appointment_service.py` | **CL-3/CL-4:** `create_booking()` sobre horario ocupado → `SLOT_TAKEN` con `MSG_SLOT_TAKEN` y 0 inserts nuevos | RF-3, CL-3, CL-4 |
| TC-004-015 | `test_appointment_routes.py` | `GET /citas` → **200** con h1 «Agendar cita», `<form>` con los 8 campos (horas en bloques, D19), «Volver al inicio» y nav de 6 | RF-1, RNF-1 |
| TC-004-016 | `test_appointment_routes.py` | `POST /citas` válido → **303** → confirmación **200** con «Cita registrada», datos de la cita y «Pendiente»; 1 fila creada | RF-1, RF-4 |
| TC-004-017 | `test_appointment_routes.py` | **CL-1:** `POST` sin cada dato obligatorio → **200** con su mensaje y **0 filas** | RF-2, CL-1 |
| TC-004-018 | `test_appointment_routes.py` | **CL-2:** `POST` con dato inválido → **200**, mensaje visible, valores conservados en el formulario y 0 filas | RF-2, CL-2 |
| TC-004-019 | `test_appointment_routes.py` | **CL-3/CL-4:** `POST` sobre horario ocupado (insert previo) → **200** con `MSG_SLOT_TAKEN` y exactamente 1 fila | RF-3, CL-3, CL-4 |
| TC-004-020 | `test_appointment_routes.py` | **CL-5:** `POST` con servicio inválido → **200** con mensaje y 0 filas; `GET /citas/horarios?service=fantasma` → **400** | RF-5, CL-5 |
| TC-004-021 | `test_appointment_routes.py` | `GET /citas/horarios` → **200** JSON con horas libres; tras reservar esa hora ya no aparece; finde → `[]`; `POST /citas/horarios` → **405** | RF-1, RF-3 |
| TC-004-022 | `test_appointment_routes.py` | `GET /citas/confirmada/999999` → **404** con `errors/404.html`; `PUT /citas` → **405** | RF-1, regresión |
| TC-004-023 | `test_appointment_routes.py` | Regresión: `/citas` ∉ `PLACEHOLDER_SECTIONS`; `/articulos` y `/contacto` siguen «Sección en construcción.»; nav de 6 hrefs → 200 con «Volver al inicio»; `/`, `/nosotros`, `/servicios`, `/buscar` intactos | regresión HU-001/002/003/016 |
| TC-004-024 | `test_hu_004.py` | **RNF-2:** `<meta viewport>`, `main.css` con ≥1 `@media (max-width…)`, colores ⊆ paleta de 6 hex, párrafos `justify` + `hyphens: none`, sin desborde a 375 px; `availability.js` sin import de librerías externas | RNF-2 |
| TC-004-025 | `test_hu_004.py` | **RNF-1:** el `<form>` de `/citas` contiene exactamente los 8 campos permitidos (sin dirección, motivo ni textarea) | RNF-1 |
| TC-004-026 | `test_hu_004.py` | **E2E:** desde `GET /` seguir «Agendar cita» → **200**, completar el formulario → submit → confirmación visible con estado «Pendiente» | RF-1, RF-4, criterios de finalización |
| TC-004-027 | `test_hu_004.py` | **Fuera de alcance:** `/citas` sin textos de correo/WhatsApp/cancelación/n8n; portada y `/servicios` sin `<form>` de reserva (TC-001-008/TC-003-015 siguen verdes) | fuera de alcance |
| TC-004-028 | `test_hu_004.py` | **D19/RNF-2:** `/citas` con layout 2 columnas (`.appointment__layout` + 2 paneles), datepicker propio (`#booking-calendar` con `data-today`, sin `type="date"`), horas en `<fieldset>` Mañana/Tarde con radios `name="time"`; `main.css` con reglas de calendario y bloques y `availability.js` con navegación de meses/días agendables | RNF-2, D19 |

### 6.2 Pirámide

1. **Unitarias** — `appointment_content`, `persistence/` y `appointment_service` sin
   HTTP. `[RF-1..RF-5][CL-1..CL-5]`
2. **Integración HTTP** — `test_client` sobre `/citas`, `/citas/horarios`,
   `/citas/confirmada/<id>` y regresión de rutas. `[RF-1..RF-5]`
3. **Regresión** — `python -m pytest -q` completo: los **74 tests actuales** de
   HU-001/002/003/016 deben seguir verdes con el ajuste D16. `[todos]`
4. **Visual/manual** — capturas 1280 y 375 + recorrido del flujo completo (formulario,
   selección de horario, error de validación, horario ocupado y confirmación) en
   navegador (exigido por los criterios de finalización). `[RNF-2][RF-1][RF-3]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar.
- Pruebas deterministas: fechas relativas calculadas en la prueba (lunes laborable
  futuro), sin estado compartido (BD temporal por test), sin orden accidental.

```text
HU: HU-004
Caso: TC-004-016
Comando: python -m pytest tests/test_appointment_routes.py -v
Resultado: PASS
Rama: feature/hu-004
Commit: <hash>
Evidencia visual: docs/evidencias/hu-004/escritorio-1280.png, movil-375.png
```

- Informe QA: `docs/evidencias/hu-004/qa-hu-004.md` con PASS/FAIL por TC y checkbox de
  aceptación; veredicto `PASS` / `PARCIAL` / `FAIL` (skill `pytest-qa`).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Datos obligatorios (duda abierta de la spec) | **Tipo de documento (CC, TI, CE, Pasaporte, RC), número de documento, nombre y apellido, correo electrónico y celular** (usuaria, 2026-10-09); la duda se cierra en la spec 004. |
| Q2 | Estado inicial de la cita (duda abierta de la spec) | **`pending` / «Pendiente»** (usuaria, 2026-10-09); se cierra en la spec 004. |
| Q3 | Selector de horario (¿alcance respecto de HU-005?) | **Select con disponibilidad en vivo** (usuaria, 2026-10-09); el endpoint se entrega en 004 y se reutiliza en 005. |
| Q4 | Persistencia | **Sí: SQLite + `consultorio/persistence/`** (usuaria, 2026-10-09); primera BD del proyecto. |
| Q5 | Unicidad `service + date + time` | **Índice `UNIQUE` desde HU-004** (usuaria, 2026-10-09); HU-006 se centra en concurrencia y estado en curso. |
| Q6 | Rama de trabajo | **Merge `feature/identidad-buscador` → `main`** (HU-016 aceptada) y **`feature/hu-004` desde `main`** (usuaria, 2026-10-09). |
| Q7 | Catálogo de horas | **Bloques de 30 min: 08:00–12:00 y 14:00–17:00 como horas de FINALIZACIÓN** → 14 slots 08:00–11:30 y 14:00–16:30 (usuaria, 2026-10-09). |
| Q8 | Días agendables | **Solo lunes a viernes** (usuaria, 2026-10-09). |
| Q9 | Literales de mensajes (errores, confirmación, helper) | **Aprobados por la usuaria el 2026-10-09** y **enmendados el mismo día**: número de documento y celular **solo dígitos** (§2.2/§2.3). Textos contractuales (AGENTS.md); se fijan en la spec 004 (§8.1) antes de codificar. |
| Q10 | Solape con HU-005 | **Delimitado**: 004 entrega el endpoint `/citas/horarios`, el select de horas y (enmienda D19, 2026-10-09) un datepicker propio que diferencia días agendables por la regla D12; 005 conserva el estado **por día** (días con/sin citas libres), el mensaje de «fecha sin horarios», la distinción comprensible de estados (no solo color) y su RNF de actualización perceptible. Sin cambio de specs (005 RF-1/RF-2/RF-5 quedan testeables sobre esta base). |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Enmienda de `specs/004_agendar-cita/spec.md` (§8.1): cerrar las 2 dudas abiertas
      (Q1, Q2) y fijar literales — mensajes de error/éxito, helper de representante,
      `BOOKING_HOURS`, reglas de fecha/día y campos obligatorios (Q7/Q8/Q9) —
      **bloquea la implementación** y requiere petición explícita sobre `specs/`.
- [x] Aprobación de este `plan.md` y de los literales Q9 por la usuaria
      (2026-10-09).
- [x] Merge a `main` y creación de `feature/hu-004` (Q6).
- [x] Implementar módulos, persistencia, plantillas, JS y CSS (§1–§5).
- [x] Tests (§6) y `python -m pytest -q` en verde (74 actuales + ~27 nuevos).
- [x] Evidencia QA (`qa-hu-004.md`, veredicto PASS) y evidencia visual
      (`escritorio-1280.png`, `movil-375.png`) con demo sobre el servidor
      (`GET /citas` → 200 y reserva completa).
- [x] Commit/Push de la evidencia y actualización de `MEMORY.md`.
- [x] Aceptación de la HU (checkbox del informe QA) — **2026-10-09**, incluye la
      modificación visual D19 y el ajuste de columna izquierda.

---

## 8. Secuencia de implementación

0. **Git**: merge `feature/identidad-buscador` → `main`; crear `feature/hu-004` desde
   `main` (Q6).
1. **Spec primero**: enmienda de la spec 004 — cerrar las dudas Q1/Q2, añadir campos
   obligatorios, `BOOKING_HOURS`, reglas de fecha/día y los literales aprobados (Q9).
2. **Plan**: este `plan.md` (aprobado 2026-10-09).
3. **Config y espejo**: `Config.DATABASE_PATH` + `BOOKING_HOURS`, `DOCUMENT_TYPES` y
   mensajes en `tests/expected_content.py` (Q9; `PLACEHOLDER_SECTIONS` se toca en el
   paso 7, junto con la ruta).
4. **Contenido**: `consultorio/content/appointment_content.py` (§2.2).
5. **Persistencia**: `consultorio/persistence/database.py` + `appointments_repository.py`
   (esquema §2.1, UNIQUE) → `test_appointment_content.py` +
   `test_appointment_persistence.py`.
6. **Servicio**: `consultorio/services/appointment_service.py` (§3) →
   `test_appointment_service.py`.
7. **Capa web**: `consultorio/web/appointments.py` + plantillas
   `appointments/index.html` y `confirmation.html` + retirar `/citas` de
   `placeholders.py` + registrar `appointments_bp` en `create_app()` + `init_db()` +
   `PLACEHOLDER_SECTIONS` sin `/citas` (D16) → `test_appointment_routes.py`.
8. **JS de disponibilidad**: `static/js/availability.js` (fetch al cargar y al cambiar
   servicio/fecha; mensaje `MSG_NO_HOURS` con la lista vacía).
9. **CSS**: sección `.appointment-*` en `static/css/main.css` (mobile-first, paleta
   intacta, párrafos justificados sin guiones).
10. **Tests de HU**: `test_hu_004.py` (RNF, E2E, fuera de alcance).
11. **Suite completa**: `python -m pytest -q` → 0 FAIL con los 74 tests previos intactos.
12. **Evidencia**: servidor (`python app.py`), capturas CDP 1280/375 →
    `docs/evidencias/hu-004/` + `qa-hu-004.md` con PASS/FAIL por TC.
13. **Cierre**: commits por fase, push, `MEMORY.md` (HU-004 + primera persistencia) y
    aceptación de la HU.
