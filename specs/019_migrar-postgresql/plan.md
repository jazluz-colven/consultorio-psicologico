# Plan 019 — Migración a PostgreSQL/Neon

> Trazabilidad: **Spec 019 (`specs/019_migrar-postgresql/spec.md`) → este plan →
> `tasks.md` → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (#1 sin ORM ni dependencias sin
> justificación y aprobación; #5 integridad en el punto de persistencia).
> Ruta canónica de las specs: `/specs`.
>
> **Estado: Aprobado por la usuaria el 2026-11-08.**
>
> La **Spec 019 fue aprobada por la usuaria el 2026-11-07**. Las **enmiendas
> coordinadas de las Specs 004/005/006/010 fueron aprobadas por la usuaria el
> 2026-11-08**. La usuaria **aprobó este plan y `tasks.md` el 2026-11-08** y
> **autorizó iniciar la Entrega A con la tarea T1**. Las tareas T2–T18 y las
> entregas B/C no están autorizadas todavía.
>
> **Baseline real (2026-11-08): 320 PASS / 0 FAIL en SQLite.**
> El spike de 2026-11 obtuvo **307 PASS con PostgreSQL** antes de que HU-018
> existiera. La **suite de paridad** debe cubrir **todos los criterios de las
> Specs 004–018**, incluidos los 18 casos de HU-018, ejecutados contra
> PostgreSQL. El baseline es 320, pero el conteo final puede variar por la
> reubicación de `TC-010-014` a la verificación de rollback (T15) y por
> renombrados; se reportará el **número real verificado**, sin declarar cifras
> no ejecutadas. **No se afirma aquí una cifra PASS de PostgreSQL**: el
> resultado real se registrará en la evidencia de la fase de implementación. El
> spike no verificó Neon, Render, TLS ni el pool de conexiones
> (`docs/spikes/postgresql-evaluacion-2026-11.md` §9).

---

## 0. Alcance y cobertura

La Spec 019 es un **habilitador técnico**, no una funcionalidad de usuario
nueva. No introduce pantallas, roles ni flujos: traslada la persistencia de
citas y eventos de automatización a PostgreSQL gestionado (Neon Free) y
preserva el comportamiento aprobado de las Specs 004–018.

**Qué cambia**

- El almacenamiento deja de ser un fichero SQLite efímero en Render y pasa a
  una base PostgreSQL gestionada, con TLS y credenciales por entorno.
- La capa de persistencia, el DDL y los tests se adaptan al dialecto PostgreSQL.
- Se añade el literal contractual de indisponibilidad de persistencia
  `MSG_PERSISTENCE_UNAVAILABLE`, ya fijado en las Specs 004/005 (enmienda
  aprobada el 2026-11-08), con su espejo en `tests/expected_content.py`.
- Se documenta y prueba un **rollback temporal** a SQLite mediante interruptor
  de entorno, que se retira tras la aceptación.

**Qué no cambia**

- Las firmas y la lógica de negocio de reserva, disponibilidad, cancelación,
  reprogramación, eventos y correos (Specs 004–018).
- Los literales contractuales vigentes, salvo el literal nuevo de
  indisponibilidad aprobado.
- La paleta, la tipografía y las reglas de texto del proyecto.
- El contrato PRG `POST /citas → 303 → /citas/confirmada/<id>`.
- El comportamiento observable de los flujos 017/018, que siguen delegando en
  el servicio centralizado de la Spec 010.

**Fuera de alcance inmediato** (detalle en §10): acceso/agenda (Specs 011/012),
compliance, migración de datos históricos, backups automáticos, reintentos o
colas, rediseño de UX y ORM/herramientas de migración externas.

### 0.1 Cobertura resumida

| Bloque | Requisitos | Diseño |
|---|---|---|
| Persistencia y durabilidad | RF-1..RF-3 | D1, D2, D4, D11, D14 |
| Paridad 004–018 | RF-4..RF-9 | D5, D8, D13 |
| Integridad en el motor | RF-10..RF-14 | D4, D5, D8 |
| Configuración y conexiones | RF-15..RF-17 | D2, D3 |
| Rollback | RF-18, RF-19 | D10, D16 |
| Indisponibilidad | RF-20..RF-23 | D6, D12, D14 |
| Esquema | RF-24..RF-27 | D4 |
| Desarrollo y pruebas | RF-28, RF-29 | D9 |
| Fechas y horas | RF-30 | D7 |

---

## 1. Arquitectura y módulos afectados

La arquitectura se mantiene: Flask + capas `web/` → `services/` →
`persistence/`, sin ORM. Se sustituye el motor y se adapta la frontera de
persistencia. Los cambios se concentran en los módulos siguientes.

```text
Consultorio_Carolina/
├── consultorio/
│   ├── config.py                         # DATABASE_URL, PERSISTENCE_BACKEND,
│   │                                     # DATABASE_PATH solo rollback,
│   │                                     # límites y timeouts; sin secretos
│   ├── __init__.py                       # create_app: Database + init_db
│   │                                     # tolerante a BD no disponible
│   ├── errors.py                         # + PersistenceUnavailable -> 503
│   ├── persistence/
│   │   ├── database.py                   # DatabaseTarget/Database, conexión
│   │   │                                 # por petición/operación, transacción,
│   │   │                                 # DDL PostgreSQL y SQLite de rollback,
│   │   │                                 # errores de dominio y lazy init
│   │   ├── appointments_repository.py    # %s, RETURNING id, índice parcial,
│   │   │                                 # transición + evento atómico
│   │   └── automation_events_repository.py # UNIQUE(event_id), UTC, rowcount
│   ├── services/
│   │   ├── appointment_service.py        # mapeo UniqueViolation -> SLOT_TAKEN;
│   │   │                                 # PersistenceUnavailable no es SLOT_TAKEN
│   │   └── cancellation_flow_service.py  # sin cambios de lógica; usa el
│   │                                     # servicio centralizado de la 010
│   ├── content/
│   │   └── appointment_content.py        # + MSG_PERSISTENCE_UNAVAILABLE
│   └── web/
│       ├── appointments.py               # target de BD; sin lógica nueva
│       ├── cancellation.py               # target de BD; sin lógica nueva
│       └── admin.py                      # target de BD; sin lógica nueva
├── templates/errors/persistence_unavailable.html  # nuevo (503)
├── static/js/availability.js             # manejo de 503 sin marcar «Ocupado»
├── tests/
│   ├── conftest.py                       # fixtures PostgreSQL y esquema aislado
│   ├── expected_content.py               # espejo del literal nuevo
│   ├── test_appointment_persistence.py   # catálogos PostgreSQL
│   ├── test_hu_006.py / test_hu_007.py   # introspección PostgreSQL
│   ├── test_hu_010.py                    # idempotencia PostgreSQL
│   ├── test_rollback_sqlite.py           # TC-010-014: rollback, fuera de paridad
│   ├── test_double_booking_service.py    # concurrencia real en PostgreSQL
│   ├── test_cancellation_service.py      # atomicidad y eventos en PostgreSQL
│   ├── test_availability_service.py      # disponibilidad en PostgreSQL
│   ├── test_hu_018.py                    # flujos 018 sobre PostgreSQL
│   ├── test_pg_schema.py                 # nuevo: DDL, idempotencia, catálogos
│   ├── test_pg_persistence.py            # nuevo: repositorios y dialecto
│   ├── test_pg_resilience.py             # nuevo: conexiones, errores, cold start
│   └── test_hu_019.py                    # nuevo: flujos y espejo contractual
├── requirements.txt                      # + psycopg[binary]==3.3.8
├── render.yaml                           # DATABASE_URL, PERSISTENCE_BACKEND;
│                                         # retirada de DATABASE_PATH
└── docs/
    ├── operaciones/postgresql.md         # nuevo: config, despliegue, rollback
    └── evidencias/hu-019/                # nuevo: QA, E2E, despliegue, rollback
```

### 1.1 Responsabilidades

| Módulo | Responsabilidad | No debe hacer |
|---|---|---|
| `config.py` | Leer y validar `DATABASE_URL`, backend, límites y timeouts; no exponer secretos | Contener lógica de negocio ni conectar a la BD |
| `persistence/database.py` | Abrir/reutilizar/cerrar conexiones, transacciones, DDL idempotente, traducir errores del driver a errores de dominio | Contener reglas de reserva o de notificación |
| `appointments_repository.py` | SQL de citas, unicidad de horario, transición + evento pendiente en una transacción | Decidir mensajes de usuario ni códigos HTTP |
| `automation_events_repository.py` | SQL de eventos, deduplicación, estados y marcas UTC | Publicar webhooks |
| `appointment_service.py` | Orquestar reserva/cancelación y mapear conflictos de unicidad | Capturar errores de indisponibilidad como conflicto de horario |
| `cancellation_flow_service.py` | Verificación y delegación en el servicio 010 | Implementar persistencia propia |
| `web/*` | Rutas, códigos HTTP y entrega de literales | Consultar la BD directamente ni contener reglas |
| `errors.py` | Traducir `PersistenceUnavailable` a 503 con el literal aprobado | Mezclar indisponibilidad con 404/409 |
| `availability.js` | Mostrar el estado real del backend; no marcar horas ocupadas ante 503 | Decidir disponibilidad |

---

## 2. Decisiones de diseño

### D1 — Driver `psycopg` 3, sin ORM

**Decisión:** usar `psycopg` 3 en la versión **3.3.8** (`psycopg[binary]==3.3.8`
en `requirements.txt`), sin ORM ni capa de emulación de SQLite. Es la versión
verificada por el spike con PostgreSQL 16.15 y Python 3.14.8; para Python
3.12.7 existen wheels de `psycopg[binary]`, pero su ejecución en Render queda
como verificación de despliegue (RNF-3, riesgo R-01).

**Justificación:** Constitución #1 (dependencia mínima justificada) y RNF-8.
El spike demostró que el SQL del proyecto funciona sobre PostgreSQL con
`psycopg`; no hace falta un ORM ni una herramienta de migraciones para el
alcance aprobado. La integridad se mantiene en el motor (índice parcial,
`UNIQUE(event_id)`).

**Alternativas descartadas:**

- `psycopg2`: no es la versión verificada por el spike y añade otra API.
- `asyncpg`: cambiaría el modelo síncrono de Flask y los servicios.
- SQLAlchemy u otro ORM: prohibido por la constitución #1 y por RF-27.
- Reutilizar el `pg_adapter.py` del spike: era un emulador desechable de
  SQLite (511 líneas) y el propio spike recomienda no usarlo como solución
  final.

**RF:** RF-1, RF-27; RNF-8.

### D2 — Configuración por entorno, TLS y sin secretos

**Decisión:**

- `DATABASE_URL`: DSN de PostgreSQL. En entornos no locales debe incluir
  `sslmode=require` (o `verify-ca`/`verify-full`); si falta, la configuración
  falla al arrancar. En local (host `localhost`, `127.0.0.1` o `::1`) se admite
  `sslmode=disable` para el PostgreSQL de Docker.
- `PERSISTENCE_BACKEND`: `postgres` (valor por defecto) o `sqlite` (solo
  rollback temporal). Un valor distinto es un error de configuración.
- `DATABASE_PATH`: se lee **solo** cuando `PERSISTENCE_BACKEND=sqlite`; no es
  una alternativa permanente ni un modo de desarrollo.
- `DATABASE_MAX_CONNECTIONS` (por defecto 5 por proceso),
  `DATABASE_CONNECT_TIMEOUT` (por defecto 10 s),
  `DATABASE_ACQUIRE_TIMEOUT` (por defecto 5 s) y
  `DATABASE_STATEMENT_TIMEOUT_MS` (por defecto 15000 ms) como protecciones
  operativas, no como umbrales de negocio.
- Ningún secreto, DSN con contraseña ni credencial se guarda en el repositorio,
  la documentación ni las pruebas. `render.yaml` declara `DATABASE_URL` con
  `sync: false` para que se configure como secreto en Render.

**Justificación:** RF-15, RF-16, RF-17, RNF-6. El valor por defecto
`postgres` evita que un despliegue sin configuración vuelva silenciosamente a
SQLite y divida los datos. Si falta `DATABASE_URL`, la aplicación **arranca**
(RF-22) pero las rutas que necesitan persistencia responden con
indisponibilidad (RF-20/21); no se hace fallback automático.

**Alternativas descartadas:**

- Mantener `DATABASE_PATH` como configuración principal: perpetúa el
  almacenamiento efímero.
- Fallback automático a SQLite si PostgreSQL falla: ocultaría la caída y
  produciría pérdida silenciosa de datos.
- Guardar el DSN en `render.yaml` o en documentación: viola RNF-6.

**RF:** RF-15, RF-16, RF-17, RF-18, RF-22; RNF-6.

### D3 — Conexiones: una por petición/operación, reutilizada y cerrada; sin conexiones globales

**Decisión:** `Database` encapsula el destino y la gestión de conexiones:

- En una petición web, se abre **como máximo una conexión** y se reutiliza en
  todas las operaciones de esa petición; se cierra en `teardown_request`.
- Fuera de una petición (servicios invocados desde tests o scripts), cada
  operación abre y cierra su conexión; una transacción comparte la conexión
  durante su ámbito.
- No hay conexiones globales por worker ni conexiones creadas al importar el
  módulo.
- Un `BoundedSemaphore` por proceso limita las conexiones simultáneas a
  `DATABASE_MAX_CONNECTIONS`. Si no se adquiere un permiso dentro de
  `DATABASE_ACQUIRE_TIMEOUT`, se lanza `PersistenceUnavailable` (no un 409 ni
  un «Ocupado»).
- El DSN incluye `connect_timeout`, `application_name=consultorio-web` y, si se
  configura, `statement_timeout`; no se registra el DSN ni la contraseña.
- Neon puede dormir el compute (scale-to-zero). La conexión cerrada o rota se
  traduce a `PersistenceUnavailable`; la **siguiente petición** abre una
  conexión nueva. No se reintenta dentro de la misma petición para no duplicar
  escrituras.

**Justificación:** RF-17, CL-9, CL-11. El spike midió 96 s en
`test_availability_service.py` porque cada llamada abría una conexión nueva;
la reutilización por petición reduce ese coste sin añadir `psycopg_pool`.
`psycopg_pool` sería una dependencia adicional; el semáforo de la stdlib cubre
el límite y el comportamiento ante saturación con menos superficie.

**Alternativas descartadas:**

- `psycopg_pool.ConnectionPool`: justificable, pero añade una dependencia y
  configuración que el MVP no necesita; queda como alternativa si la carga
  real lo exige.
- Conexión global por worker: no es segura ante concurrencia y complica el
  cierre y la recuperación tras un fallo.
- Abrir una conexión por sentencia: reproduce el problema de latencia del
  spike.

**RF:** RF-17, RF-22, RF-23; RNF-2; CL-9, CL-11.

### D4 — DDL idempotente sin ORM, con bloqueo de arranque concurrente

**Decisión:** el esquema se crea y evoluciona con SQL explícito en
`persistence/database.py`:

- `CREATE TABLE IF NOT EXISTS` para `appointments` y `automation_events`.
- `CREATE UNIQUE INDEX IF NOT EXISTS ux_appointments_slot_open ON
  appointments(service, date, time) WHERE status <> 'cancelled'`.
- `UNIQUE(event_id)` en `automation_events` (restricción de tabla).
- Tabla mínima `schema_migrations (version INTEGER PRIMARY KEY, applied_at
  TEXT NOT NULL DEFAULT ...)` para registrar pasos aplicados y soportar
  cambios futuros sin pasos manuales no documentados (RF-26).
- Todo el DDL se ejecuta dentro de una transacción precedida de
  `SELECT pg_advisory_xact_lock(719019)`; dos instancias que arranquen a la vez
  se serializan y la segunda ve los objetos ya creados (CL-7).
- Los pasos son idempotentes y aditivos. Un cambio destructivo exigirá una
  decisión documentada y su propia estrategia de respaldo; no se incluye en
  esta migración.
- La ruta SQLite de rollback conserva su DDL y su índice parcial, con
  `created_at` en UTC (D7), para que el interruptor funcione sin cambios de
  código.

**Justificación:** RF-24..RF-27, CL-4, CL-7. Sin ORM ni Alembic; el alcance no
necesita una herramienta de migraciones y la constitución #1 exige justificar
cada dependencia.

**Alternativas descartadas:**

- Alembic u otra herramienta de migraciones: dependencia y complejidad no
  justificadas para un esquema de dos tablas.
- `executescript`/traducción general de SQL del spike: no es DDL nativo y
  ocultaba el esquema real (F-02/F-04).
- Crear el esquema solo manualmente: viola RF-24 y RNF-7.

**RF:** RF-24, RF-25, RF-26, RF-27; CL-4, CL-5, CL-7.

### D5 — Transacciones y atomicidad de la Spec 010

**Decisión:** la transición a `cancelled` y el registro del evento `pending`
comparten **la misma conexión y la misma transacción**:

1. `UPDATE appointments SET status = %s WHERE id = %s AND status = 'confirmed'`.
2. Si `rowcount = 0`: rollback y retorno `None` (no existe o ya cancelada; sin
   evento).
3. `INSERT INTO automation_events (..., status) VALUES (..., 'pending')`.
4. `COMMIT` único.
5. Solo después del commit, el servicio publica el evento de negocio y el
   correo (best-effort, Spec 010 RF-8/RF-11/RF-12).

`Database.transaction()` usa `autocommit=False` en PostgreSQL y el modo
transaccional de SQLite; cualquier excepción hace rollback de ambas
operaciones y se propaga. No hay `autocommit` accidental ni una segunda
conexión para el evento.

**Justificación:** RF-13; Spec 010 RF-11/RF-12 («sin traza local, sin
cancelación confirmada»). El spike ya demostró el rollback con un
`event_id` duplicado; esta decisión lo convierte en contrato del código.

**Alternativas descartadas:**

- Registrar el evento después del commit: rompe la atomicidad (fue la
  desalineación T19/T20 de la Spec 010).
- Abrir dos conexiones: no comparten transacción.
- Notificar antes del commit: podría avisar de cancelaciones que luego fallan.

**RF:** RF-8, RF-9, RF-13.

### D6 — Mapeo de errores y UX mínima de indisponibilidad

**Decisión:** la frontera de persistencia traduce las excepciones del driver a
errores de dominio:

| Situación | Error de dominio | Comportamiento |
|---|---|---|
| `UniqueViolation` al insertar una cita en un slot activo | `IntegrityError` → `SLOT_TAKEN` en el servicio | **200** con `MSG_SLOT_TAKEN` vigente; la hora se sirve «Ocupado»; 0 filas nuevas |
| `OperationalError`, `InterfaceError`, timeout de conexión o de adquisición, límite de conexiones | `PersistenceUnavailable` | **503** con `MSG_PERSISTENCE_UNAVAILABLE`; sin confirmación; **nunca** 409, «Ocupado», «no existe» ni «cancelada» |
| `UniqueViolation` en `automation_events.event_id` | `IntegrityError` | Rollback de la transacción; la cita no se cancela; se propaga (500 existente) |

- `create_booking()` deja de capturar `OperationalError` como `SLOT_TAKEN`:
  solo `IntegrityError` de unicidad se mapea a `SLOT_TAKEN`.
- `consultorio/errors.py` registra un handler para `PersistenceUnavailable`:
  - peticiones HTML → `templates/errors/persistence_unavailable.html` con el
    literal, **503**;
  - peticiones JSON (`/citas/horarios`, `/citas/disponibilidad`) →
    `{"error": MSG_PERSISTENCE_UNAVAILABLE}`, **503**.
- `availability.js` trata cualquier respuesta no-2xx como error de
  disponibilidad: muestra el literal en el estado de horas y **no** marca
  horas como «Ocupado». No se añaden colores ni copy nuevos.
- Las rutas de confirmación, cancelación, admin y detalle usan el mismo
  handler; no se presenta una cita inexistente o cancelada por un fallo de BD.

**Justificación:** RF-20, RF-21, CL-1, CL-2, CL-3, CL-11; AGENTS.md
«Frontend y UX» (los mensajes deben corresponder al estado real del backend).
El 503 es el código correcto para indisponibilidad; el 409 se reserva para
conflictos de negocio.

**Alternativas descartadas:**

- Devolver 200 con el literal dentro del formulario: puede confundirse con un
  rechazo de negocio y obliga a renderizar la disponibilidad, que también
  falla.
- Devolver 409: el paciente creería que el horario está ocupado.
- Devolver 404/410: sugeriría que la cita no existe o fue cancelada.

**RF:** RF-20, RF-21; RNF-6; CL-1, CL-2, CL-3, CL-11.

### D7 — UTC en `created_at` y `sent_at`

**Decisión:** se mantienen las columnas como `TEXT` para preservar los
dataclasses, las firmas y los literales de fecha ya usados por la aplicación,
pero se almacenan en **UTC** con formato `YYYY-MM-DD HH:MM:SS`:

- PostgreSQL: `DEFAULT (to_char(now() AT TIME ZONE 'UTC',
  'YYYY-MM-DD HH24:MI:SS'))`.
- SQLite de rollback: `DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))`.
- `mark_sent()` actualiza `sent_at` con la misma expresión UTC.
- No se convierte a `America/Bogota` en esta fase; la zona local se usará solo
  en futuras visualizaciones.

El payload `occurred_at` de los eventos no forma parte de RF-30; se conserva
sin cambios para no alterar el contrato de las Specs 007/008/010. Cualquier
alineación futura exigirá su propia decisión.

**Justificación:** RF-30; el spike mantuvo `TEXT` y advirtió que
`datetime('now','localtime')` era hora local. `TEXT` evita romper los
dataclasses y las comparaciones ISO de `date`/`time`.

**Alternativas descartadas:**

- `TIMESTAMPTZ`: semánticamente más rica, pero cambia los tipos de fila, los
  dataclasses y las expectativas de los tests; no es necesaria para el MVP.
- Mantener hora local: contradice RF-30 y haría ambiguos los redespliegues.

**RF:** RF-30.

### D8 — Dialecto PostgreSQL y compatibilidad del SQL

**Decisión:**

- Parámetros `%s` en todo el SQL de aplicación.
- `INSERT INTO appointments ... RETURNING id` para sustituir `lastrowid`.
- `BIGSERIAL PRIMARY KEY` para los identificadores; se descarta
  `GENERATED ... AS IDENTITY` para mantener el DDL verificado por el spike.
- `TEXT` para cadenas, fechas y horas ISO; se descarta `DATE` para no cambiar
  el tipo de los dataclasses ni las comparaciones de rango.
- `UNIQUE(event_id)` inline en `automation_events`.
- Índice único parcial `ux_appointments_slot_open`.
- `rowcount` se conserva para `UPDATE` y para `claim_failed_event`.
- `psycopg.rows.dict_row` (o equivalente) para el acceso por nombre que hoy
  ofrece `sqlite3.Row`.
- No se usa un traductor general de SQL. Para el rollback SQLite se admite un
  adaptador mínimo y documentado que sustituye `%s` por `?` en SQL controlado
  por el proyecto, sin `?` dentro de literales ni `%` fuera de placeholders.
- La introspección de tests usa `pg_indexes`, `pg_index` e
  `information_schema`; no se emula `sqlite_master` ni `PRAGMA` (F-02).

**Justificación:** RF-4..RF-9, RF-10..RF-14; paridad con el SQL actual y con el
spike. El adaptador mínimo evita duplicar dos juegos de consultas y mantiene el
rollback, sin repetir el emulador de 511 líneas del spike.

**Alternativas descartadas:**

- Traductor general de SQL (F-04): frágil y oculta el dialecto real.
- Dos implementaciones completas de repositorio: duplicación y riesgo de
  divergencia.
- `DATE`/`TIMESTAMP` nativos: cambio de contrato innecesario.

**RF:** RF-4..RF-14.

### D9 — Estrategia de pruebas: suite siempre PostgreSQL

**Decisión:**

- La suite se ejecuta **siempre** contra PostgreSQL (RF-28). SQLite no es un
  modo de pruebas paralelo ni evidencia de paridad.
- `TEST_DATABASE_URL` apunta al PostgreSQL de Docker (RF-29). Si no está
  definida o no responde, la sesión de pytest **falla explícitamente** al
  inicio con instrucciones; no se usa `skip` para ocultar la falta de BD
  (CL-10).
- Cada test usa un **esquema aislado** (`test_<uuid>`) creado y eliminado por
  fixture; el `search_path` se fija en la conexión. Esto reproduce el
  aislamiento del fichero SQLite temporal y permite concurrencia real.
- Las pruebas que hoy abren SQLite directamente se reescriben para PostgreSQL:
  `test_appointment_persistence.py`, `test_hu_006.py`, `test_hu_007.py`,
  `test_hu_010.py`, `test_double_booking_service.py`,
  `test_cancellation_service.py`, `test_availability_service.py` y
  `test_hu_018.py`.
- La prueba de migración del esquema legado SQLite (`TC-010-014`) **no se
  elimina ni se sustituye**: sale de la suite de paridad y se conserva como
  verificación específica de la ruta SQLite de rollback en T15. `test_hu_010.py`
  mezcla hoy esa prueba con la suite; se reubica a
  `tests/test_rollback_sqlite.py`, marcada como verificación de rollback y
  **no** como evidencia de paridad (RF-28). La cobertura de respaldo,
  idempotencia y aborto ante duplicados se mantiene íntegra en el archivo
  reubicado. La suite de paridad mantiene en `test_hu_010.py` los criterios
  restantes de la Spec 010 y la idempotencia del esquema PostgreSQL.
- Se prohíbe eliminar, `skip` o relajar aserciones para pasar. Las pruebas
  nuevas deben ser **no vacuas**: consultan catálogos reales, provocan
  concurrencia real y fallos reales.
- E2E contra Neon se ejecuta aparte, con `E2E_DATABASE_URL`, y se documenta;
  no forma parte de la suite automática ni usa secretos en el repo.

**Justificación:** RF-28, RF-29, RNF-5; CL-10. El spike demostró que la suite
puede correr contra PostgreSQL, pero también advirtió que algunos tests seguían
abriendo SQLite (F-07). Esta fase elimina esa ambigüedad.

**Alternativas descartadas:**

- Mantener SQLite como suite principal y PostgreSQL como opcional: no cumple
  RF-28.
- `pytest.skip` si no hay BD: oculta la falta de paridad.
- Emular catálogos de PostgreSQL: produce tests vacíos (F-02).

**RF:** RF-28, RF-29; RNF-5; CL-10.

### D10 — Rollback temporal a SQLite

**Decisión:**

- Interruptor `PERSISTENCE_BACKEND=sqlite` + `DATABASE_PATH`; sin cambios de
  código, reinicio del servicio y la aplicación opera con el almacenamiento
  anterior.
- Antes de un rollback con datos reales se realiza un **snapshot manual en
  Neon** y se registra la hora del corte. Las filas creadas en PostgreSQL
  después del corte **no se trasladan** y se pierden; la pérdida está aceptada
  por la usuaria (RF-19, CL-6).
- El rollback se prueba con una prueba específica, marcada y documentada como
  verificación de rollback, **no** como evidencia de paridad: se crea una cita
  en PostgreSQL, se cambia el interruptor, se comprueba que las filas de
  PostgreSQL no son visibles, se crea una fila SQLite y se vuelve a PostgreSQL.
- `TC-010-014` se conserva en esa verificación de rollback, ejecutada desde
  `tests/test_rollback_sqlite.py`, y su resultado se registra aparte de la suite
  de paridad. Cubre respaldo, idempotencia y aborto ante duplicados del esquema
  SQLite legado.
- Tras la aceptación de la migración, el interruptor, la ruta SQLite, el DDL
  SQLite y las pruebas de rollback se retiran (RF-18).

**Justificación:** RF-18, RF-19, RNF-7; decisión de aprobación 5 y 6 de la
Spec 019. El rollback es una vía de repliegue temporal, no una arquitectura
permanente.

**Alternativas descartadas:**

- Sincronizar filas entre motores: fuera de alcance y con riesgo de conflicto.
- Mantener SQLite indefinidamente: duplica mantenimiento y contradice RF-18.
- Rollback sin snapshot: pérdida no documentada.

**RF:** RF-18, RF-19; RNF-7; CL-6.

### D11 — Despliegue en Render y Neon Free

**Decisión:**

- Neon Free, sin tarjeta y sin recursos de pago (RNF-1). Proyecto y base
  creados en la **misma región** que el servicio web de Render; la región se
  confirma en el despliegue y se documenta (RNF-3).
- `render.yaml`:
  - `DATABASE_URL` como variable secreta (`sync: false`), configurada en el
    panel de Render;
  - `PERSISTENCE_BACKEND=postgres`;
  - retirada de `DATABASE_PATH`;
  - `PYTHON_VERSION=3.12.7` (RNF-3) y `healthCheckPath: /` sin cambios.
- **Conexión a Neon (decisión 2026-11-12, tras T13):** la aplicación en Render
  usará el **endpoint directo** de Neon (host sin `-pooler`), que conserva TLS
  y acepta el parámetro de arranque `options=-c statement_timeout=...`. El
  pooler rechaza ese parámetro (`unsupported startup parameter`); no se cambia
  el código ni se desactiva TLS. Si en T14 Render no alcanzara el endpoint
  directo, se detendrá la implementación y se solicitará una decisión para
  fijar el timeout con `SET` tras conectar.
- Orden de despliegue: 1) crear proyecto/base en Neon; 2) configurar
  `DATABASE_URL` en Render; 3) desplegar; 4) verificar el esquema y una reserva;
  5) redesplegar y verificar que la cita persiste; 6) provocar/esperar el
  spin-down y verificar de nuevo.
