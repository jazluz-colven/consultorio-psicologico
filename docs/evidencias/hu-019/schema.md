# Evidencia HU-019 — T4: DDL idempotente, advisory lock y arranque perezoso

- **Fecha:** 2026-11-09
- **Rama:** `feature/hu-019-migracion-postgres`
- **HEAD:** `8ce511f`
- **Tarea:** T4 (autorizada por la usuaria el 2026-11-09). **Sin commit ni push.**
- **Estado:** **COMPLETADA** (2026-11-09); **APROBADA por `@revisor`**.
  No se declara aceptación funcional de la usuaria.
- **Alcance:** DDL PostgreSQL sin ORM, idempotente y serializado con advisory
  lock; `create_app()` tolerante a BD no disponible; `ensure_schema()`
  perezoso con reintento. **No** incluye T5 ni posteriores (repositorios,
  servicios, literal/errores 503, suite de paridad). SQLite sigue activo para
  los repositorios/servicios actuales.

## Requisitos cubiertos

| Requisito | Resultado | Evidencia |
|---|---|---|
| RF-22 — arranque sin BD no aborta | PASS | TC-019-016 parte A; alerta sin DSN |
| RF-23 — recuperación sin reinicio manual | PASS (base) | TC-019-016 parte B; reintento perezoso |
| RF-24 — esquema completo en BD vacía | PASS | TC-019-003; catálogos reales |
| RF-25 — idempotencia | PASS | TC-019-004, TC-019-005, TC-019-018 |
| RF-26 — cambios con datos preservan filas e integridad | PASS | TC-019-018 |
| RF-27 — sin ORM | PASS | SQL explícito; guard de imports TC-010-017 |
| RF-10/RF-12 — unicidad en el motor | PASS (DDL) | índice parcial y `UNIQUE(event_id)` |
| CL-4 — BD vacía/existente | PASS | TC-019-003/004 |
| CL-5 — cambio con datos | PASS | TC-019-018 |
| CL-7 — dos instancias | PASS | TC-019-005; advisory lock |

RF-23 queda **base** en T4: la recuperación perezosa está probada a nivel de
`Database.ensure_schema()`; el uso desde las rutas de reserva/disponibilidad se
completa en T5/T6/T9.

## Entorno de ejecución

- PostgreSQL **16.15** en Docker (`consultorio-pg-019`, `127.0.0.1:55432`).
- `psycopg` **3.3.8**, `PSYCOPG_IMPL=python` y `libpq` local 16.15 (decisión A1).
- DSN de sesión (contraseña local redactada):

  ```text
  postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable
  ```

  Se usó `127.0.0.1` en lugar de `localhost`: en este equipo Windows,
  `localhost` resuelve primero a `::1` y cada conexión espera el
  `connect_timeout` (≈5 s) antes de caer a IPv4. El contenedor publica solo
  `127.0.0.1:55432`; el DSN es equivalente y evita esa latencia artificial.
- Cada test crea un esquema temporal único `test_hu019_<uuid>` con
  `search_path` (`DatabaseTarget.schema`) y lo elimina con `DROP SCHEMA …
  CASCADE`. No se toca `public` ni los datos de desarrollo.

## Implementación

| Archivo | Cambio |
|---|---|
| `consultorio/persistence/database.py` | DDL PostgreSQL explícito (`schema_migrations`, `appointments`, `automation_events`, índice parcial), `apply_postgres_schema()` con `pg_advisory_xact_lock(719019)`, registro por paso con `ON CONFLICT DO NOTHING`, `ensure_schema()` PostgreSQL perezoso y `search_path` opcional para tests. Se conserva el DDL SQLite de rollback y `init_db`. |
| `consultorio/__init__.py` | Mantiene `init_db(DATABASE_PATH)` (convivencia transitoria con T5/T6) y **además** intenta `database.ensure_schema()` al arrancar, capturando `PersistenceUnavailable` y registrando una advertencia **sin DSN ni PII**. |
| `tests/conftest.py` | `require_test_database_url()` (fallo explícito, sin `skip`), fixtures `pg_schema` y `pg_target` con esquema aislado y limpieza. |
| `tests/test_pg_schema.py` | TC-019-003, TC-019-004, TC-019-005 y TC-019-018 contra PostgreSQL real. |
| `tests/test_pg_resilience.py` | TC-019-016: arranque sin BD + recuperación perezosa con `connect_factory` que falla una vez y delega a PostgreSQL real. |

