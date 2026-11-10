# Evidencia T5 — Repositorios de citas y eventos en PostgreSQL

> Trazabilidad: **Spec 019** (`RF-4`, `RF-6`, `RF-7`, `RF-10`, `RF-11`,
> `RF-12`, `RF-14`, `RF-30`; `CL-8`) → `plan.md` (D5, D7, D8, D13; §3) →
> `tasks.md` **T5** → código → tests → esta evidencia.
> Fecha de ejecución: **2026-11-09**. Rama `feature/hu-019-migracion-postgres`.
> PostgreSQL real: **16.15** (`consultorio-pg-019`, `127.0.0.1:55432`).

## Alcance

- `consultorio/persistence/appointments_repository.py`
- `consultorio/persistence/automation_events_repository.py`
- `consultorio/persistence/database.py` (solo defaults SQLite de
  `created_at` alineados a UTC, D7/RF-30)
- `tests/test_pg_persistence.py` (nuevo)
- `tests/test_hu_019.py` (nuevo)
- `tests/test_hu_010.py` (lista blanca de imports del guard, justificada)
- `docs/operaciones/postgresql.md` (adaptador SQLite y convivencia)

No se modificó `specs/` en T5; las enmiendas 004/005/006/010 presentes en el
worktree son aprobadas y anteriores a esta tarea. No se implementó T6+ y no se
hizo commit ni push.

## Comandos ejecutados

Sesión de PowerShell (el DSN real no se escribe en la evidencia):

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"

python -m pytest -v tests/test_pg_persistence.py tests/test_hu_019.py
python -m pytest -q
```

## TC-019-006 / TC-019-007 / TC-019-017 / TC-019-013 / TC-019-015

Salida literal:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Jaz\Documents\Proyectos Python\Consultorio_Carolina
collecting ... collected 8 items

tests/test_pg_persistence.py::test_tc_019_006_appointments_repository_contract PASSED [ 12%]
tests/test_pg_persistence.py::test_tc_019_006_sql_sent_to_postgres_uses_percent_s_and_returning PASSED [ 25%]
tests/test_pg_persistence.py::test_tc_019_007_events_repository_dedup_and_claim PASSED [ 37%]
tests/test_pg_persistence.py::test_tc_019_007_claim_failed_event_retryability_patterns PASSED [ 50%]
tests/test_pg_persistence.py::test_tc_019_017_created_at_and_sent_at_are_utc PASSED [ 62%]
tests/test_hu_019.py::test_tc_019_013_slot_integrity_and_cancelled_release PASSED [ 75%]
tests/test_hu_019.py::test_tc_019_015_event_dedup_single_row_without_second_send PASSED [ 87%]
tests/test_hu_019.py::test_sqlite_rollback_route_keeps_repository_contract PASSED [100%]

============================== 8 passed in 2.54s ==============================
```

Qué comprueba cada caso:

| TC | RF/CL | Comprobación real |
|---|---|---|
| TC-019-006 | RF-4, RF-5, RF-6, RF-10, RF-11, RF-14; CL-8 | `INSERT ... RETURNING id` real, `%s` en las sentencias enviadas a PostgreSQL, `rowcount` en `UPDATE`, disponibilidad excluye `cancelled`, el índice parcial bloquea duplicados activos y cancelar libera el horario. |
| TC-019-007 | RF-7, RF-12, RF-30 | `UNIQUE(event_id)`, segundo `insert_event()` → `False` con una sola fila, `mark_sent()` con `sent_at` UTC, `claim_failed_event()` con `rowcount` y patrones permanente/retryable. |
| TC-019-017 | RF-30 | `created_at` y `sent_at` con formato `YYYY-MM-DD HH:MM:SS` y reloj UTC; sin conversión a `America/Bogota`. |
| TC-019-013 | RF-10, RF-11 | Duplicado directo en slot activo falla en el motor; el slot confirmado sigue bloqueado; tras cancelar se puede re-reservar. |
| TC-019-015 | RF-12 | Dedup de eventos: segundo `insert_event` `False`, una sola fila y sin reiniciar el estado del evento ya enviado. |
| SQLite rollback | RF-4, RF-7, RF-12 | Las mismas funciones con `database_path` legado y con `Database(backend="sqlite")` conservan el contrato. |

## Catálogos reales de PostgreSQL

Esquema temporal `evidence_t5_20261109`, creado con `Database.ensure_schema()`
y eliminado con `DROP SCHEMA ... CASCADE` al terminar. **No se tocó `public`.**