- El `render.yaml` no contiene secretos. La documentación operativa explica
  cómo rotar la credencial y cómo comprobar la región.
- **Conflicto documental a resolver en implementación:** `AGENTS.md` menciona
  Python 3.14+ y `render.yaml` fija 3.12.7 (RNF-3). Se mantiene 3.12.7 por
  requisito aprobado y se verifica que `psycopg[binary]` instala en Render; si
  falla, se detiene la implementación y se solicita decisión.

**Justificación:** RNF-1, RNF-3, RNF-6, RNF-7. El spike no verificó Neon ni
Render; esta fase lo convierte en evidencia real.

**Alternativas descartadas:**

- Render Postgres Free: caduca a los 30 días (spike §11).
- Render Postgres de pago: rompe el presupuesto $0.
- SQLite + disco persistente: exige servicio web de pago.

**RF:** RF-1..RF-3, RF-15, RF-16; RNF-1, RNF-3, RNF-6, RNF-7.

### D12 — Literal coordinado `MSG_PERSISTENCE_UNAVAILABLE`

**Decisión:** se añade la constante
`MSG_PERSISTENCE_UNAVAILABLE = "No pudimos completar tu solicitud en este
momento. Inténtalo de nuevo en unos minutos."` en
`consultorio/content/appointment_content.py` y su espejo exacto en
`tests/expected_content.py`, en el mismo PR. Las Specs 004/005 ya fijan el
contrato (enmienda aprobada el 2026-11-08); esta fase solo implementa la clave
y su espejo. No se modifican otros literales.

