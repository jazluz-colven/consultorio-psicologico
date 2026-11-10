# Evidencia T7 — Atomicidad de la cancelación (Spec 010) en 017/018

- **Fecha:** 2026-11-10
- **Rama:** `feature/hu-019-migracion-postgres`
- **HEAD:** `8ce511f` (sin commit ni push durante T7)
- **Ámbito:** T7 de `specs/019_migrar-postgresql/tasks.md`.
- **Resultado:** **PASS del alcance T7** (atomicidad de la cancelación y
  delegación 017/018). TC-019-009 (3 pruebas) y la regresión 017/018 en verde;
  suite completa `385 passed`, sin `skip`, `skipif` ni `xfail`. La **paridad
  total de la suite contra PostgreSQL no se declara demostrada**: los tests
  legacy siguen usando fixtures SQLite hasta T10/T11/T12 (ver §3.4 y §6).

## 1. Alcance y trazabilidad

| Elemento | Referencia |
|---|---|
| Spec | `specs/019_migrar-postgresql/spec.md` |
| Requisitos | RF-8 (paridad cancelación/notificación), RF-9 (paridad 018), RF-13 (transición + evento `pending` atómicos) |
| Decisión de diseño | D5 (transacciones y atomicidad de la Spec 010) |
| Tarea | T7 |
| Matriz de pruebas | TC-019-009 (`tests/test_pg_persistence.py`) |
| Flujos afectados | 010 (servicio centralizado), 017 (paciente), 018 (consultorio) |

Criterios de aceptación:

- [x] `update_appointment_status_with_pending_event()` usa la misma conexión y
  la misma transacción para el `UPDATE` y el `INSERT` del evento.
- [x] Si el `INSERT` del evento falla, se hace rollback: la cita sigue
  `confirmed` y no queda evento huérfano.
- [x] El commit es único; la publicación del evento de negocio y el correo
  ocurren después del commit y no se ejecutan si el `INSERT` falla.
- [x] Los flujos 017 y 018 siguen delegando en el servicio centralizado, sin
  lógica de persistencia propia.
- [x] No quedan imports de `sqlite3` en `consultorio/services/`.
- [ ] **Parcial/pendiente:** los tests PostgreSQL activos (incluidos
  TC-019-009) se ejecutan contra PostgreSQL real y la suite completa da
  `385 passed` sin `skip`; **la paridad total de la suite contra PostgreSQL no
  está demostrada en T7**, porque los tests legacy siguen usando fixtures
  SQLite hasta T10/T11/T12.

## 2. Cambios de producción

**No fue necesario modificar código de producción.** La implementación de T5/T6
ya cumplía D5 y RF-13:

- `consultorio/persistence/appointments_repository.py`
  `update_appointment_status_with_pending_event()` ejecuta el `UPDATE` y el
  `INSERT` dentro de un único `_scope(..., write=True)`, que resuelve a
  `Database.transaction()` sobre la misma conexión.
- `Database._transaction_scope()` hace un único `commit()` al salir o un
  `rollback()` completo si algo falla, y propaga el error.
- `appointment_service.cancel_appointment()` llama a la publicación
  (`automation_service.publish_cancelled_event`) y al correo
  (`email_service.send_cancellation`) **después** de que la función de
  persistencia haya retornado, es decir, después del commit.
- `cancellation_flow_service.cancel_verified_request()` y los blueprints
  `web/cancellation.py` y `web/admin.py` solo delegan; no contienen SQL ni
  transiciones propias.

T7 añade la prueba que demuestra esas propiedades con un fallo real del motor.

## 3. Comandos ejecutados y resultados literales

La sesión define `TEST_DATABASE_URL` con el DSN local del contenedor
(`127.0.0.1:55432`). El valor con contraseña no se registra en esta evidencia.
Las ejecuciones finales documentadas aquí se hicieron solo con esa variable. En
comprobaciones previas de la tarea se usó `PSYCOPG_IMPL=python` y el `libpq`
local, según `docs/operaciones/postgresql.md`.

### 3.1 TC-019-009 aislado

```powershell
$env:TEST_DATABASE_URL='<DSN local; no registrado>'
python -m pytest -q tests/test_pg_persistence.py -k tc_019_009 -v
```

```text
collected 10 items / 7 deselected / 3 selected
tests\test_pg_persistence.py ...                                         [100%]
======================= 3 passed, 7 deselected in 1.32s ========================
```

