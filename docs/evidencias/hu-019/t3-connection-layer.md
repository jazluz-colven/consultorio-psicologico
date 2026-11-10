# Evidencia HU-019 — T3: capa de conexiones y errores de dominio

- **Fecha:** 2026-11-09
- **Rama:** `feature/hu-019-migracion-postgres`
- **HEAD:** `8ce511f`
- **Tarea:** T3 (autorizada 2026-11-09). Sin commit ni push.
- **Estado:** **COMPLETADA** (2026-11-09); **APROBADA por `@revisor`** tras
  corregir F-01/F-02 en el segundo ciclo.
- **Alcance:** conexiones por petición/operación, semáforo, transacciones,
  `PersistenceUnavailable` y cableado mínimo de `create_app`. **No** incluye DDL
  PostgreSQL (T4), SQL de repositorios (T5), handler 503/plantilla (T9) ni la
  suite PostgreSQL (T10/T11).

## Requisitos cubiertos

- **RF-17 — PASS.** Reutilización y liberación de conexiones sin agotar el
  límite.
- **RF-22 — PASS en arranque.** `create_app()` no falla si la base no está
  disponible; la indisponibilidad se manifiesta al abrir/usar una conexión.
  La inicialización perezosa del esquema PostgreSQL sigue siendo T4.
- **RF-23 — BASE/PARCIAL, NO CERRADA.** T3 aporta la traducción de errores y la
  liberación de recursos que la recuperación necesita, pero la recuperación
  perezosa completa (`ensure_schema()` PostgreSQL, reintento y recuperación sin
  reinicio manual) se verifica en **T4/T5/T9**. No se declara RF-23 cerrada.
- **CL-9 — PASS.** Alta concurrencia contenida por el semáforo.
- **CL-11 — PASS.** El límite/indisponibilidad no se presenta como conflicto de
  horario (`PersistenceUnavailable` ≠ `SLOT_TAKEN`).

## Corrección tras revisión (2026-11-09)

El revisor emitió **CAMBIOS NECESARIOS** con dos hallazgos:

- **F-01 — traducción incompleta.** Solo se traducían los errores lanzados al
  abrir la conexión. Un `OperationalError`/`InterfaceError` durante una
  operación (`execute`), el `commit` o el `rollback` se propagaba crudo.
- **F-02 — detección por nombre exacto.** `_is_unavailable_error` comparaba
  `cls.__name__` contra un `frozenset`, por lo que no reconocía subclases
  reales de psycopg (`CannotConnectNow`, `AdminShutdown`, `CrashShutdown`,
  `ConnectionFailure`, `ConnectionDoesNotExist`, `ConnectionTimeout`).

Corrección aplicada:

- `Database.connection()` traduce los errores del driver lanzados durante el
  `yield`, tanto dentro como fuera de contexto de petición. Fuera de petición,
  el `finally` cierra la conexión y libera el permiso.
- `Database._transaction_scope()` traduce errores del cuerpo, del `commit` y
  del `rollback`. Ante un fallo de `commit` se intenta `rollback` y siempre se
  cierra la conexión fuera de petición.
- `_translate_driver_error()` es idempotente: una `PersistenceUnavailable` no
  se envuelve dos veces.
- `_is_unavailable_error()` usa `isinstance` contra las clases base reales
  `psycopg.OperationalError`/`psycopg.InterfaceError`, importadas de forma
  perezosa. `UniqueViolation`/`IntegrityError` quedan fuera de la traducción.
  Se eliminó `PoolTimeout` (no se usa `psycopg_pool`) y `TooManyConnections`
  (ya cubierto por `OperationalError`).
- No cambian la reutilización por petición, el cierre en teardown, el semáforo
  ni `ensure_schema()`.

## Implementación

| Archivo | Cambio |
|---|---|
| `consultorio/errors.py` | Nueva excepción de dominio `PersistenceUnavailable` (no es `HTTPException`). Sin handler 503 (T9). |
| `consultorio/persistence/database.py` | `DatabaseTarget`, `Database` (`connection`, `transaction`, `ensure_schema`, `close_request`), fábrica por defecto PostgreSQL/SQLite y traducción de errores del driver. Se conservan `get_connection`, `init_db` y la migración SQLite existentes. |
| `consultorio/persistence/__init__.py` | Exporta `Database` y `DatabaseTarget`. |
| `consultorio/__init__.py` | Crea el `Database` desde `app.config`, lo registra en `app.extensions["consultorio.database"]` y añade `teardown_appcontext` que llama `close_request()`. Mantiene `init_db(DATABASE_PATH)`. |
| `tests/test_pg_resilience.py` | Añade los casos de TC-019-002 (26 casos de T3; 44 en el archivo, incluidos los 18 de T2). La corrección F-01/F-02 añade 12 casos: operación en `connection()`, cuerpo/commit/rollback en `transaction()`, seis subclases reales de psycopg y `UniqueViolation` sin traducir. |
| `tests/test_hu_010.py` | La corrección F-01/F-02 no añade imports nuevos; la lista blanca ya se había ampliado en T3 respecto a `HEAD` (T2/T3) y sigue intacta. No se elimina ni relaja ninguna aserción del guard. |