**Justificación:** RF-20; AGENTS.md «Textos contractuales» (spec y espejo
cambian juntos). El literal no se inventa: está aprobado en la Spec 019 y en
las enmiendas 004/005.

**Alternativas descartadas:**

- Escribir el texto directamente en la plantilla o en el JS: rompe el espejo.
- Reutilizar `MSG_SLOT_TAKEN`: confundiría indisponibilidad con conflicto.

**RF:** RF-20; RNF-5.

### D13 — Contratos internos y compatibilidad con 004–018

**Decisión:** se mantienen los nombres públicos de servicios y repositorios,
pero el último parámetro deja de ser una ruta y pasa a ser un objeto de
persistencia:

- `DatabaseTarget`: `backend`, `dsn`, `sqlite_path`, `schema` (solo tests),
  `max_connections`, `connect_timeout`, `acquire_timeout`.
- `Database`: fachada con `connection()`, `transaction()` y `ensure_schema()`;
  reutiliza la conexión de la petición y la cierra al terminar.
- Los repositorios y servicios reciben `database: Database` (o el target) en
  lugar de `database_path: str | Path`. Las firmas de negocio (orden de
  argumentos, valores de retorno y sentinelas) se conservan.
- `Appointment` y `AutomationEvent` no cambian.
- `create_booking()` sigue devolviendo `Appointment | SLOT_TAKEN` y ahora
  puede propagar `PersistenceUnavailable`; `cancel_appointment()` conserva sus
  sentinelas y propaga `PersistenceUnavailable`.