### DDL aplicado (plan §3.1)

Pasos ordenados, aditivos e idempotentes, ejecutados uno a uno dentro de una
única transacción:

| Versión | Paso |
|---|---|
| 1 | `CREATE TABLE IF NOT EXISTS schema_migrations` |
| 2 | `CREATE TABLE IF NOT EXISTS appointments` (`BIGSERIAL`, `TEXT`, `created_at` UTC) |
| 3 | `CREATE TABLE IF NOT EXISTS automation_events` (`event_id … UNIQUE`) |
| 4 | `CREATE UNIQUE INDEX IF NOT EXISTS ux_appointments_slot_open … WHERE status <> 'cancelled'` |

Cada paso inserta su versión con `INSERT … ON CONFLICT DO NOTHING`. Si algo
falla, la transacción completa hace rollback y no queda un marcador de
migración huérfano.

## TC-019-003 / 004 / 005 / 018 / 016 — resultado real

Comando:

```powershell
python -m pytest -v tests/test_pg_schema.py `
  "tests/test_pg_resilience.py::test_tc_019_016_startup_tolerates_outage_and_recovers"
```

Salida literal:

```text
tests/test_pg_schema.py::test_tc_019_003_empty_database_creates_expected_schema PASSED
tests/test_pg_schema.py::test_tc_019_004_second_run_is_idempotent_and_keeps_data PASSED
tests/test_pg_schema.py::test_tc_019_005_concurrent_bootstrap_leaves_single_object_set PASSED
tests/test_pg_schema.py::test_tc_019_018_reapply_over_data_preserves_rows_and_integrity PASSED
tests/test_pg_resilience.py::test_tc_019_016_startup_tolerates_outage_and_recovers PASSED

============================== 5 passed in 4.45s ==============================
```

### TC-019-003 — catálogos reales tras crear desde BD vacía

Consultas ejecutadas contra el esquema temporal (la salida de abajo es real):

```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = '<schema>';
SELECT conname, pg_get_constraintdef(c.oid) FROM pg_constraint c
  JOIN pg_class t ON t.oid = c.conrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
  WHERE n.nspname = '<schema>' AND t.relname = 'automation_events' AND c.contype = 'u';
SELECT indexdef FROM pg_indexes
  WHERE schemaname = '<schema>' AND indexname = 'ux_appointments_slot_open';
SELECT column_name, data_type, is_nullable, column_default
  FROM information_schema.columns
  WHERE table_schema = '<schema>' AND table_name = 'schema_migrations'
  ORDER BY ordinal_position;
```

Salida real:

```text
tables: ['appointments', 'automation_events', 'schema_migrations']
unique constraints on automation_events:
   ('automation_events_event_id_key', 'UNIQUE (event_id)')
partial index definition:
   CREATE UNIQUE INDEX ux_appointments_slot_open ON test_hu019_<uuid>.appointments
   USING btree (service, date, "time") WHERE (status <> 'cancelled'::text)
schema_migrations columns:
   ('version', 'integer', 'NO', None)
   ('applied_at', 'text', 'NO',
    "to_char((now() AT TIME ZONE 'UTC'::text), 'YYYY-MM-DD HH24:MI:SS'::text)")
BIGSERIAL ids and UTC defaults:
   ('appointments', 'id', 'bigint', "nextval('…appointments_id_seq'::regclass)")
   ('appointments', 'created_at', 'text',
    "to_char((now() AT TIME ZONE 'UTC'::text), 'YYYY-MM-DD HH24:MI:SS'::text)")
   ('automation_events', 'id', 'bigint', "nextval('…automation_events_id_seq'::regclass)")
   ('automation_events', 'created_at', 'text',
    "to_char((now() AT TIME ZONE 'UTC'::text), 'YYYY-MM-DD HH24:MI:SS'::text)")