### Diseño de `connection()`

- **Dentro de contexto Flask** (`has_app_context()`): la conexión se guarda en
  `flask.g` por instancia de `Database`; las llamadas siguientes la reutilizan.
  El bloque `with` **no la cierra** al salir. El `teardown_appcontext` llama
  `close_request()`, que la cierra y libera el permiso del semáforo.
- **Fuera de contexto Flask:** cada `connection()` adquiere permiso, abre una
  conexión y la cierra en `finally`.
- **Semáforo:** `threading.BoundedSemaphore(max_connections)` por instancia. Se
  adquiere antes de abrir; si vence `acquire_timeout` se lanza
  `PersistenceUnavailable`. El permiso se libera al cerrar la conexión o al
  fallar la apertura.
- **Sin estado global:** no hay conexión al importar ni al construir `Database`.

### Diseño de `transaction()`

- Dentro de contexto Flask comparte la conexión de la petición (la abre y la
  registra si aún no existía); no la cierra al salir.
- Fuera de contexto abre una conexión propia y la cierra al salir.
- Commit único al terminar sin excepción; `rollback()` completo ante cualquier
  excepción (incluido un fallo del propio `commit`). No deja transacciones
  abiertas.

### Traducción de errores

- `isinstance` contra `psycopg.OperationalError`/`psycopg.InterfaceError`
  (import perezoso) → `PersistenceUnavailable`. Cubre las subclases reales
  `CannotConnectNow`, `AdminShutdown`, `CrashShutdown`, `ConnectionFailure`,
  `ConnectionDoesNotExist` y `ConnectionTimeout`, además de los timeouts y el
  límite de conexiones.
- La traducción se aplica al abrir, durante el `yield` de `connection()`, y en
  el cuerpo/`commit`/`rollback` de `transaction()`. Una `PersistenceUnavailable`
  ya traducida no se envuelve dos veces.
- `UniqueViolation`/`IntegrityError` **no** se capturan como indisponibilidad
  (quedan para T5/T6).
- Los errores ajenos al driver se propagan sin traducir, salvo que el
  `rollback` falle también por driver: en ese caso se lanza
  `PersistenceUnavailable` con el error original en `__context__` (D6).
- `DatabaseTarget`/`Database` no incluyen el DSN en `repr`; los mensajes y logs
  no contienen DSN, contraseña ni PII.

### `ensure_schema()`

- Perezoso, con `threading.Lock` y flag `_schema_ready`.
- SQLite delega en el `init_db` actual.
- PostgreSQL deja un `NotImplementedError` explícito y documentado para T4. No
  se inventa esquema, no se llama desde `create_app` y no se usa en TC-019-002.

## Decisión sobre el uso de fakes

TC-019-002 usa una fábrica de conexiones falsa inyectada en `Database` (con
errores de driver falsos y también con **clases reales de psycopg**:
`CannotConnectNow`, `AdminShutdown`, `CrashShutdown`, `ConnectionFailure`,
`ConnectionDoesNotExist`, `ConnectionTimeout` y `UniqueViolation`). Esto permite
comprobar llamadas reales de apertura/cierre/commit/rollback, el número de
conexiones abiertas y la liberación del semáforo **sin exigir
`TEST_DATABASE_URL` ni PostgreSQL real** en T3. La integración real contra
PostgreSQL llega en T10/T11/T12. No se usa `skip` para ocultar la falta de base
de datos.

## Resultado real de TC-019-002

Comando (`psycopg` 3.3.8; sin DSN):

```powershell
python -m pytest tests/test_pg_resilience.py -v
```

Casos nuevos de la corrección F-01/F-02 (salida literal):