- `cancellation_flow_service` y los blueprints 017/018 no cambian de lógica;
  solo reciben el nuevo objeto de persistencia.
- Los tests pasan de `database_path` a `database`; el cambio es mecánico y se
  hace en el mismo PR de migración de la suite.

**Justificación:** RF-4..RF-9; constitución #3. Evita duplicar la lógica de
negocio y mantiene la trazabilidad de los flujos 004–018.

**Alternativas descartadas:**

- Mantener `database_path` y meter el DSN en un `Path`: confuso y propenso a
  errores en Windows.
- Reescribir los servicios con una nueva API: riesgo de regresión innecesario.

**RF:** RF-4..RF-9, RF-17.

### D14 — Arranque sin base de datos y reintento perezoso

**Decisión:**

- `create_app()` intenta `init_db()` al arrancar. Si la BD no está disponible,
  captura `PersistenceUnavailable`, registra una advertencia **sin DSN ni PII**
  y **no aborta** el proceso (RF-22).
- `Database.ensure_schema()` se ejecuta de forma perezosa antes de la primera
  operación de persistencia. Usa un `threading.Lock` y un flag de esquema
  listo; si falla, lanza `PersistenceUnavailable` y el siguiente intento vuelve
  a probar (RF-23). No hay reinicio manual ni bucle de reintentos en segundo
  plano.