### Índice único parcial

```sql
SELECT indexname, indexdef FROM pg_indexes
 WHERE schemaname = 'evidence_t5_20261109'
   AND indexname = 'ux_appointments_slot_open';
```

```text
         indexname         |                                                                          indexdef
---------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------
 ux_appointments_slot_open | CREATE UNIQUE INDEX ux_appointments_slot_open ON evidence_t5_20261109.appointments USING btree (service, date, "time") WHERE (status <> 'cancelled'::text)
(1 row)
```

### `UNIQUE(event_id)`

```sql
SELECT conname, pg_get_constraintdef(c.oid) AS definition
  FROM pg_constraint c
  JOIN pg_class t ON t.oid = c.conrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
 WHERE n.nspname = 'evidence_t5_20261109'
   AND t.relname = 'automation_events' AND c.contype = 'u';
```

```text
            conname             |    definition
--------------------------------+-------------------
 automation_events_event_id_key | UNIQUE (event_id)
(1 row)
```

### Columnas y defaults UTC

```sql
SELECT table_name, column_name, data_type, column_default
  FROM information_schema.columns
 WHERE table_schema = 'evidence_t5_20261109'
   AND ((table_name = 'appointments' AND column_name = 'created_at')
     OR (table_name = 'automation_events' AND column_name IN ('created_at','sent_at')))
 ORDER BY table_name, column_name;
```

```text
    table_name     | column_name | data_type |                              column_default
-------------------+-------------+-----------+--------------------------------------------------------------------------
 appointments      | created_at  | text      | to_char((now() AT TIME ZONE 'UTC'::text), 'YYYY-MM-DD HH24:MI:SS'::text)
 automation_events | created_at  | text      | to_char((now() AT TIME ZONE 'UTC'::text), 'YYYY-MM-DD HH24:MI:SS'::text)
 automation_events | sent_at     | text      |
(3 rows)
```

## Formato UTC real

Filas escritas con los repositorios (`insert_appointment`, `insert_event`,
`mark_sent`) en el esquema temporal:

```text
appointments.created_at = 2026-11-09 17:25:29
automation_events.created_at = 2026-11-09 17:25:30
automation_events.sent_at = 2026-11-09 17:25:30
```

Comparación directa del reloj del servidor:

```sql
SELECT now() AT TIME ZONE 'UTC' AS utc_now,
       now() AT TIME ZONE 'America/Bogota' AS bogota_now;
```

```text
          utc_now           |         bogota_now
----------------------------+----------------------------
 2026-11-09 17:25:35.719894 | 2026-11-09 12:25:35.719894
(1 row)
```

Las marcas almacenadas coinciden con `utc_now`, no con `bogota_now`
(RF-30; plan D7). No hay conversión a `America/Bogota` en esta fase.

## Suite completa

Tras la corrección previa a la revisión (ver más abajo):

```text
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 57%]
........................................................................ [ 76%]
........................................................................ [ 95%]
..................                                                       [100%]
378 passed in 35.61s
```

- Baseline previo: **369 PASS / 0 FAIL**.
- Nuevos: **9 tests** (5 en `test_pg_persistence.py` y 4 en
  `test_hu_019.py`), todos contra PostgreSQL real salvo el de rollback SQLite.
- Sin `skip` ni `xfail`; si falta `TEST_DATABASE_URL`, las fixtures fallan con
  instrucciones (D9/CL-10).
- Cada test usa un esquema temporal `test_hu019_<uuid>` y no toca `public` ni
  datos de desarrollo.

## Corrección previa a la revisión (detectada por el coordinador)

Esta corrección se hizo antes de enviar T5 a `@revisor`; no sustituye la
revisión técnica ni implica aprobación.

**Defecto:** `_scope()` creaba internamente `Database(resource)` cuando recibía
un `DatabaseTarget`. Dentro de un contexto Flask, `Database.connection()`/
`transaction()` guarda la conexión en `flask.g`, pero el teardown solo llama
`close_request()` sobre la instancia registrada en `app.extensions`, no sobre
esa instancia temporal. Quedaban sin cerrar la conexión y el permiso del
semáforo (RF-17/D3), con posible reutilización inesperada por reutilización de
`id()` en `g`.

