# Plan 006 — Evitar doble reserva de citas

> Trazabilidad: **HU-006 → Spec 006 (`specs/006_evitar-doble-reserva/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs`.
> Etapa actual: **PLAN PROPUESTO — decisiones Q1–Q5 APROBADAS** (2026-10-09): política
> de duplicados históricos (prevenir + detectar), mecanismo RF-5 (POST de formulario
> con estado en el botón), literal «Registrando tu cita…», reintento rechazado con
> `MSG_SLOT_TAKEN` y rama `feature/hu-006` desde `main`.
> **HU-005 ACEPTADA (2026-10-09)** → cierre y merge a `main` realizados (§8.0).
> **Spec 006 ENMENDADA (2026-10-09)** (§8.1, bloqueante cumplido).
> Rama objetivo: **`feature/hu-006` desde `main`** (Q5, D10) — **creada 2026-10-09**.

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 006: que un horario no pueda quedar
reservado por más de una cita válida **incluso bajo concurrencia**, que el paciente
reciba una respuesta clara cuando el horario dejó de estar disponible, que el sistema
muestre un estado «en curso» durante la reserva y no permita acciones duplicadas, y
que exista una política cerrada para los duplicados históricos.

**Base existente (HU-004 y HU-005 aceptadas)**:
- `UNIQUE (service, date, time)` y doble comprobación `SELECT` previo + `IntegrityError`
  (D9 plan 004) con literal `MSG_SLOT_TAKEN`; patrón PRG (`POST → 303 →
  /citas/confirmada/<id>`).
- HU-005: `available`/`occupied` en `/citas/horarios`, horas «Ocupado» (`disabled`,
  sin `name`), refresco con guards `seq` al cambiar fecha/servicio y estado de conflicto
  en `#hours-status`.
- **Baseline verificado: `python -m pytest -q` → 118 PASS / 0 FAIL** (2026-10-09).

Esta HU **no reescribe lo que funciona** (regla de oro de AGENTS.md): endurece,
demuestra y completa lo que la Spec 006 exige y que los planes previos dejaron
explícitamente reservado para aquí (D17 del plan 004: estado «en curso»; D9 del plan
004: concurrencia; §0 del plan 005: «prevención de concurrencia como objetivo
independiente (Spec 006)»).

**Fuera de alcance**: notificaciones (Specs 008/009), automatización n8n (Spec 007),
cancelación de citas, agenda interna del psicólogo (Specs 011/012), cambio de estado
de la cita más allá de `pending`, saneamiento automático de la base de datos,
dependencias nuevas (constitución #1), cambios de esquema SQLite y rediseño del
formulario.

**Sin cambios de modelo de datos**: tabla `appointments` e índice
`UNIQUE (service, date, time)` intactos (constitución #5; AGENTS.md: nada de tablas
sin spec).

**Duda abierta de la spec** (debe cerrarse por enmienda antes de codificar):
- **Q1 — duplicados históricos**: propuesta de cierre (§7.1): **prevenir (índice) +
  detectar mediante diagnóstico en los tests, sin saneamiento automático**; cualquier
  limpieza exige decisión explícita de la usuaria con respaldo/auditoría (AGENTS.md).

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Horario libre → se registra una única cita válida | §2.3 capas de protección; §3 `create_booking()`; §4 `POST /citas` → 303; §5 D2/D3; §6 TC-006-001/003/007 |
| RF-2 | Horario reservado → impide otra cita sobre la misma combinación servicio+fecha+hora | §2.1 clave única; §2.3 SELECT previo; §3; §4 semántico; §5 D2/D3/D9; §6 TC-006-002/004/005/006/008 |
| RF-3 | Dos intentos concurrentes → máximo una reserva válida, rechazo de las restantes | §3 `IntegrityError`/bloqueo → `SLOT_TAKEN`; §5 D3/D12; §6 TC-006-003/005/007 |
| RF-4 | Horario deja de estar disponible tras mostrarse libre → rechaza e informa | §2.2 `MSG_SLOT_TAKEN` (reutilizado); §3 re-render con horas recalculadas; §4 semántico; §5 D5; §6 TC-006-006/008/010 |
| RF-5 | Durante el procesamiento → estado «en curso» y sin acciones duplicadas | §2.2 `MSG_SUBMITTING`; §3 guard de submit en JS; §1 plantilla/JS/CSS; §5 D4/D6/D7; §6 TC-006-009/011/012/014 |
| RF-6 | Integridad de las reservas frente a duplicados y solicitudes concurrentes | §2.1 índice + diagnóstico; §2.3/§3 doble comprobación; §5 D2/D3/D8; §6 TC-006-003/005/007/013/015/016 |
| RNF-1 | Integridad y consistencia de las reservas | constitución #5 + §2.1 + §3; §6 TC-006-013/015/016 |
| RNF-2 | Respuesta clara ante conflictos | §2.2 `MSG_SLOT_TAKEN`; §3 re-render «Ocupado»; §4 contrato; §6 TC-006-006 |
| RNF-3 | Experiencia usable durante el procesamiento | §2.2 literal + §3 estado en botón/form; §1 CSS; §6 TC-006-011/012 |
| CL-1 | Dos o más intentos simultáneos | §3 concurrencia; §6 TC-006-003/007 |
| CL-2 | Horario ocupado después de mostrarse disponible | §3 re-render (HU-005 lo sirve como «Ocupado»); §6 TC-006-006/010 |
| CL-3 | Registros históricos duplicados | §2.1 política de diagnóstico; §6 TC-006-013/015; Q1/D8 |
| CL-4 | Reintento de una misma solicitud | §3 rechazo; §6 TC-006-002; Q4/D9 |
| CL-5 | Cambio de servicio después de consultar un horario | §4 terna por servicio; §6 TC-006-004/008/010 (regresión guards HU-005) |
| Finalización | Tests en verde (incluida concurrencia y regresión) + demo antes-durante-después | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-6][CL-1..CL-5][RNF-1..RNF-3]` — Constitución #3: la lógica de reserva vive
en `services/` + `persistence/`; el JS solo gestiona la presentación del estado y la
protección frente a dobles clics. Estructura por capas y patrón de blueprint ya
validados; solo se muestran los **cambios sobre lo existente**:

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   └── appointment_content.py   # + MSG_SUBMITTING (§2.2)            [RF-5]
│   ├── services/
│   │   └── appointment_service.py   # create_booking(): capturar
│   │                             #   sqlite3.IntegrityError y bloqueo
│   │                             #   → SLOT_TAKEN (§3)                [RF-2][RF-3][RF-6]
│   └── web/
│       └── appointments.py          # _render_form(): entrega
│                                 #   data-submitting a la plantilla;
│                                 #   contrato HTTP intacto            [RF-4][RF-5]
├── templates/appointments/index.html  # botón identificable
│                                 #   (.appointment__submit) y literal
│                                 #   en #booking-calendar
│                                 #   data-submitting                   [RF-5]
├── static/
│   ├── js/availability.js           # guard de submit: primer envío →
│   │                             #   estado en curso; envío repetido →
│   │                             #   preventDefault                    [RF-5]
│   └── css/main.css                 # estado en curso/deshabilitado del
│                                 #   botón (paleta intacta)            [RF-5][RNF-3]
└── tests/
    ├── expected_content.py          # + MSG_SUBMITTING (espejo único)   [RF-5]
    ├── test_double_booking_service.py  # unicidad, concurrencia con hilos
    │                             #   y mapeo de excepciones
    │                             #   [RF-1][RF-2][RF-3][RF-6][CL-1][CL-4][CL-5]
    ├── test_double_booking_routes.py   # conflicto HTTP, concurrencia POST,
    │                             #   estado en curso, regresión 005
    │                             #   [RF-1..RF-5][CL-2][CL-5]
    └── test_hu_006.py               # RNF, esquema + diagnóstico de
                                #   duplicados, espejo y regresión
                                #   [RF-4][RF-5][RF-6][todos]
```

**Sin cambios**: `persistence/database.py` (esquema), `persistence/appointments_repository.py`,
`create_app()`, `base.html`, `nav.js`, `availability.js` fuera del bloque de submit
(guards `seq`, calendario y horas de HU-005 intactos).

Responsabilidades (sin solaparse; solo módulos tocados):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/appointment_content.py` | Declarar `MSG_SUBMITTING` | Contener lógica ni acceder a la BD |
| `services/appointment_service.py` | Orquestar la reserva y traducir los fallos de unicidad/bloqueo a `SLOT_TAKEN` | Escribir HTML, manejar status codes |
| `web/appointments.py` | Rutas, status codes y entrega de literales a la plantilla | Consultar la BD directamente ni contener reglas de negocio |
| `templates/appointments/index.html` | Marco semántico del botón y atributos `data-*` | Condicionales de negocio |
| `static/js/availability.js` | Estado visual «en curso» y bloqueo de envíos repetidos | Decidir si el horario está libre (siempre servidor) |
| `static/css/main.css` | Presentación del estado en curso con la paleta vigente | Introducir colores nuevos |

---

## 2. Literales, modelo de datos y reglas de protección

`[RF-2][RF-3][RF-4][RF-5][RF-6][CL-3]` — Sin cambios de esquema (§2.1) y con el
literal de §2.2 **ya fijado en la spec 006 (enmienda 2026-10-09)** (textos
contractuales, AGENTS.md).

### 2.1 Modelo de datos — sin cambios

La tabla `appointments` y el índice `UNIQUE (service, date, time)` de HU-004 se
reutilizan tal cual; no hay migraciones. **Política de duplicados históricos (Q1)**:

- **Prevención**: el índice impide la creación de nuevos duplicados (constitución #5).
- **Detección**: los tests ejecutan el diagnóstico
  `SELECT service, date, time FROM appointments GROUP BY service, date, time
  HAVING COUNT(*) > 1` y exigen **0 filas**.
- **Sin saneamiento automático**: ante duplicados reales se requiere decisión explícita
  de la usuaria con respaldo/auditoría previa (AGENTS.md «Base de datos e integridad»).

### 2.2 Literales (`content/appointment_content.py`)

> Único literal nuevo (Q3, §7.1); **fijado en la spec 006 (enmienda 2026-10-09)**.
> `MSG_SLOT_TAKEN`, `MSG_OCCUPIED_HOUR`, `MSG_CHECKING_HOURS` y el
> resto de literales de HU-004/005 se **reutilizan sin cambio**.

```python
# RF-5: estado en curso del botón mientras se procesa la reserva
MSG_SUBMITTING: str = "Registrando tu cita…"
```

### 2.3 Reglas de protección (tres capas)

| Capa | Mecanismo | RF |
|---|---|---|
| Comprobación previa | `is_slot_taken()` (SELECT) → camino normal, sin excepciones ni mensaje técnico | RF-2, RF-4, CL-4 |
| Punto de persistencia | Índice `UNIQUE (service, date, time)` → `sqlite3.IntegrityError` → `SLOT_TAKEN`, 0 filas nuevas | RF-3, RF-6, CL-1 |
| Concurrencia | `busy_timeout` de la stdlib (5 s, por defecto) serializa las escrituras; un bloqueo no resuelto se traduce también a `SLOT_TAKEN` (nunca un 500) | RF-3, RF-6, RNF-2 |

Clave de unicidad: **exclusivamente `(service, date, time)`** (D18 plan 004, D2 plan
005, aprobados por la usuaria y coherentes con RF-2 de esta spec).

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-6][CL-1..CL-5][RNF-2]`

```text
# --- capa de servicio -------------------------------------------------
FUNCTION create_booking(data, db):
    IF repository.is_slot_taken(service, date, time, db):          # SELECT previo
        RETURN SLOT_TAKEN                                     [RF-2][CL-4]
    TRY:
        RETURN repository.insert_appointment(data, db)        # RF-1: 1 fila
    CATCH sqlite3.IntegrityError:                            # UNIQUE (service,date,time)
        RETURN SLOT_TAKEN                                     [RF-3][RF-6][CL-1][CL-4]
    CATCH sqlite3.OperationalError (locked/busy):
        RETURN SLOT_TAKEN                                     [RF-3][RF-6][RNF-2]
    # cualquier otra excepción se propaga (500 real, no silenciar)

# --- capa web (POST /citas; contrato intacto) -------------------------
FUNCTION handle_create(request):
    errors = validate_booking(data)
    IF errors NOT EMPTY: RETURN _render_form(data, errors), 200      # sin inserts
    result = create_booking(data, db)
    IF result == SLOT_TAKEN:
        RETURN _render_form(data, {time: MSG_SLOT_TAKEN}), 200       [RF-4]
        # _render_form recalcula los pares: la hora aparece «Ocupado»,
        # sin radio name="time" seleccionable                       [CL-2]
    RETURN redirect(f"/citas/confirmada/{result.id}", 303)            [RF-1]

# --- static/js/availability.js (nuevo bloque) -------------------------
FUNCTION initBookingSubmit():
    form = document.querySelector(".appointment__form")
    submitting = False
    form.addEventListener("submit", event =>                          [RF-5]
        IF submitting:
            event.preventDefault()          # evita el segundo POST    [RF-5]
            RETURN
        submitting = True
        button.disabled = True
        button.textContent = dataAttr("data-submitting")   # «Registrando tu cita…»
        form.setAttribute("aria-busy", "true"))             [RNF-3]

# --- diagnóstico de duplicados (solo en tests; Q1/D8) -----------------
# SELECT service, date, time FROM appointments
#  GROUP BY service, date, time HAVING COUNT(*) > 1   → []           [RF-6][CL-3]
```

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor (BD existente) | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `python -m pytest -q` | Suite completa (118 actuales + ~16 nuevos) | `N passed` | `0` / `1` |
| `python -m pytest tests/test_hu_006.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-1..RF-5]`

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `GET` | `/citas` | formulario con `data-submitting="Registrando tu cita…"` y botón `.appointment__submit` | **200** |
| `POST` | `/citas` (válido y libre) | redirige a la confirmación; **1 fila** | **303** → **200** |
| `POST` | `/citas` (horario ya ocupado o reintento) | formulario con `MSG_SLOT_TAKEN`, **0 filas** nuevas y la hora servida como «Ocupado» | **200** |
| `POST` | `/citas` (dato faltante/inválido) | formulario con mensajes (literal sin cambio) | **200** |
| `GET` | `/citas/horarios?service=…&date=…` | JSON `{"available": […], "occupied": […]}` | **200** |
| `GET` | `/citas/horarios` con parámetros inválidos | `{"error": "Parámetros inválidos."}` | **400** |
| `GET` | `/citas/disponibilidad?service=…&month=YYYY-MM` | JSON `{"days": […]}` | **200** |
| `GET` | `/citas/confirmada/<id>` | confirmación (sin cambios) | **200** / **404** |
| resto rutas y 405 | sin cambios | como hasta ahora | 200/303/404/405 |

**Contrato semántico (lo que verifican los tests):**

```text
[RF-1] POST sobre horario libre → exactamente 1 fila nueva (1×303)  → absent ⇒ FAIL
[RF-2] POST sobre terna ocupada → 200 con MSG_SLOT_TAKEN y COUNT(*)
       sin cambios (también en reintento idéntico)                  → absent ⇒ FAIL
[RF-3] N POST simultáneos sobre la misma terna → exactamente 1×303 y
       N-1×200 con MSG_SLOT_TAKEN; COUNT(*) = 1                     → absent ⇒ FAIL
[RF-4] en el 200 de conflicto, la hora ocupada se sirve como «Ocupado»
       y sin radio name="time" seleccionable                        → absent ⇒ FAIL
[RF-5] GET /citas lleva data-submitting; availability.js con guard de
       submit (preventDefault + disabled + aria-busy); main.css con
       el estado en curso                                           → absent ⇒ FAIL
[RF-6] esquema con UNIQUE (service, date, time) y consulta de
       duplicados → 0 filas                                         → absent ⇒ FAIL
[CL-3] BD de prueba creada sin el índice: el diagnóstico detecta las
       2 filas duplicadas                                           → absent ⇒ FAIL
[regresión] 118 tests previos intactos; /citas/horarios (available+occupied)
       y /citas/disponibilidad sin cambios de contrato              → present ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Sin dependencias ni frameworks**: concurrencia con `threading`/`concurrent.futures` (stdlib) y SQLite nativo | Constitución #1 y AGENTS.md; las pruebas de concurrencia no necesitan nada más | *SQLAlchemy/pytest-xdist/Pool externo*: dependencia sin aprobación | RF-3, RF-6 |
| D2 | **El índice `UNIQUE (service, date, time)` sigue siendo la garantía de unicidad**; sin migraciones ni objetos nuevos en la BD | Constitución #5: la integridad se protege en el punto de persistencia; la tabla nació con el índice (HU-004) y no hay duplicados posibles | *Tabla/clave de bloqueo*: más piezas móviles sin ganancia. *Índice adicional*: redundante | RF-2, RF-6 |
| D3 | **`create_booking()` endurecido**: capturar `sqlite3.IntegrityError` de forma específica y mapear también `OperationalError` de bloqueo a `SLOT_TAKEN`; el resto de excepciones se propaga | Hoy captura `Exception` y busca la subcadena "UNIQUE", lo que puede enmascarar errores ajenos; RF-3/RF-6 exigen rechazar las restantes y RNF-2 prohíbe un 500 crudo por concurrencia | *Solo SELECT previo*: ventana sin protección (AGENTS.md). *Solo UNIQUE con 500*: viola RF-4/RNF-2. *Transacción `BEGIN IMMEDIATE`*: más código con el mismo resultado ya garantizado por el índice (constitución #1); se conserva la doble comprobación D9 de HU-004 | RF-2, RF-3, RF-4, RF-6, RNF-2 |
| D4 | **RF-5 con el POST de formulario actual + estado en el botón** (Q2): guard `submitting` en JS, `preventDefault` en el envío repetido, `disabled` + texto + `aria-busy` en el primero | PRG intacto (no se reescribe un flujo que funciona); cubre «estado en curso» y «evitar acciones duplicadas»; vanilla JS (constitución #1) | *Envío vía `fetch` + redirect cliente*: reescribe el envío, añade manejo de errores de red y cambia el contrato de pruebas. *Solo servidor*: no cubre RF-5 | RF-5, RNF-3 |
| D5 | **Conflicto = `MSG_SLOT_TAKEN` reutilizado + re-render que recalcula las horas** (la ocupada se sirve «Ocupado», sin radio seleccionable) | RF-4/RNF-2: respuesta clara con textos ya fijados en specs 004/005; HU-005 ya pinta el estado ocupado | *Nuevo literal específico de concurrencia*: copy adicional sin requisito y más técnico para el paciente | RF-4, CL-2, RNF-2 |
| D6 | **Literal único nuevo `MSG_SUBMITTING` servido vía `data-submitting` en `#booking-calendar`** (mismo contenedor de literales de HU-004/005) | El JS nunca contiene textos (decisión de HU-005); el espejo `expected_content.py` mantiene la trazabilidad spec → test (constitución #6) | *Texto hardcodeado en el JS*: rompe el espejo. *Varios literales (spinner, aria-label)*: más copy sin necesidad | RF-5 |
| D7 | **CSS del estado en curso** en `.appointment__submit` (`:disabled` / `[aria-busy="true"]`) con cursor de espera y atenuación dentro de la paleta (salvia/arena) | AGENTS.md: la paleta es restricción, no sugerencia; RNF-3 (usable durante el procesamiento) | *Color nuevo de marca*: requiere decisión de diseño. *Spinner de librería*: dependencia sin aprobación | RF-5, RNF-3 |
| D8 | **Duplicados históricos (Q1): prevención + detección en tests, sin saneamiento automático** | AGENTS.md exige decisión explícita, respaldo/auditoría y pruebas para saneamientos; el índice ya impide nuevos duplicados; detectar es suficiente para cerrar la duda | *Limpieza automática en `init_db`*: riesgo de pérdida de datos sin decisión formal. *Función de diagnóstico en producción*: código sin consumidor funcional | RF-6, CL-3, RNF-1 |
| D9 | **Reintento de la misma solicitud (Q4) → rechazo con `MSG_SLOT_TAKEN` y 0 filas** | RF-3/RF-4 exigen rechazar las solicitudes restantes; es el comportamiento ya existente, ahora con test explícito | *Redirección idempotente a la confirmación*: comportamiento no pedido, exige enmienda de spec y detección de duplicado por datos | RF-2, RF-3, CL-4 |
| D10 | **Rama `feature/hu-006` desde `main`, tras aceptar y mergear HU-005** (Q5, aceptada 2026-10-09) | AGENTS.md: aislamiento de HU por rama; `main` vuelve a ser el punto de partida con 118 tests en verde | *Rama desde `feature/hu-005`*: arrastra pendientes de cierre. *Seguir en `feature/hu-005`*: mezcla dos HU en una rama | regresión |
| D11 | **Identificadores en inglés, mensajes en español; espejo único en `expected_content.py` actualizado junto con la enmienda de la spec** | Constitución #6 y AGENTS.md (textos contractuales: spec y espejo cambian juntos; patrón D15/D11) | *Literales solo en código*: rompe la trazabilidad spec → test | todos |
| D12 | **Tests de concurrencia deterministas**: `threading.Barrier` antes del INSERT, un `test_client` por hilo, BD temporal por fixture, sin `sleep` como sincronización | RF-3 necesita evidencia real de concurrencia; la determinización evita falsos positivos/negativos (pytest-qa) | *Pruebas secuenciales disfrazadas*: no demuestran RF-3. *`sleep` como coordinación*: flaky | RF-3, RF-6 |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` (suite) · `python -m pytest tests/test_hu_006.py -v`
(HU). Fixtures de `conftest.py` **sin cambios** (`app`, `client`, `database_path` con
BD temporal). Arrange/Act/Assert, sin dependencia del orden; fechas relativas
calculadas en cada prueba (lunes laborable futuro). `tests/expected_content.py`
concentra el literal nuevo (espejo único, D11).

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-006-001 | `test_double_booking_service.py` | Horario libre → `create_booking()` devuelve `Appointment` con `status='pending'` y exactamente **1 fila** | RF-1 |
| TC-006-002 | `test_double_booking_service.py` | **CL-4:** reintento con datos idénticos (secuencial) → `SLOT_TAKEN`, **0 filas** nuevas, la fila original intacta | RF-2, CL-4 |
| TC-006-003 | `test_double_booking_service.py` | **CL-1:** 8 hilos con `threading.Barrier` sobre la misma terna → **1** `Appointment`, **7** `SLOT_TAKEN` y `COUNT(*) = 1` | RF-3, RF-6, CL-1 |
| TC-006-004 | `test_double_booking_service.py` | **CL-5:** misma fecha/hora en **servicio distinto** → 2 citas válidas (unicidad por la terna; regresión TC-004-007) | RF-2, CL-5 |
| TC-006-005 | `test_double_booking_service.py` | `repository.insert_appointment` parcheado: `IntegrityError` → `SLOT_TAKEN`; `OperationalError("database is locked")` → `SLOT_TAKEN`; `ValueError` → **se propaga** (500 real, no silenciado) | RF-3, RF-6 |
| TC-006-006 | `test_double_booking_routes.py` | **CL-2:** `POST` sobre terna ocupada → **200** con `MSG_SLOT_TAKEN` visible, la hora servida como «Ocupado» (sin radio `name="time"` seleccionable) y **1 fila** total | RF-4, CL-2, RNF-2 |
| TC-006-007 | `test_double_booking_routes.py` | **CL-1:** 8 `POST` concurrentes (`ThreadPoolExecutor`, un `test_client` por hilo, Barrier) → **1×303**, **7×200** con `MSG_SLOT_TAKEN`, `COUNT(*) = 1` | RF-1, RF-3, RF-6, CL-1 |
| TC-006-008 | `test_double_booking_routes.py` | **CL-5:** hora ocupada en servicio A → `POST` con servicio B (misma fecha/hora) → **303** y 2 filas (combinación distinta) | RF-2, RF-4, CL-5 |
| TC-006-009 | `test_double_booking_routes.py` | `GET /citas` → **200** con `data-submitting="Registrando tu cita…"` y botón `.appointment__submit` | RF-5 |
| TC-006-010 | `test_double_booking_routes.py` | **Regresión HU-005:** tras reservar, `/citas/horarios` devuelve la hora en `occupied` y `/citas/disponibilidad` excluye el día lleno; 400/405 sin cambios | RF-4, CL-5, regresión |
| TC-006-011 | `test_hu_006.py` | **RF-5 (inspección estática, patrón TC-005-015):** `availability.js` con listener de `submit`, `preventDefault` en el envío repetido, `disabled`, `data-submitting` vía `dataAttr` y `aria-busy`; sin imports de librerías externas | RF-5 |
| TC-006-012 | `test_hu_006.py` | `main.css` con el estado en curso/deshabilitado de `.appointment__submit`; colores ⊆ paleta de 6 hex; párrafos `justify` + `hyphens: none`; sin desborde a 375 px | RF-5, RNF-3 |
| TC-006-013 | `test_hu_006.py` | **RF-6:** el esquema conserva `UNIQUE (service, date, time)` (consultado sobre `sqlite_master`) y el diagnóstico de duplicados devuelve **0 filas** tras un flujo completo de reservas | RF-6, RNF-1, CL-3 |
| TC-006-014 | `test_hu_006.py` | Espejo: `expected_content.MSG_SUBMITTING == appointment_content.MSG_SUBMITTING == "Registrando tu cita…"`; `MSG_SLOT_TAKEN` idéntico al de specs 004/005 | RF-4, RF-5 |
| TC-006-015 | `test_hu_006.py` | **CL-3:** BD temporal cuya tabla `appointments` se crea **sin** el índice (DDL del test) con 2 filas idénticas → el diagnóstico las detecta (valida la política Q1: detectar, no sanear) | RF-6, CL-3 |
| TC-006-016 | `test_hu_006.py` | **Regresión total:** `python -m pytest -q` → **0 FAIL** con los **118 tests previos** intactos (HU-001/002/003/016/004/005) | todos, finalización |

> **Nota de recuento (2026-10-09, verificada en ejecución)**: TC-006-016 es la propia
> corrida de la suite, no una función de test; los TC con función son **15**, de modo
> que el total es **133** (118 previos + 15). La cifra «134» de §4.1/§6.2 y del
> `task.md` contaba los 16 TC incluyendo la corrida; se corrige aquí sin tocar los
> criterios: **0 FAIL con los 118 previos intactos** sigue siendo la condición real.

### 6.2 Pirámide

1. **Unitarias** — `appointment_service.create_booking()` (libre, ocupado, reintento,
   concurrencia con hilos y mapeo de excepciones) sin HTTP.
   `[RF-1][RF-2][RF-3][RF-6][CL-1][CL-4]`
2. **Integración HTTP** — `test_client`: conflicto con respuesta clara, concurrencia
   de `POST`, contrato del estado en curso y regresión de los endpoints HU-005.
   `[RF-1..RF-5][CL-2][CL-5]`
3. **Regresión** — `python -m pytest -q` completo: los **118 tests actuales** deben
   seguir verdes sin enmiendas (ninguna aserción existente se relaja ni se omite).
   `[todos]`
4. **Visual/manual** — servidor `python app.py`: **demo antes-durante-después** de una
   reserva — antes (horario libre y botón en reposo), durante (botón «Registrando tu
   cita…» con `disabled` y `aria-busy`, capturado con *throttling* de red en DevTools
   o `Network.emulateNetworkConditions` por CDP) y después (confirmación + horario
   «Ocupado» y día `is-full` en el calendario) — con capturas CDP 1280 y 375
   (exigido por los criterios de finalización).
   `[RF-4][RF-5][RNF-2][RNF-3]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar (pytest-qa §1.2).
- Pruebas deterministas: Barrier en lugar de `sleep`, BD temporal por fixture, fechas
  relativas, sin estado compartido entre hilos (cada hilo crea su conexión y su
  cliente).

```text
HU: HU-006
Caso: TC-006-007
Comando: python -m pytest tests/test_double_booking_routes.py -v
Resultado: PASS
Rama: feature/hu-006
Commit: <hash>
Evidencia visual: docs/evidencias/hu-006/escritorio-1280.png, movil-375.png, boton-en-curso-1280.png
```

- Informe QA: `docs/evidencias/hu-006/qa-hu-006.md` con PASS/FAIL por TC y checkbox de
  aceptación; veredicto `PASS` / `PARCIAL` / `FAIL` (skill `pytest-qa`).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Duda abierta de la spec: política para duplicados históricos | **Prevenir (índice) + detectar en los tests, sin saneamiento automático**; cualquier limpieza requiere decisión explícita con respaldo/auditoría (D8). **Aprobada y fijada en la spec 006 — enmienda 2026-10-09.** |
| Q2 | Mecanismo del estado «en curso» (RF-5) | **POST de formulario actual + estado en el botón con guard JS** (D4). **Aprobada 2026-10-09.** |
| Q3 | Literal del estado en curso | **«Registrando tu cita…» → `MSG_SUBMITTING`** (D6). Texto contractual: **fijado en la spec 006 y en `expected_content.py` (enmienda 2026-10-09)**. **Aprobada 2026-10-09.** |
| Q4 | Caso límite «reintento de una misma solicitud» | **Rechazo con `MSG_SLOT_TAKEN` y 0 filas nuevas** (D9). **Aprobada y fijada en la spec 006 — enmienda 2026-10-09.** |
| Q5 | Rama de trabajo | **`feature/hu-006` desde `main`, tras aceptar y mergear HU-005** (D10). HU-005 **aceptada y mergeada 2026-10-09 (`8463087`)**; `feature/hu-006` **creada 2026-10-09**. |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Cierre de HU-005: merge de `feature/hu-005` a `main`, checkbox de aceptación en
      `qa-hu-005.md` y actualización de `MEMORY.md` (T18) — **2026-10-09
      (`8463087`, fast-forward de `main`).**
- [x] Aprobación de este `plan.md` (alcance, D1–D12 y literal Q3) por la usuaria
      — **2026-10-09**.
- [x] Enmienda de `specs/006_evitar-doble-reserva/spec.md`: cerrar la duda de los
      duplicados históricos (Q1), fijar `MSG_SUBMITTING` (Q3), fijar el comportamiento
      de reintento (Q4) y los contratos de RF-4/RF-5 — **realizada el 2026-10-09 con
      petición explícita de la usuaria («Iniciar las tareas» sobre el task.md aprobado);
      verificada con 118 PASS.**
- [x] Creación de `feature/hu-006` desde `main` (Q5) — **2026-10-09**.
- [ ] Espejo `tests/expected_content.py` + implementación de §1–§5.
- [ ] Tests (§6) y `python -m pytest -q` en verde (118 actuales + ~16 nuevos).
- [ ] Evidencia QA (`qa-hu-006.md`, veredicto PASS) y evidencia visual (capturas CDP
      1280/375, incluido el botón en curso) con la demo antes-durante-después.
- [ ] Commit/Push por fases y actualización de `MEMORY.md`.
- [ ] Aceptación de la HU (checkbox del informe QA).

---

## 8. Secuencia de implementación

0. **Git**: merge de `feature/hu-005` → `main` (HU-005 aceptada 2026-10-09), cierre en
   `qa-hu-005.md` y `MEMORY.md`; crear **`feature/hu-006` desde `main`** (Q5) — solo
   tras aprobar el plan.
1. **Spec primero**: enmienda de la spec 006 — cerrar la duda Q1, fijar
   `MSG_SUBMITTING`, el reintento Q4 y los contratos de RF-4/RF-5 (bloqueante).
2. **Plan**: este `plan.md` (aprobado por la usuaria).
3. **Espejo**: `tests/expected_content.py` con `MSG_SUBMITTING` (junto con la
   enmienda, D11).
4. **Contenido**: `MSG_SUBMITTING` en `consultorio/content/appointment_content.py`.
5. **Servicio**: `create_booking()` endurecido (D3) → `test_double_booking_service.py`.
6. **Capa web**: `data-submitting` en `_render_form()` → `test_double_booking_routes.py`.
7. **Plantilla + JS + CSS**: botón identificable, atributo `data-submitting`, guard de
   submit y estado en curso (§3) → `test_hu_006.py`.
8. **Suite completa**: `python -m pytest -q` → 0 FAIL con los 118 tests previos
   intactos.
9. **Evidencia**: servidor (`python app.py`), demo antes-durante-después con
   capturas CDP 1280/375 → `docs/evidencias/hu-006/` + `qa-hu-006.md` con PASS/FAIL
   por TC.
10. **Cierre**: commits por fase, push, `MEMORY.md` (HU-006) y aceptación de la HU;
    dejar el servidor de revisión en marcha (AGENTS.md).