- Las páginas que no requieren persistencia siguen respondiendo.
- El DDL es idempotente y está serializado con el advisory lock (D4).

**Justificación:** RF-22, RF-23; CL-2. Neon puede estar dormido o no
alcanzable; el servicio debe recuperarse solo cuando vuelva.

**Alternativas descartadas:**

- Abortar el arranque si no hay BD: incumple RF-22.
- Reintentos infinitos en el arranque: bloquea el servicio y consume cuota.
- Crear el esquema en cada petición sin flag: coste y contención innecesarios.

**RF:** RF-22, RF-23; CL-2.

### D15 — Documentación operativa y actualización de planes

**Decisión:** se crea `docs/operaciones/postgresql.md` con configuración,
Docker local, despliegue en Render/Neon, verificación de persistencia, rotación
de credenciales, snapshot y rollback. Se actualizan las menciones a SQLite en
los `plan.md` de las Specs 004/005/006/007/010, sin cambiar requisitos ni
literales aprobados. La actualización es documental y trazable.

**Justificación:** RNF-7; la Spec 019 exige que otra persona pueda reproducir
configuración, despliegue, operación y rollback.

**Alternativas descartadas:**

- Dejar el procedimiento solo en `MEMORY.md`: no es documentación operativa y
  la memoria debe ser breve.
- Reescribir los planes antiguos desde cero: perdería decisiones históricas.

**RF:** RF-18, RF-19; RNF-7.

### D16 — Control de alcance y fases

**Decisión:** el trabajo se divide en tres entregas para no convertir el plan
en un bloque monolítico:

- **Entrega A — núcleo (T1–T9):** Docker/dev, dependencia/config, conexiones,
  DDL, repositorios, servicios, atomicidad, literal y errores/UX.
- **Entrega B — validación y despliegue (T10–T14):** migración de la suite,
  pruebas nuevas, E2E Neon y Render.
- **Entrega C — cierre (T15–T18):** rollback, actualización de planes,
  QA/aceptación y retirada del rollback.

Cada entrega requiere autorización expresa de implementación. **Ninguna tarea
está autorizada por este documento.** La T18 (retirada del rollback) queda
además condicionada a la aceptación funcional de la usuaria.

**Justificación:** el alcance supera diez tareas; la división permite revisar y
aprobar por fases sin perder requisitos ni trazabilidad (skill `sdd` §6).

**RF:** todos; RNF-7.

---

## 3. Esquema y DDL

### 3.1 PostgreSQL (destino)

```sql
CREATE TABLE IF NOT EXISTS appointments (
    id              BIGSERIAL PRIMARY KEY,
    document_type   TEXT NOT NULL,
    document_number TEXT NOT NULL,
    patient_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    service         TEXT NOT NULL,
    date            TEXT NOT NULL,
    time            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'confirmed',
    created_at      TEXT NOT NULL
        DEFAULT (to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))
);

CREATE TABLE IF NOT EXISTS automation_events (
    id              BIGSERIAL PRIMARY KEY,
    event_id        TEXT NOT NULL UNIQUE,
    event_type      TEXT NOT NULL,
    event_version   INTEGER NOT NULL,
    appointment_id  INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    detail          TEXT,
    created_at      TEXT NOT NULL
        DEFAULT (to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')),
    sent_at         TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_appointments_slot_open
    ON appointments(service, date, time)
    WHERE status <> 'cancelled';

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
        DEFAULT (to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))
);
```

La aplicación del DDL se hace paso a paso (no `executescript`), dentro de una
transacción y con `pg_advisory_xact_lock(719019)` al inicio. Cada paso se
registra en `schema_migrations` con `ON CONFLICT DO NOTHING`.

### 3.2 SQLite (solo rollback temporal)

Se conserva el esquema actual con `INTEGER PRIMARY KEY AUTOINCREMENT`, el
índice parcial `ux_appointments_slot_open` y las mismas columnas. Los defaults
de `created_at` y `sent_at` se expresan en UTC con
`strftime('%Y-%m-%d %H:%M:%S', 'now')`. No se migran datos históricos: no hay
datos reales de pacientes (decisión aprobada).

### 3.3 Invariantes de integridad

- Como máximo una cita no cancelada por `(service, date, time)`.
- Al cancelar, el horario se libera porque el índice parcial excluye
  `cancelled`.
- `automation_events.event_id` es único en el motor.
- La transición a `cancelled` y el evento `pending` son atómicos.
- Las marcas `created_at` y `sent_at` son UTC.

---

## 4. Contratos internos y compatibilidad

### 4.1 Objetos de persistencia

```text
DatabaseTarget
  backend: "postgres" | "sqlite"
  dsn: str | None
  sqlite_path: Path | None
  schema: str | None          # aislado por test; None en producción
  max_connections: int
  connect_timeout: float
  acquire_timeout: float
  statement_timeout_ms: int

Database
  connection() -> context manager[Connection]
  transaction() -> context manager[Connection]
  ensure_schema() -> None
  close_request() -> None
```

- `connection()` reutiliza la conexión activa de la petición/operación y la
  cierra al salir si la abrió.
- `transaction()` garantiza `commit` único o `rollback` completo.
- `ensure_schema()` aplica el DDL una vez por proceso, con reintento perezoso.

### 4.2 Errores de dominio

| Error | Origen | Uso |
|---|---|---|
| `PersistenceUnavailable` | `OperationalError`, `InterfaceError`, timeout de conexión/adquisición, límite de conexiones | 503 + `MSG_PERSISTENCE_UNAVAILABLE`; nunca conflicto de negocio |
| `IntegrityError` | `UniqueViolation` u otra violación de integridad | En citas → `SLOT_TAKEN`; en eventos → dedup o rollback |
| `SlotConflict` (interno, opcional) | `IntegrityError` en el slot de cita | Traducido a `SLOT_TAKEN` por el servicio |

### 4.3 Compatibilidad con 004–018