**Corrección:** `_scope()` distingue ahora el `Database` propiedad del llamador
(`owned=False`, no se cierra) del `Database` creado por el repositorio desde un
`DatabaseTarget` (`owned=True`). Para este último, `_scope()` llama a
`close_request()` en un `finally`, por lo que se cierra también si
`ensure_schema()`, la operación o el commit lanzan una excepción. Fuera de
contexto Flask, `close_request()` es no-op y el cierre lo sigue haciendo
`transaction()`/`connection()`; no hay doble cierre. La API pública y el
comportamiento con `database_path`/`Database` no cambian.

**Regresión:** `test_t5_target_scope_closes_connection_in_app_context` usa un
`DatabaseTarget` PostgreSQL dentro de `app.app_context()` y consulta el estado
público del servidor (`pg_stat_activity`, filtrando la conexión observadora).
Comprueba el conteo tras escrituras y lecturas de citas y eventos, y tras una
excepción (`UniqueViolation`). Verificación de no vacuidad: al desactivar
temporalmente el cierre, el test falló con `assert 1 <= 0`; con la corrección
pasa.

```text
python -m pytest -q tests/test_pg_persistence.py tests/test_hu_019.py
.........                                                                [100%]
9 passed in 3.10s
```

El permiso del semáforo se libera en la misma ruta pública `close_request()`
(`_close_connection()`); no se inspeccionan atributos privados en el test.

## Nota sobre T4 y los defaults SQLite

T4 conservó el DDL SQLite de rollback y, en su cierre, registró
`datetime('now','localtime')` porque la alineación UTC correspondía a T5/T6
(ver `docs/evidencias/hu-019/schema.md`). T5 cambió **solo** los defaults SQLite
de `created_at` (dos en `SCHEMA` y uno en `APPOINTMENTS_TABLE_SQL`) a
`datetime('now')`, que es UTC y mantiene el formato `YYYY-MM-DD HH:MM:SS`
(D7/RF-30). El resto del DDL de T4 (tablas, índice parcial, advisory lock,
bootstrap perezoso) permanece intacto. No se modificó `schema.md`.

## Notas y riesgos

- El adaptador SQLite es **mínimo y controlado** (`%s` → `?`); no hay dos juegos
  completos de consultas ni un traductor general (D8).
- `insert_event()` solo captura `psycopg.errors.UniqueViolation` en PostgreSQL
  (y `sqlite3.IntegrityError` en la ruta de rollback). Otros errores se
  propagan; no se añadieron reglas de negocio ni mensajes de usuario.
- Los servicios web todavía pasan `database_path` hasta T6; los repositorios
  aceptan ambos recursos de forma transitoria (D13).
- `RETURNING id` en la ruta SQLite requiere SQLite ≥ 3.35; la suite local con
  Python 3.14.8 lo verifica. La versión de SQLite de Render se comprobará en
  T14/T15, no en T5.
- Una base SQLite preexistente no cambia el default de `created_at` con
  `CREATE TABLE IF NOT EXISTS`; T15 deberá considerarlo para el rollback.
- `mark_skipped()` y la atomicidad real de
  `update_appointment_status_with_pending_event()` se cubren en T11 y T7,
  respectivamente; T5 verifica su SQL y contrato, no el flujo completo.
- La afirmación histórica de `schema.md` sobre `localtime` corresponde al
  cierre de T4; esta evidencia documenta el cambio posterior de T5 y no se
  reescribe el documento aprobado de T4.

## Revisión técnica

- **Dictamen:** **APROBADO** por `@revisor` (2026-11-09).
- **Alcance revisado:** T5, RF-4, RF-5, RF-6, RF-7, RF-10, RF-11, RF-12,
  RF-14, RF-30 y CL-8, con las dependencias de T6/T7/T11/T12/T15 declaradas
  como pendientes de esas tareas.
- **Evidencia de la revisión:** `9 passed` en los tests T5 y **378 passed** en
  la suite completa, contra PostgreSQL 16.15 real y sin `skip`.
- **Defectos bloqueantes:** ninguno.
- **Observaciones no bloqueantes:** actualizar la nota de `schema.md` sobre
  `localtime`; añadir RF-5 a la fila de TC-019-006 (hecho); precisar los tres
  defaults SQLite (hecho); aclarar las enmiendas previas de `specs/` (hecho);
  limpiar el `import sqlite3` sin uso en `appointments_repository.py`; ajustar
  el docstring de `insert_event()`; validar SQLite ≥ 3.35 y bases preexistentes
  en T14/T15; completar la cobertura de `mark_skipped` y de la atomicidad en
  T11/T7.
- **Estado:** T5 completada y aprobada técnicamente. **T6+ no autorizadas.** No
  hay aceptación funcional de la usuaria ni commit/push.