### 3.2 Pruebas obligatorias de T7

```powershell
$env:TEST_DATABASE_URL='<DSN local; no registrado>'
python -m pytest -q tests/test_pg_persistence.py tests/test_cancellation_service.py tests/test_hu_018.py
```

```text
.............................................................            [100%]
61 passed in 16.54s
```

Ejecución final con el comando obligatorio exacto (solo
`TEST_DATABASE_URL` en la sesión, sin variables adicionales).

### 3.3 Regresión ampliada 017/018

```powershell
$env:TEST_DATABASE_URL='<DSN local; no registrado>'
python -m pytest -q tests/test_hu_017.py tests/test_cancellation_flow_service.py tests/test_hu_018.py tests/test_cancellation_service.py
```

```text
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 17.03s
```

La delegación sin lógica propia ya está cubierta por:

- `tests/test_cancellation_flow_service.py::test_tc_017_011_cancellation_flow_service_delega_sin_logica_propia`
  (inspección de fuente: delega en `cancel_appointment()` y no contiene SQL ni
  notificaciones propias).
- `tests/test_cancellation_flow_service.py::test_tc_017_004_delega_con_la_configuracion_recibida`
  (`cancel_appointment` se invoca una vez con los mismos argumentos).
- `tests/test_hu_018.py::test_tc_018_018_orden_cancelar_antes_de_crear`
  (el admin invoca `cancel_appointment` y después `create_booking`).

### 3.4 Suite completa (resultado global; no equivale a paridad PostgreSQL)

Ejecución realizada con el comando obligatorio exacto:

```powershell
$env:TEST_DATABASE_URL='<DSN local; no registrado>'
python -m pytest -q
```

```text
........................................................................ [ 18%]
........................................................................ [ 37%]
........................................................................ [ 56%]
........................................................................ [ 74%]
........................................................................ [ 93%]
.........................                                                [100%]
385 passed in 50.16s
```

Una corrida previa con `python -m pytest -q -rs` dio `385 passed in 51.83s` y
no imprimió ninguna línea de `SKIPPED`. La búsqueda de marcadores en `tests/`
(`pytest.mark.skip`, `pytest.mark.skipif`, `pytest.mark.xfail`,
`pytest.skip(`) no devolvió resultados.

**Alcance de este resultado:** los tests PostgreSQL activos (incluidos los 3 de
TC-019-009) se ejecutan contra el servidor real y la suite completa pasa sin
`skip`; los tests legacy siguen usando las fixtures SQLite hasta T10/T11/T12.
Por tanto, `385 passed` acredita ausencia de regresiones y de skips, **no** que
toda la suite se ejecute en PostgreSQL.

## 4. TC-019-009 — detalle de las pruebas

### 4.1 Misma conexión y un único commit

`test_tc_019_009_update_and_event_share_connection_and_single_commit` usa una
fábrica de conexiones que registra el identificador de cada conexión y cada
sentencia/commit. Afirma:

1. El `UPDATE appointments SET status ...` y el
   `INSERT INTO automation_events ...` se ejecutan en la **misma** conexión.
2. Esa conexión hace **exactamente un** `commit`, después de ambas sentencias.
3. No hay ningún `rollback` en el camino feliz.

### 4.2 Fallo REAL del `INSERT` del evento y rollback

`test_tc_019_009_real_event_insert_failure_rolls_back_cancellation` no simula el
fallo con un mock del repositorio. Inserta previamente un evento con el mismo
`event_id` determinista que usará la cancelación
(`appointment.cancelled:<id>:v1`), de modo que el `INSERT` real dentro de la
transacción viola `UNIQUE(event_id)` en el motor.

La excepción capturada es `psycopg.errors.UniqueViolation` con
`diag.constraint_name == "automation_events_event_id_key"`, es decir, el fallo
ocurre en el `INSERT` del evento.

**Salida ilustrativa/representativa (no es salida literal de pytest).** El test
no imprime este bloque: se construye a partir de las consultas y aserciones del
test (misma conexión independiente, mismos campos) y los hechos que refleja sí
están asertados. Esquema aislado; datos ficticios, sin PII real.