| Flujo | Contrato conservado | Cambio interno |
|---|---|---|
| 004 reserva | 8 campos, estado «Confirmada», PRG 303, literales | `database` en lugar de `database_path`; `RETURNING id` |
| 005 disponibilidad | `available`/`occupied`, días con huecos, 400/405 | SQL PostgreSQL; 503 si la BD no responde |
| 006 doble reserva | índice parcial, `SLOT_TAKEN`, 0 filas, 200 | `UniqueViolation` → `SLOT_TAKEN`; concurrencia real |
| 007/008 eventos | tipos, versiones, estados, dedup, payload | `UNIQUE(event_id)`, UTC, `rowcount` |
| 010 cancelación | transición + evento `pending` atómicos; publicación posterior | misma conexión/transacción; sin SQLite específico |
| 017 cancelación paciente | verificación, ventana 3 h, delegación | solo cambia el objeto de persistencia |
| 018 cancelar/reprogramar | orden cancelar → crear, sin reversión, literales | solo cambia el objeto de persistencia |

---

## 5. Errores y UX mínima

| Superficie | Éxito | Conflicto de horario | BD no disponible |
|---|---|---|---|
| `POST /citas` | 303 a confirmación | 200 + `MSG_SLOT_TAKEN`; hora «Ocupado» | 503 + `MSG_PERSISTENCE_UNAVAILABLE`; sin confirmación |
| `GET /citas/horarios` | 200 JSON `available`/`occupied` | — | 503 JSON `{"error": literal}`; el JS no marca «Ocupado» |
| `GET /citas/disponibilidad` | 200 JSON `days` | — | 503 JSON `{"error": literal}` |
| `GET /citas/confirmada/<id>` | 200 con estado real | — | 503; no se presenta como inexistente ni cancelada |
| Cancelación 017 | 303 a éxito | — | 503; no se presenta como «ya cancelada» |
| Admin 018 | 200 con resumen/resultado | 200 + literal de horario ocupado | 503; no se presenta como cita inexistente |

- Se añade `templates/errors/persistence_unavailable.html` con el literal y un
  enlace de vuelta a `/citas`. Usa la paleta y la tipografía vigentes; no
  introduce colores nuevos.
- `availability.js` distingue error de disponibilidad de éxito y limpia el
  estado de horas; no pinta badges «Ocupado» ante 503.
- No se añaden mensajes nuevos: el único literal es el aprobado en la Spec 019
  y en las Specs 004/005.
- Los logs no incluyen DSN, contraseña, documento, nombre, correo ni teléfono.

---

## 6. Estrategia de pruebas

### 6.1 Infraestructura

- PostgreSQL 16 en Docker para desarrollo y suite (RF-29). Comando documentado
  en `docs/operaciones/postgresql.md`; sin credenciales reales en el repo.
- `TEST_DATABASE_URL` obligatoria. Si falta o no responde, la sesión de pytest
  falla al inicio con un mensaje que explica cómo levantar el contenedor
  (CL-10). No se usa `skip`.
- Esquema aislado por test (`test_<uuid>`) con `search_path` fijado; limpieza
  con `DROP SCHEMA ... CASCADE`.
- Fixtures: `database` (target), `app` (config PostgreSQL), `client`.
- Concurrencia con `ThreadPoolExecutor`/`threading.Barrier`; cada hilo usa su
  propia conexión al mismo esquema. Sin `sleep` como sincronización.
- E2E Neon separado, manual y documentado; no usa secretos en el repo.

### 6.2 Casos de prueba propuestos

| ID | Archivo | Objetivo | RF/RNF/CL |
|---|---|---|---|
| TC-019-001 | `test_pg_resilience.py` | Config: `DATABASE_URL` obligatoria, TLS en host no local, `PERSISTENCE_BACKEND` inválido falla, sin secretos en config; DSN local con `sslmode=disable` aceptado | RF-15, RF-16; RNF-6 |
| TC-019-002 | `test_pg_resilience.py` | Conexión reutilizada dentro de una operación/petición y cerrada al final; sin conexión global; límite de conexiones y timeout de adquisición → `PersistenceUnavailable` | RF-17; CL-9, CL-11 |
| TC-019-003 | `test_pg_schema.py` | BD vacía → `init_db()` crea tablas, `UNIQUE(event_id)`, índice parcial y `schema_migrations`; catálogos reales | RF-24; CL-4 |
| TC-019-004 | `test_pg_schema.py` | Segunda ejecución de `init_db()` es idempotente; no duplica objetos ni borra datos; cambio aditivo preserva filas | RF-25, RF-26; CL-4, CL-5 |
| TC-019-005 | `test_pg_schema.py` | Dos instancias concurrentes sobre una BD vacía → ambas terminan sin error y queda un solo juego de objetos | RF-25; CL-7 |
| TC-019-006 | `test_pg_persistence.py` | Repositorio de citas: `RETURNING id`, `%s`, `rowcount`, disponibilidad excluye `cancelled`, índice parcial bloquea duplicados activos | RF-4, RF-6, RF-10, RF-11, RF-14 |
| TC-019-007 | `test_pg_persistence.py` | Repositorio de eventos: `UNIQUE(event_id)`, dedup, `mark_sent` con `sent_at` UTC, `claim_failed_event` con `rowcount` | RF-7, RF-12, RF-30 |
| TC-019-008 | `test_pg_persistence.py` | Servicio de reserva: `UniqueViolation` → `SLOT_TAKEN`; `OperationalError` → `PersistenceUnavailable` (no `SLOT_TAKEN`); concurrencia de 8 hilos → exactamente un ganador | RF-6, RF-14, RF-20, RF-21; CL-8 |
| TC-019-009 | `test_pg_persistence.py` | Atomicidad 010: transición + evento `pending` en la misma transacción; fallo del evento → rollback y cita sigue `confirmed`; publicación solo después del commit | RF-8, RF-13 |
| TC-019-010 | `test_pg_resilience.py` | BD inalcanzable → 503 + literal; JSON 503; no 409, «Ocupado», «no existe» ni «cancelada»; sin confirmación | RF-20, RF-21; CL-1, CL-2, CL-3, CL-11 |
| TC-019-011 | `test_hu_019.py` | Espejo: `appointment_content.MSG_PERSISTENCE_UNAVAILABLE == expected_content...`; Specs 004/005 sin cambios de otros literales | RF-20; RNF-5 |
| TC-019-012 | suite de paridad | Suite completa contra PostgreSQL, sin `skip` y sin SQLite directo; cubre todos los criterios de las Specs 004–018, incluidos los 18 casos de HU-018; 0 FAIL; se reporta el número real verificado | RF-28; RNF-5; CL-10 |
| TC-019-013 | `test_hu_019.py` | Integridad: insert directo duplicado en slot activo falla; tras cancelar se puede re-reservar; el slot confirmado sigue bloqueado | RF-10, RF-11 |
| TC-019-014 | `test_hu_019.py` | Concurrencia de 8 hilos sobre el mismo slot: 1 cita, 7 `SLOT_TAKEN`, sin excepción no controlada | RF-14; CL-8 |
| TC-019-015 | `test_hu_019.py` | Dedup de eventos: segundo `insert_event` devuelve `False`, una sola fila, sin segundo envío | RF-12 |
| TC-019-016 | `test_pg_resilience.py` | Arranque sin BD: `create_app()` no aborta; páginas sin persistencia responden; tras volver la BD, la primera operación crea el esquema y funciona | RF-22, RF-23; CL-2 |
| TC-019-017 | `test_pg_persistence.py` | `created_at` y `sent_at` en UTC con formato esperado; sin conversión a `America/Bogota` | RF-30 |
| TC-019-018 | `test_pg_schema.py` | Cambio de esquema aditivo sobre una BD con datos: conserva filas y garantías; segunda ejecución no falla | RF-26; CL-5 |
| TC-019-019 | E2E Neon | E2E desde entorno controlado contra Neon: TLS, creación de esquema, reserva + eventos y cold start tras inactividad/scale-to-zero; **no** incluye redespliegue ni spin-down del servicio web | RF-1; RNF-2, RNF-4 |
| TC-019-020 | Render | Despliegue: variables, región coincidente, `DATABASE_URL` secreta, reserva completa y persistencia tras **redespliegue** y **spin-down** del servicio web; sin recursos de pago | RF-2, RF-3, RF-15; RNF-1, RNF-3, RNF-6 |
| TC-019-021 | Rollback | Interruptor a SQLite, `TC-010-014` (respaldo, idempotencia y aborto ante duplicados), pérdida aceptada de filas posteriores al corte, snapshot manual documentado, vuelta a PostgreSQL; resultado registrado aparte de la paridad | RF-18, RF-19; RNF-7; CL-6 |
| TC-019-022 | Documental | Planes 004/005/006/007/010 sin menciones obsoletas a SQLite; trazabilidad intacta | RNF-7 |
| TC-019-023 | QA | Informe `qa-hu-019.md` con PASS/FAIL por TC, evidencia y checkbox de aceptación | RNF-5, RNF-7 |
| TC-019-024 | Retirada | Tras aceptación: interruptor, ruta SQLite, DDL y pruebas de rollback retirados; suite sigue en verde | RF-18; RNF-7 |