```

El test comprueba además que `indexdef` empieza por `CREATE UNIQUE INDEX`,
contiene `ux_appointments_slot_open`, `USING btree`, `(service, date, "time")` y
`WHERE (status <> 'cancelled'`, y que `applied_at` es `text NOT NULL` con
default `to_char(now() AT TIME ZONE 'UTC', …)`.

### TC-019-004 — segunda ejecución idempotente

Se aplica el esquema, se inserta una cita y un evento, y se vuelve a aplicar
con una instancia `Database` nueva (el flag `_schema_ready` se reinicia, así
que el DDL se ejecuta de verdad). Resultado:

- Tablas e índices: idénticos antes y después.
- `appointments`: 1 fila; `automation_events`: 1 fila.
- `schema_migrations`: `[(1,), (2,), (3,), (4,)]` (sin duplicados).

### TC-019-005 — dos instancias concurrentes

Dos `Database` independientes aplican el esquema a la vez, sincronizados con
`threading.Barrier`. Ambos terminan sin error; los dos hilos acaban vivos =
`False`; queda **una** copia del índice parcial y las cuatro versiones únicas.
El advisory lock `pg_advisory_xact_lock(719019)` serializa el bootstrap y los
`IF NOT EXISTS` cubren al segundo.

### TC-019-018 — reaplicación sobre datos

Con una cita y un evento ya insertados, una instancia nueva reaplica el DDL:

- Filas preservadas: `appointments` = 1, `automation_events` = 1.
- Estado de la cita intacto (`confirmed`), relación evento→cita intacta.
- La integridad sigue vigente: un segundo `INSERT` en el mismo
  `(service, date, time)` activo y un `event_id` repetido lanzan
  `psycopg.errors.UniqueViolation`.

### TC-019-016 — arranque sin BD y recuperación perezosa

Parte A: `create_app()` con un DSN local inalcanzable y **sin credenciales**
(`127.0.0.1:1`, `DATABASE_CONNECT_TIMEOUT=1`) arranca sin abortar y `GET /`
responde 200. La advertencia de arranque **no** contiene `postgresql://` ni el
usuario `consultorio_dev`.

Parte B: un `connect_factory` lanza `psycopg.OperationalError` la primera vez y
delega en la conexión real la segunda. El primer `ensure_schema()` lanza
`PersistenceUnavailable` y no crea objetos; el segundo, sin reiniciar el
proceso, crea las tres tablas y una consulta real (`SELECT 1`) funciona.

## `TEST_DATABASE_URL` obligatoria (sin skip)

Comprobación negativa ejecutada sin la variable:

```text
E           Failed: TEST_DATABASE_URL no está definida: la Spec 019 exige PostgreSQL
            para los tests de esquema. Define el DSN local
            (ver docs/operaciones/postgresql.md) y vuelve a ejecutar.
1 error in 0.30s
```

Es un **fallo explícito** (D9/CL-10), no un `skip` ni un `xfail`.

## Suite completa

Comando (con `TEST_DATABASE_URL` definida):

```powershell
python -m pytest -q
```

Resultado real:

```text
369 passed in 34.22s
```

Baseline previo: **364 PASS**. Los 5 casos nuevos de T4 (4 de esquema + 1 de
resiliencia) elevan el total a **369 PASS / 0 FAIL**, sin regresiones.

## Convivencia transitoria con SQLite

Hasta T5/T6 los repositorios y servicios siguen usando `DATABASE_PATH`/SQLite,
por eso `create_app()` **conserva** `init_db(DATABASE_PATH)`. El DDL PostgreSQL
se ejecuta además cuando el backend es `postgres` y no sustituye al SQLite. El
DDL SQLite de rollback (`SCHEMA`, `init_db`, índice parcial) no se ha
modificado y sigue siendo idempotente; la suite actual (364 casos previos) lo
sigue ejercitando.

## Riesgos y pendientes

- **T5 en adelante no implementado:** los repositorios/servicios todavía no
  usan `Database`; RF-23 completo requiere T5/T6/T9.
- **`sslmode` duplicado en el DSN (riesgo de T2):** sigue abierto; endurecer
  antes de T14.
- **`localhost` con 5 s de espera:** peculiaridad del entorno Windows (IPv6);
  no afecta a Neon/Render. Los helpers de test siempre pasan `connect_timeout`.
- **Prueba de esquema en `public`:** los tests usan esquemas temporales; no se
  verificó visualmente nada porque T4 no cambia la interfaz.
- La sentencia `CREATE TABLE IF NOT EXISTS` es idempotente pero no migra
  columnas de una tabla preexistente con forma distinta; un cambio destructivo
  exigirá una decisión documentada (D4), fuera de T4.

## Revisión técnica

- **2026-11-09 — `@revisor`: APROBADO.** Sin defectos bloqueantes. Verificó
  RF-22 a RF-27 y CL-4/CL-5/CL-7, catálogos reales, concurrencia, rollback
  manual ante fallo mid-DDL/commit, liberación de advisory lock y semáforo.
- Suite completa: **369 PASS / 0 FAIL** (364 previos + 5 T4). Sin `skip`.
- Observaciones no bloqueantes:
  - Sin `TEST_DATABASE_URL`, la ejecución da 364 PASS + 5 errores de setup, no
    un fallo en `pytest_sessionstart`; sigue siendo fallo explícito sin skip.
  - `create_app()` intenta `ensure_schema()` al arrancar; con la BD caída puede
    añadir hasta `connect_timeout` (10 s por defecto), aunque no aborta.
  - `create_app()` solo captura `PersistenceUnavailable`; un DSN malformado
    podría abortar el arranque (no probado, fuera del caso «BD no disponible»).
  - El rollback mid-DDL y la ausencia de marcadores huérfanos se verificaron
    manualmente, no con un test automatizado.
  - La limpieza de esquemas temporales del fixture es best-effort; se eliminó
    manualmente el esquema residual de una ejecución previa.
  - El DDL SQLite conserva `datetime('now','localtime')`; la alineación UTC de
    RF-30 corresponde a T5/T6.
  - Los marcadores de `schema_migrations` se insertan aunque el objeto ya
    existiera; los cambios de forma de tabla quedan fuera de T4.

## Confirmaciones de alcance

- No se modificaron repositorios, servicios, blueprints, plantillas ni
  `tests/expected_content.py`.
- No se modificó `render.yaml` ni se añadieron dependencias.
- No se implementó T5 ni tareas posteriores.
- No se hizo commit ni push.
- Esta evidencia no contiene contraseñas ni PII.

---

## T12 — revisión de no vacuidad (TC-019-003, 004, 005, 018)

> Sección añadida el **2026-11-11** al implementar T12. No reescribe el cierre
> de T4; documenta la auditoría de T12 y los refuerzos aplicados.

**Resultado real:** `python -m pytest -q tests/test_pg_schema.py` → **4 passed**
(además, los cuatro archivos T12 dieron **77 passed** y la suite completa
**397 passed**; ver `suite-postgres.txt` y `resilience.md`).

| TC | Prueba (`tests/test_pg_schema.py`) | Resultado | Argumento de no vacuidad |
|---|---|---|---|
| TC-019-003 | `test_tc_019_003_empty_database_creates_expected_schema` | PASS | Crea el esquema en PostgreSQL real y lee `information_schema.tables`, `pg_constraint`, `pg_indexes` y `information_schema.columns`. Comprueba el índice parcial exacto, `UNIQUE(event_id)`, `BIGSERIAL` y defaults UTC; no usa SQLite ni introspección simulada. |
| TC-019-004 | `test_tc_019_004_second_run_is_idempotent_and_keeps_data` | PASS | Inserta una cita y un evento reales entre dos `ensure_schema()` ejecutados por instancias distintas (`_schema_ready` reiniciado) y verifica que tablas, índices, filas y marcadores de migración no cambian. |
| TC-019-005 | `test_tc_019_005_concurrent_bootstrap_leaves_single_object_set` | PASS | Dos conexiones/instancias reales arrancan simultáneamente tras un `threading.Barrier`; el advisory lock serializa el DDL y el test comprueba que no hay errores ni objetos duplicados. |
| TC-019-018 | `test_tc_019_018_reapply_over_data_preserves_rows_and_integrity` | PASS | Aplica un **paso aditivo real** (versión 5, `ALTER TABLE … ADD COLUMN IF NOT EXISTS`) sobre una tabla con datos, verifica filas/columnas y que la unicidad del slot y de `event_id` siguen impuestas por el motor; una tercera aplicación es idempotente. |

**Refuerzos T12:**

- **TC-019-003 y TC-019-005** pasan de comprobar un subconjunto a exigir
  igualdad exacta de tablas (`EXPECTED_TABLES`) e índices (`EXPECTED_INDEXES`).
  Así un objeto extra o duplicado también hace fallar la prueba.
- **TC-019-018** antes solo reaplicaba el mismo DDL. Ahora simula un cambio
  aditivo real con `monkeypatch` sobre `PG_SCHEMA_STEPS` en el proceso de test
  (la producción conserva sus cuatro pasos), conserva los datos y vuelve a
  comprobar la integridad y la idempotencia.

No se modificó el DDL de producción, `public` no se tocó y el esquema temporal
se elimina con `DROP SCHEMA … CASCADE` al finalizar cada test.