```text
tests/test_pg_resilience.py::test_connection_operation_driver_error_translates_and_releases[OperationalError] PASSED
tests/test_pg_resilience.py::test_connection_operation_driver_error_translates_and_releases[InterfaceError] PASSED
tests/test_pg_resilience.py::test_transaction_body_driver_error_translates_and_rolls_back PASSED
tests/test_pg_resilience.py::test_transaction_commit_driver_error_translates_and_rolls_back PASSED
tests/test_pg_resilience.py::test_transaction_rollback_driver_error_translates PASSED
tests/test_pg_resilience.py::test_real_psycopg_operational_subclasses_translate[CannotConnectNow] PASSED
tests/test_pg_resilience.py::test_real_psycopg_operational_subclasses_translate[AdminShutdown] PASSED
tests/test_pg_resilience.py::test_real_psycopg_operational_subclasses_translate[CrashShutdown] PASSED
tests/test_pg_resilience.py::test_real_psycopg_operational_subclasses_translate[ConnectionFailure] PASSED
tests/test_pg_resilience.py::test_real_psycopg_operational_subclasses_translate[ConnectionDoesNotExist] PASSED
tests/test_pg_resilience.py::test_real_psycopg_operational_subclasses_translate[ConnectionTimeout] PASSED
tests/test_pg_resilience.py::test_real_psycopg_unique_violation_is_not_translated PASSED

============================= 44 passed in 0.69s ==============================
```

El archivo contiene los 18 casos de TC-019-001 de T2 y 26 casos de TC-019-002
(14 originales de T3 + 12 de la corrección). No se usa `skip`.

### Comprobación manual con driver real

Sin escribir en la base, se intentó abrir una conexión a un puerto local
cerrado con `DatabaseTarget` y `Database`:

```text
translated: PersistenceUnavailable
cause: ConnectionTimeout
```

El error real del driver (`ConnectionTimeout`, subclase de
`psycopg.OperationalError`) se tradujo a `PersistenceUnavailable`.

## Conteo de conexiones y semáforo observado

| Escenario | Observación real del test |
|---|---|
| Dos `connection()` en la misma petición | 1 apertura, misma instancia devuelta, 0 cierres al salir de los `with` |
| `teardown_appcontext` / `close_request()` | 1 cierre después del teardown; segunda llamada idempotente sin cierre extra |
| Dos operaciones fuera de petición | 2 aperturas y 2 cierres, instancias distintas |
| `transaction()` con éxito | 1 apertura, 1 `commit`, 0 `rollback`, cierre al salir |
| `transaction()` con excepción | 1 apertura, 0 `commit`, 1 `rollback`, cierre al salir |
| Semáforo con `max_connections=1` y `acquire_timeout=0.05` | La segunda adquisición lanza `PersistenceUnavailable`; tras cerrar la primera, la siguiente operación vuelve a adquirir permiso |
| Error de driver simulado al abrir | `PersistenceUnavailable` (no `slot_taken`); el permiso se libera y la siguiente operación funciona |
| Error de driver en `execute` dentro de `connection()` | `PersistenceUnavailable`; la conexión se cierra y el permiso se libera |
| Error de driver en el cuerpo de `transaction()` | `PersistenceUnavailable`; 0 `commit`, 1 `rollback`, cierre |
| Error de driver en `commit` | `PersistenceUnavailable`; se intenta 1 `rollback` y se cierra |
| Error de driver en `rollback` | `PersistenceUnavailable`; el fallo de limpieza no se propaga crudo |
| Subclases reales de psycopg (`CannotConnectNow`, `AdminShutdown`, `CrashShutdown`, `ConnectionFailure`, `ConnectionDoesNotExist`, `ConnectionTimeout`) | `PersistenceUnavailable` |
| `UniqueViolation` real | Se propaga como `UniqueViolation`, no como indisponibilidad; el permiso se libera |
| Sin `DATABASE_URL` | `create_app()` arranca; el primer `connection()` lanza `PersistenceUnavailable` |

## Suite completa

Comando:

```powershell
python -m pytest -q
```

Resultado real:

```text
364 passed in 41.39s
```

Baseline previo a la corrección: 352 PASS. Los 12 casos nuevos de F-01/F-02
elevan el total a **364 PASS / 0 FAIL**, sin regresiones. No se usa `skip`.

## Confirmaciones de alcance

- No se modificaron repositorios, servicios, blueprints ni plantillas.
- No se añadió el handler HTTP 503 ni la plantilla de indisponibilidad (T9).
- No se implementó DDL PostgreSQL, advisory lock ni arranque perezoso (T4).
- No se cambió ningún literal contractual ni `tests/expected_content.py`.
- No se añadieron dependencias (`psycopg` ya fue añadido en T2).
- No se creó ninguna conexión al importar módulos ni al construir `Database`.
- No se hizo commit ni push.
- La evidencia no contiene DSN, credenciales ni PII.

## Observaciones no bloqueantes de la revisión

- Falta un test automatizado de error de driver dentro de un contexto Flask;
  la rama se verificó manualmente y puede cubrirse en T11/T12.
- Persiste el riesgo de T2 sobre un `sslmode` duplicado en el DSN; endurecer la
  validación antes de T14.
- La integración real con PostgreSQL y la suite completa contra el motor son
  T10/T11/T12, no T3.