> TC-019-012 es la corrida de la suite, no una función de test. No se fija un
> número PASS de PostgreSQL hasta ejecutarla. La condición real es **0 FAIL y
> cobertura de todos los criterios de las Specs 004–018, incluidos los 18 casos
> de HU-018**. El baseline es **320 PASS / 0 FAIL en SQLite (2026-11-08)**, pero
> el conteo final puede variar por la reubicación de `TC-010-014` a
> `tests/test_rollback_sqlite.py` y por renombrados; se reportará el **número
> real verificado**, sin declarar cifras no ejecutadas.

### 6.3 No vacuidad

- Las pruebas de esquema consultan `pg_indexes`, `pg_index` e
  `information_schema`, no una emulación.
- Las pruebas de concurrencia usan conexiones reales y `Barrier`; no son
  secuenciales disfrazadas.
- La atomicidad se prueba provocando un fallo real en el `INSERT` del evento.
- La indisponibilidad se prueba con un DSN inalcanzable o un timeout corto.
- El cold start se simula cerrando conexiones y forzando una nueva; el
  scale-to-zero real de 5 minutos se verifica en E2E Neon (RNF-4).

---

## 7. Rollback y despliegue

### 7.1 Rollback operativo

1. Confirmar que existe un snapshot manual reciente en Neon y registrar la hora
   del corte.
2. Configurar `PERSISTENCE_BACKEND=sqlite` y `DATABASE_PATH` en el servicio.
3. Reiniciar/redeployar.
4. Verificar que las citas y eventos de PostgreSQL posteriores al corte no son
   visibles; la pérdida está aceptada.
5. Para volver a PostgreSQL, restaurar `PERSISTENCE_BACKEND=postgres` y el
   `DATABASE_URL`; las filas creadas en SQLite durante el rollback no se
   trasladan.
6. Documentar el incidente, la hora, el snapshot y las filas afectadas en
   `docs/evidencias/hu-019/rollback.md`.

### 7.2 Despliegue Render/Neon

1. Crear proyecto y base en Neon Free en la región coincidente con Render.
2. Copiar el DSN con TLS y guardarlo como secreto `DATABASE_URL` en Render.
3. Configurar `PERSISTENCE_BACKEND=postgres`; retirar `DATABASE_PATH`.
4. Desplegar y verificar `GET /` y una reserva completa.
5. Redesplegar y verificar que la cita persiste.
6. Esperar/provocar spin-down y verificar de nuevo.
7. Revisar que no hay recursos de pago ni secretos en el repositorio.
8. Registrar la evidencia en `docs/evidencias/hu-019/render-deploy.md`.

---

## 8. Matriz de trazabilidad

| Requisito | Decisión | Tarea | Prueba |
|---|---|---|---|
| RF-1 persistencia PostgreSQL | D1, D2, D4, D13 | T2, T3, T4, T13, T14 | TC-019-003, TC-019-019, TC-019-020 |
| RF-2 sobrevive redespliegue | D11 | T14 | TC-019-020 |
| RF-3 sobrevive spin-down | D3, D11, D14 | T3, T14 | TC-019-016, TC-019-020 |
| RF-4 paridad reserva | D8, D9, D13 | T5, T7, T11 | TC-019-006, TC-019-012 |
| RF-5 paridad disponibilidad | D8, D9 | T5, T7, T11 | TC-019-006, TC-019-012 |
| RF-6 paridad doble reserva | D4, D8 | T5, T7, T11 | TC-019-006, TC-019-008, TC-019-012 |
| RF-7 paridad eventos | D8, D9 | T5, T7, T11 | TC-019-007, TC-019-012 |
| RF-8 paridad cancelación/notificación | D5, D8 | T7, T11 | TC-019-009, TC-019-012 |
| RF-9 paridad 018 | D5, D8 | T7, T11 | TC-019-009, TC-019-012 |
| RF-10 unicidad en el motor | D4 | T4, T5, T12 | TC-019-003, TC-019-006, TC-019-013 |
| RF-11 liberación al cancelar | D4, D8 | T5, T7, T12 | TC-019-006, TC-019-013 |
| RF-12 unicidad de evento | D4, D8 | T4, T5, T12 | TC-019-003, TC-019-007, TC-019-015 |
| RF-13 atomicidad cancelación + evento | D5 | T7, T12 | TC-019-009 |
| RF-14 concurrencia de reservas | D4, D6, D8 | T5, T7, T12 | TC-019-008, TC-019-014 |
| RF-15 configuración sin secretos | D2 | T2, T14 | TC-019-001, TC-019-020 |
| RF-16 TLS | D2 | T2, T13, T14 | TC-019-001, TC-019-019, TC-019-020 |
| RF-17 conexiones reutilizadas/liberadas | D3 | T3, T11 | TC-019-002, TC-019-012 |
| RF-18 rollback por interruptor | D2, D10 | T15, T18 | TC-019-021, TC-019-024 |
| RF-19 sin migración de datos | D10 | T15 | TC-019-021 |
| RF-20 literal de indisponibilidad | D6, D12 | T8, T9, T12 | TC-019-010, TC-019-011 |
| RF-21 no confundir con ocupado/inexistente/cancelada | D6 | T9, T11 | TC-019-010, TC-019-012 |
| RF-22 arranque sin BD | D4, D14 | T4, T12 | TC-019-016 |
| RF-23 recuperación sin intervención | D4, D14 | T4, T12 | TC-019-016 |
| RF-24 creación del esquema | D4 | T4, T12 | TC-019-003 |
| RF-25 idempotencia | D4 | T4, T12 | TC-019-004, TC-019-005 |
| RF-26 cambios con datos | D4 | T4, T12 | TC-019-004, TC-019-018 |
| RF-27 sin ORM | D1, D4 | T2, T4, T12 | TC-019-003 |
| RF-28 suite siempre PostgreSQL | D9 | T10, T11, T12, T17 | TC-019-012, TC-019-021 |
| RF-29 PostgreSQL local en Docker | D9 | T1, T10, T11 | TC-019-012 |
| RF-30 UTC | D7 | T4, T5, T12 | TC-019-007, TC-019-017 |
| RNF-1 coste $0 | D11 | T14 | TC-019-020 |
| RNF-2 límites Neon Free | D3, D9, D11 | T1, T3, T13, T14 | TC-019-002, TC-019-019 |
| RNF-3 Render/región | D11 | T13, T14 | TC-019-019, TC-019-020 |
| RNF-4 cold start | D3, D14 | T3, T12, T13 | TC-019-016, TC-019-019 |
| RNF-5 sin regresiones | D9, D12 | T8, T10, T11, T12, T17 | TC-019-011, TC-019-012, TC-019-023 |
| RNF-6 seguridad/PII | D2, D6, D15 | T2, T9, T13, T14, T17 | TC-019-001, TC-019-010, TC-019-019, TC-019-020 |
| RNF-7 documentación operativa | D10, D15 | T1, T13, T14, T15, T16, T17 | TC-019-019, TC-019-020, TC-019-021, TC-019-022, TC-019-023 |
| RNF-8 dependencias mínimas | D1 | T2, T17 | TC-019-001 |
| CL-1 cuota agotada | D6, D14 | T9, T12 | TC-019-010 |
| CL-2 BD dormida/inalcanzable | D3, D6, D14 | T3, T9, T12, T13 | TC-019-002, TC-019-010, TC-019-016, TC-019-019 |
| CL-3 1 GB alcanzado | D6 | T9, T12 | TC-019-010 |
| CL-4 esquema vacío/existente | D4 | T4, T12 | TC-019-003, TC-019-004 |
| CL-5 cambio con datos | D4 | T4, T12 | TC-019-004, TC-019-018 |
| CL-6 rollback | D10 | T15 | TC-019-021 |
| CL-7 dos instancias | D4 | T4, T12 | TC-019-005 |
| CL-8 concurrencia mismo slot | D4, D6 | T5, T7, T12 | TC-019-008, TC-019-014 |
| CL-9 alta concurrencia | D3 | T3, T11 | TC-019-002, TC-019-012 |
| CL-10 sin BD local | D9 | T1, T11 | TC-019-012 |
| CL-11 límite de conexiones | D3, D6 | T3, T9, T12 | TC-019-002, TC-019-010 |

