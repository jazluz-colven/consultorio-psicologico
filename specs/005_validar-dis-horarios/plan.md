# Plan 005 — Validar disponibilidad de horarios

> Trazabilidad: **HU-005 → Spec 005 (`specs/005_validar-dis-horarios/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs` (Q5).
> Etapa actual: **PLAN APROBADO + ENMIENDA DE LA SPEC APROBADAS Y REALIZADAS**
> (2026-10-09): alcance, decisiones D1–D11, cierre de la duda Q1 y los literales Q3
> aprobados por la usuaria; la spec 005 quedó enmendada (duda cerrada, literales y
> contratos fijados). **Implementación autorizada** según `task.md` (T1–T3 completadas).
> Rama: **`feature/hu-005`** creada desde `main` (`6807afc`: HU-004 aceptada,
> mergeada y sincronizada; 102 tests en verde).

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 005: que el calendario de `/citas`
muestre únicamente horarios reservables, distinga de forma comprensible los estados
disponible/no disponible (por hora y por día), actualice la disponibilidad de forma
perceptible al cambiar de fecha o servicio, informe claramente cuando una fecha no
tenga horarios y refleje la no disponibilidad tras registrar una cita.

**Base existente (HU-004, aceptada)**: la Spec 004 ya entregó `GET /citas/horarios`,
`get_available_hours()`, el datepicker propio con días agendables (lun–vie ≥ hoy,
D19), los bloques Mañana/Tarde, la doble comprobación de horario (`SELECT` + `UNIQUE`,
D9) y el mensaje `MSG_NO_HOURS` (fijado en la spec 004 como «base Spec 005 RF-4»).
La HU-005 es una **evolución de esa misma pantalla**: no reescribe lo que ya funciona
(regla de oro de AGENTS.md), solo añade los estados y la información que la Spec 005
exige y que la delimitación Q10 del plan 004 reservó para esta HU.

**Fuera de alcance**: prevención de concurrencia como objetivo independiente (Spec 006:
el `UNIQUE` y el rechazo en `POST` de HU-004 se conservan intactos como base),
notificaciones posteriores a la reserva (Specs 008/009/010), agenda interna del
psicólogo (Specs 011/012), cancelación de citas, automatización n8n (Spec 007),
cambios de esquema SQLite y dependencias nuevas (constitución #1).

**Sin cambios de modelo de datos**: se reutiliza la tabla `appointments` y el índice
`UNIQUE (service, date, time)` de HU-004 sin migraciones (AGENTS.md: nada de tablas
sin spec; la constitución #5 ya está activa y se respeta).

**Duda abierta de la spec** (debe cerrarse por enmienda antes de codificar):
- **Q1 — regla de disponibilidad**: la spec pregunta si la disponibilidad depende
  exclusivamente de `servicio + fecha + hora` o de reglas adicionales. Propuesta de
  cierre (coherente con D18 del plan 004 y con Spec 006 RF-2): **exclusivamente la
  terna servicio + fecha + hora, sin reglas adicionales**. Detalle en §7.

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Al consultar el calendario se muestran como disponibles únicamente los horarios libres | §2 estados por hora/día; §3 `get_hours_with_status()` + `get_available_days()`; §4 `/citas/horarios` y `/citas/disponibilidad`; §5 D1/D2/D4/D5; §6 TC-005-001/002/003/008/010/013 |
| RF-2 | Un horario ocupado no se puede seleccionar como disponible | §3 radios ocupadas `disabled` sin `name` + rechazo en servidor (base HU-004 D9); §4 contrato semántico; §5 D4; §6 TC-005-004/009/013 |
| RF-3 | Al cambiar de fecha se actualizan los horarios correspondientes exclusivamente a esa fecha | §3 `refreshHours()` + guard de respuestas obsoletas; §4 semántico; §5 D3; §6 TC-005-008/014/015 |
| RF-4 | Si una fecha no tiene horarios disponibles, se informa de forma clara | §2 `MSG_NO_HOURS` (reutilizado, ya fijado); §3 estado vacío + día `is-full`; §4 semántico; §5 D5/D6; §6 TC-005-002/005/006/008 |
| RF-5 | Tras registrar una cita, la reconsulta muestra ese horario como no disponible | §3 consulta viva + selección obsoleta; §4 E2E semántico; §5 D7; §6 TC-005-004/009/013 |
| RF-6 | Distinción comprensible entre horarios disponibles y no disponibles | §2 literales «Ocupado» + leyenda; §3 render de ocupadas + día `is-full` + leyenda textual; §5 D4/D5/D8; §6 TC-005-001/005/009/014/015/016 |
| RNF-1 | Disponibilidad actualizada de forma consistente y perceptible | §3 estado «Consultando disponibilidad…» + guard obsoleto + `aria-live`; §5 D3/D7/D8; §6 TC-005-015 |
| RNF-2 | Los estados no dependen únicamente del color | §2 etiquetas textuales y leyenda; §3 `disabled` + etiqueta «Ocupado» + `aria-label` de día; §5 D4/D5/D8; §6 TC-005-014/016 |
| CL-1 | Fecha sin horarios | §3 estado vacío (RF-4) + día `is-full`; §6 TC-005-005/006/008 |
| CL-2 | Cambio rápido entre fechas | §3 guard de secuencia (D3); §6 TC-005-015 |
| CL-3 | Cambio de servicio con un horario previamente ocupado | §3 refresco de horas **y** días al cambiar servicio (D2/D8); §6 TC-005-007/011 |
| CL-4 | Horario que pasa a ocupado mientras el paciente consulta | §3 selección obsoleta → estado conflicto (D7); rechazo en `POST` (base HU-004); §6 TC-005-004/009/015 |
| CL-5 | Reconsulta de la misma fecha después de una reserva | §3 consulta viva (RF-5); §6 TC-005-004/009/013 |
| Finalización | Tests en verde + demo manual del calendario | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-6][CL-1..CL-5][RNF-1][RNF-2]` — Constitución #3: la lógica de
disponibilidad vive en `services/` + `persistence/`; el JS solo pinta la respuesta del
servidor (mismo criterio que D7 del plan 004). Estructura por capas y patrón de
blueprint ya validados; solo se muestran los **cambios sobre lo existente**:

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   └── appointment_content.py   # + MSG_OCCUPIED_HOUR, MSG_CHECKING_HOURS,
│   │                             #   CALENDAR_LEGEND_FREE, CALENDAR_LEGEND_FULL,
│   │                             #   DAY_LABEL_NO_HOURS  (§2.2)
│   │                             #   [RF-4][RF-6][RNF-1][RNF-2]
│   ├── persistence/
│   │   └── appointments_repository.py  # + list_booked_times_by_date(service,
│   │                                 #   date_from, date_to)  (§3)   [RF-1][RF-5][RF-6]
│   │                                 #   (insert/is_slot_taken/list_booked_times
│   │                                 #    SIN CAMBIOS — base HU-004)
│   ├── services/
│   │   └── appointment_service.py   # + get_hours_with_status(), get_available_days()
│   │                             #   get_available_hours() se conserva como
│   │                             #   envoltura (contrato HU-004 intacto)  [RF-1..RF-6]
│   └── web/
│       └── appointments.py          # GET /citas/horarios devuelve available+occupied;
│                                 #   + GET /citas/disponibilidad (§4)  [RF-1..RF-6]
├── templates/
│   └── appointments/
│       └── index.html               # radios ocupadas disabled + etiqueta «Ocupado»
│                                 #   + leyenda del calendario            [RF-2][RF-6][RNF-2]
├── static/
│   ├── css/main.css                 # + .is-full, .appointment__hour--taken,
│   │                             #   .appointment__calendar-legend (paleta intacta)
│   │                             #   [RF-6][RNF-2]
│   └── js/availability.js           # + estados por día (fetch mensual), guard de
│                                 #   respuestas obsoletas, estado de carga,
│   │                             #   render de ocupadas y deselección obsoleta
│                                 #   [RF-1..RF-6][CL-2][CL-4][RNF-1]
└── tests/
    ├── expected_content.py          # + literales nuevos (espejo único, junto con
    │                             #   la enmienda de la spec)             [RF-4][RF-6]
    ├── test_availability_service.py # get_hours_with_status / get_available_days
    │                             #   [RF-1][RF-2][RF-4][RF-5][RF-6][CL-3][CL-5]
    ├── test_availability_routes.py  # contrato HTTP de /citas/horarios ampliado y
    │                             #   /citas/disponibilidad + E2E reserva→reconsulta
    │                             #   [RF-1..RF-5]
    └── test_hu_005.py               # RNF + estados visuales + regresión HU-004
                                #   [RF-6][RNF-1][RNF-2][todos]
```

Responsabilidades (sin solaparse; solo módulos tocados):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/appointment_content.py` | Declarar los literales nuevos (§2.2) | Contener lógica ni acceder a la BD |
| `persistence/appointments_repository.py` | Leer horas reservadas agrupadas por fecha en un rango | Calcular horas libres (eso es regla de negocio: `services/`) |
| `services/appointment_service.py` | Restar reservadas a `BOOKING_HOURS`, decidir días con horarios libres, validar servicio/mes | Escribir HTML, manejar status codes |
| `web/appointments.py` | Rutas, validación de parámetros, status codes, `jsonify` | Consultar la BD directamente ni calcular disponibilidad |
| `templates/appointments/index.html` | Marco de horas ocupadas (deshabilitadas + etiqueta) y leyenda | Condicionales de negocio |
| `static/js/availability.js` | Pintar estados del servidor, cargar estados del mes, secuenciar peticiones | Decidir qué día/hora está libre (siempre servidor) |

`create_app()` no cambia (blueprint `appointments` ya registrado). `base.html`, `nav.js`
y el esquema SQLite no cambian.

---

## 2. Literales y reglas de disponibilidad

`[RF-1][RF-4][RF-5][RF-6][RNF-1][RNF-2]` — Sin cambios de esquema (§2.1) y con los
literales nuevos de §2.2 **pendientes de fijar en la spec 005 antes de codificar**
(misma regla Q9 del plan 004: textos contractuales, AGENTS.md).

### 2.1 Modelo de datos — sin cambios

La tabla `appointments` y el índice `UNIQUE (service, date, time)` de HU-004 se
reutilizan tal cual (§2.1 del plan 004). La disponibilidad se deriva siempre de la
consulta viva a esa tabla; no existe caché ni estado derivado persistido.

### 2.2 Literales nuevos (`content/appointment_content.py`)

> Propuestos en este plan (Q3, §7); se fijan en la spec 005 en la enmienda previa a la
> implementación. `MSG_NO_HOURS`, `MSG_SLOT_TAKEN`, `MSG_INVALID_PARAMS`,
> `MSG_SELECT_DATE_HINT` y el resto de literales de HU-004 se **reutilizan sin cambio**.

```python
# RF-6: etiqueta de hora ocupada (texto, no solo color)
MSG_OCCUPIED_HOUR: str = "Ocupado"

# RNF-1: estado perceptible mientras se consulta al servidor
MSG_CHECKING_HOURS: str = "Consultando disponibilidad…"

# RF-6/RNF-2: leyenda del calendario (texto junto al color)
CALENDAR_LEGEND_FREE: str = "Con horarios disponibles"
CALENDAR_LEGEND_FULL: str = "Sin horarios disponibles"

# RF-6/RNF-2: sufijo de aria-label/tooltip para días sin horarios libres
DAY_LABEL_NO_HOURS: str = ", sin horarios disponibles"
```

### 2.3 Reglas de disponibilidad (base de cálculo)

| Nivel | Regla |
|---|---|
| Hora | libre = `BOOKING_HOURS` − horas con cita para el mismo `(service, date)` — idéntico a HU-004, ahora visible también como «ocupada» |
| Día | laborable (lun–vie) ≥ hoy con **≥ 1 hora libre** para el `(service, date)` → «con horarios disponibles»; laborable ≥ hoy sin horas libres → «sin horarios» (`is-full`, no seleccionable) |
| No laborable / pasado | fuera del catálogo de días (regla D12 de HU-004, ya aplicada por el datepicker; `/citas/disponibilidad` nunca los incluye) |
| Dependencia | exclusivamente `(service, date, time)` — cierre propuesto de la duda Q1 de la spec, coherente con D18 del plan 004 y Spec 006 RF-2 |

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-6][CL-1..CL-5][RNF-1]`

```text
# --- persistencia (solo lectura nueva) -------------------------------------
FUNCTION list_booked_times_by_date(service, date_from, date_to):
    # SELECT date, time FROM appointments
    #  WHERE service = ? AND date >= ? AND date <= ? ORDER BY date, time
    RETURN { date: [time, …], … }     # solo fechas con al menos una cita

# --- capa de servicio -------------------------------------------------------
FUNCTION get_hours_with_status(service, date, db):
    IF NOT valid_weekday(date): RETURN []            # lun–vie ≥ hoy (HU-004)
    booked = repository.list_booked_times(service, date, db)
    RETURN [(h, h NOT IN booked) FOR h IN BOOKING_HOURS]   # orden del catálogo
    # True = libre, False = ocupada                            [RF-1][RF-2][RF-6]

FUNCTION get_available_hours(service, date, db):     # contrato HU-004 intacto
    RETURN [h FOR (h, free) IN get_hours_with_status(...) IF free]   [RF-1][RF-5]

FUNCTION get_available_days(service, year, month, db):
    booked_by_date = repository.list_booked_times_by_date(
        service, first_day(year, month), last_day(year, month), db)
    days = []
    FOR d IN weekdays(year, month) WHERE d >= today():     # lun–vie ≥ hoy
        IF [h FOR h IN BOOKING_HOURS IF h NOT IN booked_by_date[d]] NO VACÍO:
            days.ADD(d.isoformat())                        [RF-1][RF-4]
    RETURN days

# --- capa web ---------------------------------------------------------------
FUNCTION handle_availability(request):                 # GET /citas/horarios
    service, date = args
    IF service NOT IN SERVICES_CATALOG OR NOT valid_iso(date):
        RETURN jsonify(error="Parámetros inválidos."), 400
    pairs = get_hours_with_status(service, date, db)
    RETURN jsonify(available=[h FOR (h,f) IN pairs IF f],
                   occupied=[h FOR (h,f) IN pairs IF NOT f]), 200
    # clave "available" intacta (HU-004); "occupied" es aditiva (D9)  [RF-1][RF-2][RF-6]

FUNCTION handle_month_days(request):                   # GET /citas/disponibilidad
    service, month = args.get("service"), args.get("month")
    IF service NOT IN SERVICES_CATALOG OR NOT valid_month(month):   # month = YYYY-MM
        RETURN jsonify(error="Parámetros inválidos."), 400
    RETURN jsonify(days=get_available_days(service, year(month), mon(month), db)), 200
    # meses pasados → [] (sin error); sin horizonte máximo (D10)     [RF-1][RF-4]
    # otros métodos → 405

# --- JavaScript availability.js --------------------------------------------
FUNCTION loadDayStates(service, month):
    seq_day = ++seq_day                      # guard también aquí (CL-3/CL-2)
    fetch("/citas/disponibilidad?service=…&month=…")
      .then → si seq_day vigente: dayStates = {iso: true}; renderCalendar()
      .catch → degradar: dayStates = {} (todos los laborables como hasta ahora,
               D12); las horas siguen siendo la fuente de verdad (D8)

FUNCTION renderCalendar():                    # por cada día del mes visible
    IF NOT isBookable(iso):        clase "is-disabled"            (HU-004)
    ELIF dayStates[iso] == false:  clase "is-full" + disabled +
                                   aria-label += ", sin horarios disponibles"   [RF-4][RF-6]
    SINO:                          clase "is-bookable"            (con libres o
                                   aún sin datos)                 [RF-1]

FUNCTION refreshHours():
    IF fecha o servicio sin elegir: pista MSG_SELECT_DATE_HINT (HU-004)
    status.textContent = "Consultando disponibilidad…"             [RNF-1]
    seq = ++seq_hours                     # CL-2: cambio rápido entre fechas
    fetch("/citas/horarios?service=…&date=…")
      .then → IGNORAR si seq != seq_hours (respuesta obsoleta)     [CL-2]
      .then → fillHours(data.available, data.occupied)
              SI hora_seleccionada ∈ occupied:
                  status = MSG_SLOT_TAKEN (estado conflicto)       [CL-4]
              SI hora_seleccionada ∉ available ∪ occupied:
                  se deselecciona (radio ya no existe)             [RF-3][RF-5]

FUNCTION fillHours(available, occupied):       # orden cronológico por bloque
    Mañana/Tarde (corte "12:00", HU-004):
      disponibles → <input type="radio" name="time"> seleccionables   [RF-1]
      ocupadas    → <input type="radio" disabled> SIN name +
                    <span>«Ocupado»</span> (clase .is-taken)         [RF-2][RF-6]
    SI available VACÍO: status = MSG_NO_HOURS (data-empty-message)    [RF-4][CL-1]

INIT:
    loadDayStates(servicio_actual, mes_visible)
    al cambiar mes → loadDayStates(...)        # CL-3
    al cambiar servicio → refreshHours() + loadDayStates(...)   [CL-3]
    refreshHours() inicial (como HU-004)
```

**Nota de regresión**: en la carga inicial de `GET /citas` con BD vacía se siguen
emit exactamente 14 radios `name="time"` (las ocupadas van sin `name` y `disabled`),
por lo que TC-004-028 y TC-004-015 siguen verdes sin tocarlos.

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF-ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor (BD existente de HU-004) | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `python -m pytest -q` | Suite completa (102 actuales + ~16 nuevos) | `N passed` | `0` / `1` |
| `python -m pytest tests/test_hu_005.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-1..RF-6]`

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `GET` | `/citas/horarios?service=…&date=…` | JSON `{"available": ["08:00", …], "occupied": ["09:00", …]}` (ambas claves siempre; vacías si aplica; finde/pasada → ambas `[]`) | **200** |
| `GET` | `/citas/horarios` con parámetros ausentes o inválidos | JSON `{"error": "Parámetros inválidos."}` (literal sin cambio) | **400** |
| `GET` | `/citas/disponibilidad?service=…&month=YYYY-MM` | JSON `{"days": ["2026-10-13", …]}` (solo lun–vie ≥ hoy con ≥ 1 hora libre; mes vacío/pasado → `[]`) | **200** |
| `GET` | `/citas/disponibilidad` con servicio/mes ausentes o inválidos | JSON `{"error": "Parámetros inválidos."}` | **400** |
| `POST/PUT/DELETE` | `/citas/disponibilidad` | `errors/405.html` | **405** |
| `GET` | `/citas` | formulario con leyenda del calendario y, si hay citas, horas ocupadas marcadas «Ocupado» | **200** |
| resto rutas (`/citas` POST/confirmada, `/`, `/nosotros`, `/servicios`, `/buscar…`) | sin cambios (regresión HU-001/002/003/004/016) | 200/303/404/405 como hasta ahora |

**Contrato semántico (lo que verifican los tests):**

```text
[RF-1] GET /citas/horarios → "available" solo contiene horas libres y
       "occupied" solo las ocupadas para (service, date)   → absent ⇒ FAIL
[RF-1] GET /citas/disponibilidad → solo días laborables ≥ hoy
       con ≥ 1 hora libre del servicio elegido             → absent ⇒ FAIL
[RF-2] hora ocupada → en el HTML como radio disabled SIN
       name y con texto «Ocupado»; jamás seleccionable     → absent ⇒ FAIL
[RF-3] tras cambiar la fecha (fetch), los radios mostrados
       corresponden solo a esa fecha                       → absent ⇒ FAIL
[RF-4] fecha con 0 libres → status «No hay horarios disponibles
       para esta fecha.» + día marcado "is-full"           → absent ⇒ FAIL
[RF-5] registrar cita → GET /citas/horarios devuelve esa
       hora en "occupied" y no en "available"              → absent ⇒ FAIL
[RF-6] día con libres "is-bookable"; día laborable lleno
       "is-full" + disabled + aria-label con «sin horarios
       disponibles»; leyenda textual visible junto al
       calendario (no solo color)                          → absent ⇒ FAIL
[RNF-1] durante el fetch, #hours-status muestra «Consultando
       disponibilidad…»; respuestas obsoletas ignoradas     → absent ⇒ FAIL
[RNF-2] cada estado (ocupada, día lleno) tiene etiqueta de
       texto además de color                               → absent ⇒ FAIL
[regresión] TC-004-021/028 y la suite HU-004 siguen verdes
       (contrato "available" intacto; 14 radios name="time"
       en carga inicial)                                   → presente ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Endpoint nuevo `GET /citas/disponibilidad?service=…&month=YYYY-MM`** que devuelve los días del mes con ≥ 1 hora libre | El datepicker navega meses y cambia de servicio; un solo JSON mensual evita N peticiones por día, la lógica queda en `services/` (constitución #3) y es testeable con `test_client` (patrón del proyecto: sin tests E2E de JS) | *Una petición por día visible*: ~31 fetches por vista. *Precargar en el HTML de `/citas`*: no cubre cambio de mes ni de servicio sin recarga. *Estado en BD*: caché sin requisito (AGENTS: nada por conveniencia) | RF-1, RF-4, CL-3 |
| D2 | **La disponibilidad depende exclusivamente de `(service, date, time)`** (cierre propuesto de la duda Q1 de la spec) | Coherente con D18 del plan 004, con el `UNIQUE (service, date, time)` vigente y con Spec 006 RF-2 («la misma combinación de servicio, fecha y hora»); la usuaria ya aprobó esa regla en HU-004 | *Agenda global por fecha*: impediría dos servicios a la misma hora, contradiciendo 006 RF-2. *Reglas adicionales (anticipación máxima, cupos por día)*: ninguna spec las pide | RF-1, RF-2, CL-3 |
| D3 | **Guard de respuestas obsoletas con contador secuencial** (`seq_hours` / `seq_day`) en `availability.js` | Cubre «cambio rápido entre fechas» (CL-2): solo la última petición en curso aplica; vanilla sin dependencias (constitución #1); patrón simple y verificable por inspección estática en los tests de la casa | *Sin guard*: dos fetches en vuelo pueden pintar la hora de la fecha anterior (viola RF-3 y el «mensajes visibles = estado real» de AGENTS.md). *AbortController*: válido pero más verboso sin ganar pruebas automatizadas | RF-3, CL-2, RNF-1 |
| D4 | **Las horas ocupadas se muestran deshabilitadas con etiqueta textual «Ocupado»** (radio `disabled` **sin** `name`, dentro del mismo bloque Mañana/Tarde, orden cronológico) | RF-6 exige distinción comprensible entre disponible y no disponible; omitirlas (comportamiento HU-004) no informa *por qué* falta una hora; el texto + `disabled` cumple RNF-2 (no solo color); sin `name` no pueden enviarse ni alteran el recuento de TC-004-028 | *Seguir omitiéndolas*: incumple RF-6. *Solo atenuar por color*: incumple RNF-2. *Checkbox de estado*: introduce un estado nuevo no pedido (la cita sigue «Pendiente») | RF-2, RF-6, RNF-2 |
| D5 | **Estado por día binario: `is-bookable` (con libres) vs `is-full` (laborable sin libres) vs `is-disabled` (finde/pasado)**, con leyenda textual visible | Delimitación Q10 del plan 004: HU-005 conserva el «estado por día»; binario es lo que la spec pide («horarios libres» vs nada libre); la leyenda (texto + color) cumple RNF-2; `is-full` es una clase nueva, las de HU-004 se conservan (regresión TC-004-028) | *Escala de semáforo (lleno/parcial/libre)*: complejidad sin requisito. *Solo color por día*: incumple RNF-2. *Renombrar `is-bookable`*: rompe TC-004-028 sin necesidad | RF-1, RF-4, RF-6, RNF-2 |
| D6 | **`MSG_NO_HOURS` reutilizado como estado vacío de RF-4/CL-1** (bloques sin radios + `#hours-status`), sin literales nuevos para ese estado | El literal ya fue aprobado y fijado en la spec 004 expresamente como «base Spec 005 RF-4»; el JS ya lo aplica vía `data-empty-message`; los tests de la HU-005 lo asertan | *Nuevo mensaje*: duplicaría copy contractual sin necesidad | RF-4, CL-1 |
| D7 | **Selección obsoleta tras refresco**: si la hora elegida pasa a «occupied» → estado de conflicto con `MSG_SLOT_TAKEN` en `#hours-status`; si desaparece por otra razón → se deselecciona sin error; el rechazo definitivo sigue siendo el del servidor en `POST` (D9 de HU-004, sin cambios) | Caso límite «horario que pasa a ocupado mientras el paciente consulta» y RF-5: los mensajes visibles corresponden al estado real del backend (AGENTS.md); el servidor sigue siendo la única autoridad (constitución #5) | *Mantener el radio seleccionado*: permitiría enviar un horario ocupado. *Bloquear el formulario*: comportamiento de HU-006 sin spec | RF-2, RF-5, CL-4, CL-5, RNF-1 |
| D8 | **Actualización perceptible**: «Consultando disponibilidad…» durante el fetch (con `aria-live`, ya presente); fallo del fetch de días del mes degrada al comportamiento D12 sin bloquear | RNF-1 («consistente y perceptible») y estados de AGENTS.md (procesando → éxito/conflicto); las horas del servidor siguen siendo la fuente de verdad, nunca el JS decide | *Sin indicador*: el usuario no percibe la actualización (RNF-1). *Pantalla de carga completa*: desproporcionado para un select | RNF-1, RF-3 |
| D9 | **El JSON de `/citas/horarios` gana la clave `occupied` (aditiva)** y TC-004-021 se enmienda en el mismo PR para asertar ambas claves | RF-6 necesita que el servidor distinga ocupadas; mantener dos endpoints para la misma fecha crearía una ventana de incoherencia; la aserción se **refuerza** (dos claves), no se relaja (pytest-qa §1.2); la spec 005 fija el contrato en la enmienda | *Seguir devolviendo solo `available` y calcular ocupadas en el JS*: duplicaría la regla de negocio fuera de `services/` (constitución #3). *Endpoint paralelo*: incoherencia potencial entre respuestas | RF-2, RF-6 |
| D10 | **`/citas/disponibilidad` valida `service ∈ SERVICES_CATALOG` y `month` con formato `YYYY-MM` real; meses pasados o sin libres → `[]` (sin error)**; sin horizonte máximo de anticipación | Mismo patrón que `/citas/horarios` (400 solo por parámetros inválidos; los estados vacíos son estados de usuario, D3 del plan 016); ninguna spec pide límite de anticipación (D12 del plan 004 lo descartó) | *404 para meses sin citas*: confundiría «sin datos» con «recurso inexistente. *Límite de N meses*: regla no solicitada | RF-1, RF-4 |
| D11 | **Identificadores en inglés, mensajes en español; espejo único en `expected_content.py` actualizado junto con la enmienda de la spec** | Constitución #6 y AGENTS.md (textos contractuales: spec y espejo cambian juntos, patrón D15 del plan 004) | *Literales solo en código*: rompe la trazabilidad spec → test | todos |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` (suite) · `python -m pytest tests/test_hu_005.py -v`
(HU). Fixtures de `conftest.py` **sin cambios** (`app`, `client` con BD temporal por
test de HU-004). Arrange/Act/Assert, sin dependencia del orden. Fechas relativas
calculadas en cada prueba (lunes laborable futuro, mes vivo), sin estado compartido.
`tests/expected_content.py` concentra los literales nuevos (espejo único, D11).

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-005-001 | `test_availability_service.py` | `get_hours_with_status()` sin citas → los 14 slots con `free=True`, en orden de `BOOKING_HOURS` | RF-1, RF-6 |
| TC-005-002 | `test_availability_service.py` | Con una cita previa en esa terna → esa hora `free=False` y las 13 restantes `True`; `get_available_hours()` devuelve las 13 (contrato HU-004 intacto) | RF-1, RF-2, RF-5 |
| TC-005-003 | `test_availability_service.py` | `get_available_days()` sin citas → todos los laborables ≥ hoy del mes, ordenados; nunca incluye sábados, domingos ni fechas pasadas | RF-1 |
| TC-005-004 | `test_availability_service.py` | **CL-5:** tras `create_booking()`, el día sigue en `get_available_days()` si queda ≥ 1 libre y desaparece si se ocupan los 14; la hora reservada queda `free=False` | RF-5, CL-5 |
| TC-005-005 | `test_availability_service.py` | **CL-3:** mismo mes/día con los 14 slots ocupados en el servicio A → el día no aparece para A pero sí para el servicio B (disponibilidad por terna, D2) | RF-1, CL-3 |
| TC-005-006 | `test_availability_service.py` | **CL-1:** mes en el que todos los laborables ≥ hoy están llenos → `get_available_days()` = `[]`; finde/pasada → `[]` también en `get_hours_with_status()` | RF-4, CL-1 |
| TC-005-007 | `test_availability_service.py` | Fecha/hora ocupada en servicio A: `get_hours_with_status(B, …)` la devuelve libre (regla D2 verificada en la capa de servicio) | RF-1, CL-3 |
| TC-005-008 | `test_availability_routes.py` | `GET /citas/horarios` → **200** con `available` = 14 y `occupied` = `[]`; con insert previo → esa hora pasa a `occupied`; finde → ambas `[]` | RF-1, RF-3, RF-4 |
| TC-005-009 | `test_availability_routes.py` | **RF-5/CL-5:** `POST /citas` válido → **303**; `GET /citas/horarios` de esa terna devuelve la hora solo en `occupied`; hora en otra fecha sigue libre | RF-2, RF-5, CL-5 |
| TC-005-010 | `test_availability_routes.py` | `GET /citas/disponibilidad?service=…&month=YYYY-MM` → **200** `{"days": […]}` con laborables ≥ hoy; mes siguiente incluido si tiene libres | RF-1 |
| TC-005-011 | `test_availability_routes.py` | **CL-3:** `GET /citas/disponibilidad` para servicio A (día lleno) no incluye ese día; para servicio B sí | RF-1, CL-3 |
| TC-005-012 | `test_availability_routes.py` | **400:** servicio inexistente, `month` ausente, `month=2026-13`, `month=banana` → `{"error": "Parámetros inválidos."}`; **405:** `POST /citas/disponibilidad` | RF-1 |
| TC-005-013 | `test_availability_routes.py` | **E2E servidor:** reserva completa → redirect 303 → reconsulta `/citas` y `/citas/horarios`: la hora reservada no figura como disponible en ninguna petición posterior | RF-1, RF-2, RF-5, finalización |
| TC-005-014 | `test_hu_005.py` | Plantilla `/citas`: leyenda del calendario con `CALENDAR_LEGEND_FREE` y `CALENDAR_LEGEND_FULL` visibles; `data-*` con los literales nuevos; `main.css` con `.is-full`, `.appointment__hour--taken` y `.appointment__calendar-legend`; colores ⊆ paleta; párrafos `justify` + `hyphens: none` | RF-6, RNF-2 |
| TC-005-015 | `test_hu_005.py` | `availability.js` (inspección estática, patrón TC-004-028): tokens `/citas/disponibilidad`, `is-full`, «Ocupado»/literal vía atributo, contador de secuencia (`seq`), condición de guard, `Consultando`/atributo de carga y deselección; sin imports de librerías externas | RF-3, RF-6, CL-2, CL-4, RNF-1 |
| TC-005-016 | `test_hu_005.py` | **Regresión:** HTML de `/citas` con BD vacía contiene exactamente 14 `name="time"` y 0 radios `disabled` de horas; `python -m pytest -q` completo → 0 FAIL con los 102 tests previos intactos (TC-004-021 enmendado a dos claves, resto sin tocar) | RF-6, regresión HU-001/002/003/004/016 |

### 6.2 Pirámide

1. **Unitarias** — `appointment_service` (`get_hours_with_status`,
   `get_available_days`, envoltura `get_available_hours`) y
   `appointments_repository.list_booked_times_by_date` sin HTTP.
   `[RF-1][RF-2][RF-4][RF-5][RF-6][CL-1][CL-3][CL-5]`
2. **Integración HTTP** — `test_client` sobre `/citas/horarios` (contrato ampliado),
   `/citas/disponibilidad` y E2E reserva → reconsulta. `[RF-1..RF-5]`
3. **Regresión** — `python -m pytest -q` completo: los **102 tests actuales**
   (HU-001/002/003/016/004) deben seguir verdes; única enmienda deliberada:
   TC-004-021 pasa de `{"available": …}` a asertar `available` **y** `occupied`
   (D9, refuerzo). `[todos]`
4. **Visual/manual** — servidor `python app.py`: capturas CDP 1280 y 375 de `/citas`
   (leyenda, día `is-full` si hay datos, hora «Ocupado» si hay datos) + recorrido:
   cambiar fecha (rápido), cambiar servicio, registrar cita y volver, fecha llena →
   mensaje RF-4 (exigido por los criterios de finalización). `[RF-6][RNF-1][RNF-2]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar (pytest-qa §1.2).
- Pruebas deterministas: fechas relativas calculadas en la prueba; BD temporal por
  fixture; sin orden accidental.

```text
HU: HU-005
Caso: TC-005-009
Comando: python -m pytest tests/test_availability_routes.py -v
Resultado: PASS
Rama: feature/hu-005
Commit: <hash>
Evidencia visual: docs/evidencias/hu-005/escritorio-1280.png, movil-375.png
```

- Informe QA: `docs/evidencias/hu-005/qa-hu-005.md` con PASS/FAIL por TC y checkbox de
  aceptación; veredicto `PASS` / `PARCIAL` / `FAIL` (skill `pytest-qa`).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Duda abierta de la spec: ¿la disponibilidad depende solo de servicio + fecha + hora o hay reglas adicionales? | **Exclusivamente la terna servicio + fecha + hora, sin reglas adicionales** (D2; coherente con D18 del plan 004 y Spec 006 RF-2, ya aprobadas por la usuaria). **Aprobada y fijada en la spec 005 (enmienda 2026-10-09).** |
| Q2 | Horas ocupadas: ¿se muestran marcadas o se omiten como hasta ahora? | **Se muestran deshabilitadas con «Ocupado»** (D4) — lo exige RF-6 y RNF-2. **Aprobada 2026-10-09.** |
| Q3 | Literales nuevos (ocupado, carga, leyenda, sufijo de día) | **Los 5 literales de §2.2, aprobados el 2026-10-09 y fijados en la spec 005** (sección «Literales y contrato»). |
| Q4 | Rama de trabajo | **`feature/hu-005` desde `main` (`6807afc`)**, tras aceptación y merge de HU-004. **Creada 2026-10-09.** |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Aprobación de este `plan.md` (alcance, D1–D11 y literales Q3) por la usuaria
      — **2026-10-09**.
- [x] Enmienda de `specs/005_validar-dis-horarios/spec.md`: cerrar la duda Q1,
      fijar los literales de §2.2 y el contrato de `/citas/horarios`
      (`available` + `occupied`) y de `/citas/disponibilidad` — **realizada el
      2026-10-09 con aprobación y petición explícita de la usuaria**.
- [x] Creación de `feature/hu-005` desde `main` (Q4) — **2026-10-09**.
- [ ] Implementar módulos, JS, plantilla y CSS (§1–§5).
- [ ] Tests (§6) y `python -m pytest -q` en verde (102 actuales + ~16 nuevos).
- [ ] Evidencia QA (`qa-hu-005.md`, veredicto PASS) y evidencia visual
      (`escritorio-1280.png`, `movil-375.png`) con demo sobre el servidor
      (cambio de fecha/servicio, reserva + reconsulta, fecha sin horarios).
- [ ] Commit/Push por fases y actualización de `MEMORY.md`.
- [ ] Aceptación de la HU (checkbox del informe QA).

---

## 8. Secuencia de implementación

0. **Git**: verificar `main` (`6807afc`) sincronizada; crear `feature/hu-005` desde
   `main` (Q4) — solo tras aprobar el plan.
1. **Spec primero**: enmienda de la spec 005 — cerrar la duda Q1 (§7.1), fijar los
   literales de §2.2 y los contratos HTTP de §4.2 (bloqueante, petición explícita).
2. **Plan**: este `plan.md` (aprobado por la usuaria).
3. **Espejo**: `tests/expected_content.py` con los literales nuevos (junto con la
   enmienda, D11).
4. **Persistencia**: `list_booked_times_by_date()` en `appointments_repository.py`
   (solo lectura; esquema intacto).
5. **Servicio**: `get_hours_with_status()` y `get_available_days()`
   (`get_available_hours()` pasa a envoltura) → `test_availability_service.py`.
6. **Capa web**: `/citas/horarios` con `occupied` (+ enmienda de TC-004-021, D9) y
   `GET /citas/disponibilidad` → `test_availability_routes.py`.
7. **Plantilla**: radios ocupadas `disabled` sin `name` + etiqueta «Ocupado» +
   leyenda del calendario en `appointments/index.html`.
8. **JS**: `availability.js` — `loadDayStates()`, estados `is-full`, guard de
   secuencia, estado de carga y deselección obsoleta (§3).
9. **CSS**: `.is-full`, `.appointment__hour--taken`, `.appointment__calendar-legend`
   en `main.css` (mobile-first, paleta intacta, párrafos justificados sin guiones).
10. **Tests de HU**: `test_hu_005.py` (RNF, regresión).
11. **Suite completa**: `python -m pytest -q` → 0 FAIL con los 102 tests previos
    intactos (salvo la enmienda reforzada D9).
12. **Evidencia**: servidor (`python app.py`), capturas CDP 1280/375 →
    `docs/evidencias/hu-005/` + `qa-hu-005.md` con PASS/FAIL por TC.
13. **Cierre**: commits por fase, push, `MEMORY.md` (HU-005) y aceptación de la HU;
    dejar el servidor de revisión en marcha (AGENTS.md).