```text
=== A) Fallo real del INSERT (event_id duplicado) ===
exception: UniqueViolation
constraint: automation_events_event_id_key
preexisting event id: 1
appointments: [{'id': 1, 'status': 'confirmed'}]
automation_events: [{'id': 1, 'event_id': 'appointment.cancelled:1:v1', 'appointment_id': 1, 'status': 'pending'}]
```

Interpretación:

- `appointments.status` sigue siendo `confirmed`: el `UPDATE` revirtió.
- `automation_events` contiene solo la fila preexistente (id 1). No aparece una
  segunda fila huérfana con un id nuevo.
- Los espías de `publish_cancelled_event` y `send_cancellation` no se invocan
  (`assert_not_called()`).

### 4.3 Publicación posterior al commit

`test_tc_019_009_publication_runs_only_after_commit` intercepta
`automation_service.publish_cancelled_event` y
`email_service.send_cancellation`. Cada espía consulta, en el instante en que
se le invoca, la cita y sus eventos desde una **conexión independiente**.

**Salida ilustrativa/representativa (no es salida literal de pytest).** El test
no imprime este bloque: se construye a partir de las consultas y aserciones del
test (snapshots tomados desde conexiones independientes) y los hechos que
refleja sí están asertados. Esquema aislado; datos ficticios.

```text
=== B) Snapshots de publicación (después del commit) ===
at publish_cancelled_event -> appointments: [{'id': 2, 'status': 'cancelled'}]
at publish_cancelled_event -> automation_events: [{'id': 3, 'event_id': 'appointment.cancelled:2:v1', 'appointment_id': 2, 'status': 'pending'}]
at send_cancellation -> appointments: [{'id': 2, 'status': 'cancelled'}]
at send_cancellation -> automation_events: [{'id': 3, 'event_id': 'appointment.cancelled:2:v1', 'appointment_id': 2, 'status': 'pending'}]
publish calls: 1 | email calls: 1
result status: cancelled
final appointments: [{'id': 2, 'status': 'cancelled'}]
final automation_events: [{'id': 3, 'event_id': 'appointment.cancelled:2:v1', 'appointment_id': 2, 'status': 'pending'}]
```

Interpretación:

- En el momento de invocar la publicación, la cita ya es `cancelled` y el
  evento `pending` ya es visible desde otra conexión: el commit ya ocurrió.
- El orden es evento de negocio y después correo.
- Los espías no publican de verdad, por eso la fila permanece `pending` y sin
  `sent_at`; la prueba no depende de la red.
- El `SELECT` del `UPDATE`/`INSERT` y el commit de la transacción no podrían ser
  observados desde otra conexión antes del commit; por tanto no hay publicación
  anticipada.

## 5. Criterio de servicios sin `sqlite3`

Búsqueda en `consultorio/services/`:

```text
sqlite3 -> No files found
```

Los servicios no importan ni capturan `sqlite3`; la traducción de errores del
driver vive en `consultorio/persistence/database.py`.

## 6. Límites y pendientes

- T8 (literal `MSG_PERSISTENCE_UNAVAILABLE`), T9 (503/UX) y T10 (migración
  completa de la suite a PostgreSQL) **no** se han implementado, conforme a la
  autorización de T7.
- La suite completa ejecuta los tests PostgreSQL activos contra el servidor
  real y da `385 passed` sin `skip`, pero **la paridad total de la suite contra
  PostgreSQL no está demostrada en T7**: los tests legacy que todavía usan las
  fixtures SQLite seguirán así hasta T10/T11/T12. La paridad completa
  (TC-019-012) queda pendiente y no se declara en esta evidencia.
- T7 no modifica `specs/`, `MEMORY.md` ni literales contractuales. Los cambios
  que aparecen en `git status` para `specs/004,005,006,010` y `MEMORY.md` son
  preexistentes de T2–T6, no de esta tarea.
- No se ha hecho commit ni push.
- No se incluyen credenciales, DSN con contraseña, datos de pacientes reales ni
  PII. Los datos de los volcados son ficticios.

## 7. Archivos tocados por T7

- `tests/test_pg_persistence.py` — se añaden TC-019-009 y su helper de lectura
  desde conexión independiente (el archivo ya existía como untracked de T5).
- `docs/evidencias/hu-019/t7-atomicity.md` — este documento.

> Nota de revisión (2026-11-10): la corrección solicitada por el revisor es
> exclusivamente documental sobre este archivo. No se modificaron código,
> tests, `specs/` ni `MEMORY.md`, y no hubo commit ni push.