---

## 9. Riesgos y mitigaciones

| # | Riesgo | Impacto | Mitigación |
|---|---|---|---|
| R-01 | `psycopg[binary]==3.3.8` no instala o falla en Python 3.12.7 de Render | Bloquea el despliegue | Verificar en T14; si falla, detener y solicitar decisión (no cambiar la versión sin aprobación) |
| R-02 | Neon Free no verificado en el spike (cold start, límites, TLS) | Comportamiento real desconocido | E2E T13 y despliegue T14 con evidencia; documentar límites |
| R-03 | Límite de conexiones de Neon alcanzado | 503 en picos | Semáforo por proceso, `DATABASE_MAX_CONNECTIONS`, timeouts, 503 correcto (no 409) |
| R-04 | Latencia de la suite PostgreSQL (spike: 232 s) | Desarrollo más lento | Esquema aislado, reutilización por petición, evitar conexiones por sentencia |
| R-05 | Errores de conexión tratados como conflicto | Paciente ve «Ocupado» falso | D6: `PersistenceUnavailable` ≠ `SLOT_TAKEN`; TC-019-008/010 |
| R-06 | Tests que siguen abriendo SQLite | Paridad ficticia | D9: prohibido; reescritura de tests; TC-019-012 |
| R-07 | Migración legado SQLite sin equivalente | Cobertura de migración perdida | Reubicar `TC-010-014` a `tests/test_rollback_sqlite.py`, conservando respaldo, idempotencia y aborto; ejecutarla y registrar su resultado aparte en T15 |
| R-08 | Rollback con datos posteriores al corte | Pérdida de filas | Aceptada por la usuaria; snapshot manual y documentación (T15) |
| R-09 | DDL concurrente en dos instancias | Error de arranque | Advisory lock + `IF NOT EXISTS`; TC-019-005 |
| R-10 | Secretos en repo/docs/tests | Incidente de seguridad | `sync: false`, revisión de artefactos, DSN local de usar y tirar |
| R-11 | `TEXT` UTC vs payload local | Inconsistencia menor | RF-30 acota columnas; payload fuera de alcance; documentado |
| R-12 | Conflicto AGENTS.md (3.14+) vs RNF-3 (3.12.7) | Decisión ambigua | Mantener 3.12.7 por requisito aprobado; verificar y escalar si falla |
| R-13 | 503 genérico percibido como error técnico | Mala UX | Literal aprobado, enlace de vuelta, sin tecnicismos; revisión en QA |
| R-14 | Retirada prematura del rollback | Sin vía de repliegue | T18 solo tras aceptación explícita |
| R-15 | PII en logs de error | Incumple RNF-6 | No loguear DSN ni datos de paciente; revisar handlers |

---

## 10. Fuera de alcance

- Spec de acceso/agenda (roles, sesión, CSRF, auditoría) y Specs 011/012.
- Certificación de compliance, acuerdos de tratamiento, planes de pago, alta
  disponibilidad, réplica y multi-región.
- Migración de datos históricos desde SQLite.
- Backups, retención y restauración automatizados más allá del snapshot manual
  previo a un rollback.
- Cambios de UX/UI; solo el estado de error estrictamente necesario para
  indisponibilidad.
- Reintentos automáticos de reservas, colas o workers.
- ORM, Alembic u otras herramientas de migración.
- WhatsApp (Spec 009) y cualquier cambio de literales distinto del aprobado.

---

## 11. Plan de evidencias

Directorio: `docs/evidencias/hu-019/`.

| Artefacto | Contenido | Tarea |
|---|---|---|
| `qa-hu-019.md` | PASS/FAIL por TC, comandos, resultados reales, regresiones, checkbox de aceptación | T17 |
| `suite-postgres.txt` | Salida de `python -m pytest -q` contra PostgreSQL, sin secretos | T11, T17 |
| `e2e-neon.md` | Pasos y resultados del E2E Neon desde entorno controlado: TLS, esquema, reserva + eventos y cold start/scale-to-zero (sin redespliegue ni spin-down del servicio web; sin DSN ni PII) | T13 |
| `render-deploy.md` | Variables, región, reserva completa y persistencia tras redespliegue y spin-down del servicio web | T14 |
| `rollback.md` | Snapshot, hora de corte, filas afectadas, pérdida aceptada y resultado de `TC-010-014` registrado aparte | T15 |
| `persistence-unavailable.png` | Captura de la pantalla 503 si se valida visualmente | T9, T17 |
| `capturas/` | Capturas CDP 1280/375 de la pantalla de indisponibilidad, si aplica | T17 |

No se guardan DSN, contraseñas, tokens, datos de pacientes ni capturas con PII.
Las capturas, si se generan, usan CDP (`Emulation.setDeviceMetricsOverride`),
no `--window-size` (AGENTS.md).

---

## 12. Estimación basada en el spike

El spike no midió tiempos por tarea; solo estimó líneas. No se inventan horas
ni cifras de negocio. La referencia es
`docs/spikes/postgresql-evaluacion-2026-11.md` §7:

| Área | Estimación del spike | Tareas |
|---|---|---|
| Producción | ~140–200 líneas netas en 9 archivos | T2–T9 |
| Tests | ~180–250 líneas en 6–8 archivos | T10–T12 |
| Dependencia | `psycopg[binary]` +1 en `requirements.txt` | T2 |
| Rollback | No medido por el spike; se acota a interruptor + documentación + prueba | T15, T18 |
| Despliegue | No verificado por el spike; se valida con evidencia real | T13, T14 |

La granularidad de las tareas sigue la referencia de 20–30 minutos de la skill
`sdd`, pero las tareas T5, T10, T11 y T12 pueden subdividirse durante la
implementación si se autoriza la fase.

---

## 13. Secuencia de implementación

> **T1 está autorizada (2026-11-08).** Las tareas T2–T18 permanecen pendientes
> de autorización expresa; cada cierre se revisa antes de la siguiente tarea.

0. **Aprobación** de este `plan.md` y de `tasks.md` (2026-11-08).
1. **Entrega A — núcleo:** T1–T9.
2. **Entrega B — validación y despliegue:** T10–T14.
3. **Entrega C — cierre:** T15–T17.
4. **Retirada del rollback:** T18, solo tras la aceptación funcional.

Cada tarea se cierra con sus pruebas propias en verde y su evidencia. No se
declara PASS por inspección del código (AGENTS.md).

---

## 14. Aprobación registrada

Este documento fue **aprobado por la usuaria el 2026-11-08** junto con
`tasks.md`, incluidas las decisiones D1–D16, el esquema y el contrato de errores
(§3–§5), la estrategia de pruebas (§6), la división en entregas (D16), el plan
de evidencias y la estimación basada en el spike (§11–§12). La aprobación
autoriza **T1** de la Entrega A; las tareas T2–T18 requieren autorización
expresa.

Cualquier cambio de requisitos, literales, tarifas o alcance exige actualizar
primero la Spec 019 y sus enmiendas coordinadas, y después este plan y
`tasks.md`.
