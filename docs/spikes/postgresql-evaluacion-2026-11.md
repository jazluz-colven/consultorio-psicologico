# Spike técnico — Evaluación de PostgreSQL (2026-11-07)

> **Estado: SPIKE AISLADO Y DESECHABLE.** No es una HU, no es una migración
> definitiva y no debe mergearse tal cual. Todo el prototipo vive únicamente
> en el worktree `C:\Users\Jaz\AppData\Local\Temp\opencode\spike-postgres`,
> rama `spike/postgres-evaluacion` (base `main` = `9846613`), sin commit ni push.

## 1. Contexto y alcance

- Decisión de la usuaria (2026-11-07): evaluar PostgreSQL en **modalidad B
  (prototipo aislado)**.
- Alcance: **Render Postgres** y **Neon** como destino; en este spike solo se
  ejecutó PostgreSQL 16 **local en Docker**, porque el entorno no tiene acceso
  a esas cuentas cloud.
- Confirmado por la usuaria: **no hay datos reales de pacientes que migrar**.
- Objetivo: demostrar o refutar con evidencia ejecutada que el código actual
  puede funcionar sobre PostgreSQL sin perder las garantías de integridad, y
  medir el esfuerzo de una migración real.
- Fuera de alcance: migración definitiva, cambios en `specs/`, cambios en
  `requirements.txt`/`render.yaml`, commit/push.

## 2. Entorno y versiones verificadas

| Elemento | Versión / valor | Cómo se verificó |
|---|---|---|
| Worktree | `C:\Users\Jaz\AppData\Local\Temp\opencode\spike-postgres` | `Test-Path`, `git status` |
| Rama | `spike/postgres-evaluacion` | `git status --short --branch` |
| Base | `9846613` (`main`) | `git log --oneline -1` |
| Python | 3.14.8 | `python --version` |
| pytest | 9.1.1 | salida de pytest |
| psycopg | **3.3.8** (`psycopg[binary]`, wheel `cp314`) | `python -c "import psycopg; print(psycopg.__version__)"` |
| Docker Engine (server) | 29.9.2 | `docker version --format '{{.Server.Version}}'` |
| Imagen | `postgres:16-alpine` | `docker pull` |
| Servidor PostgreSQL | **16.15** (`x86_64-pc-linux-musl`) | `SHOW server_version` / `SELECT version()` |
| Contenedor | `spike-pg`, host `55432` → `5432` | `docker ps` |
| Base / usuario | `consultorio_spike` / `spike` | `SELECT current_database(), current_user` |
| Credencial | contraseña local de usar y tirar (no se documenta) | — |

> **F-08 (nota):** el DSN por defecto de `tests/conftest.py` contiene una
> contraseña local de usar y tirar (`spike_local_only`), sin datos de pacientes.
> Es exclusiva de este spike y **no debe reutilizarse fuera del spike** ni
> promoverse a ningún entorno real.

Salida relevante:

```text
psycopg 3.3.8
16.15
PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
spike-pg | postgres:16-alpine | Up ... | 0.0.0.0:55432->5432/tcp
```

Comandos principales (sin la contraseña real):

```powershell
docker pull postgres:16-alpine
docker run -d --name spike-pg `
  -e POSTGRES_USER=spike `
  -e POSTGRES_PASSWORD=<local-throwaway> `
  -e POSTGRES_DB=consultorio_spike `
  -p 55432:5432 postgres:16-alpine

$env:SPIKE_DB_BACKEND = "postgres"
$env:SPIKE_PG_DSN = "host=localhost port=55432 user=spike password=<local-throwaway> dbname=consultorio_spike"
python -m pytest -q tests/test_spike_postgres_critical.py
```

## 3. Inventario SQLite-específico y traducción a PostgreSQL

Inventario completo de lo detectado en `consultorio/persistence/*.py` y
`consultorio/services/appointment_service.py` (búsqueda con `grep` sobre
`sqlite3`, `sqlite_master`, `PRAGMA`, `lastrowid`, `datetime('now'`, etc.):

| Constructo SQLite | Ubicación | Traducción PostgreSQL | Estado en el spike |
|---|---|---|---|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `database.py` (tablas `appointments` y `automation_events`) | `BIGSERIAL PRIMARY KEY` (o `GENERATED … AS IDENTITY`) | Funciona |
| `datetime('now', 'localtime')` | `database.py` (defaults de `created_at`), `automation_events_repository.py::mark_sent` | `to_char(now(), 'YYYY-MM-DD HH24:MI:SS')` manteniendo columna `TEXT` | Funciona; ojo: `now()` es UTC en el contenedor, `localtime` era local |
| `sqlite_master` | `database.py` (migración legado) y tests HU-006/HU-007 | `pg_indexes` / `information_schema.columns` | Emulado; tests pasan |
| `PRAGMA table_info/index_list/index_info` | tests de esquema | catálogo `information_schema` / `pg_index` | Emulado; tests pasan |
| `sqlite3.Row` | `_to_appointment`, `_to_event` | `Row` con acceso por índice y por nombre | Funciona |
| `sqlite3.IntegrityError` | `automation_events_repository.insert_event`, `appointment_service.create_booking` | `psycopg.errors.IntegrityError` / `UniqueViolation` | Traducido a `sqlite3.IntegrityError`; el servicio no se tocó |
| `sqlite3.OperationalError` | `appointment_service.create_booking` | `psycopg.errors.OperationalError` | Traducido a `sqlite3.OperationalError`; no se disparó en el camino feliz |
| `BEGIN` / `COMMIT` manuales | `database.py::_migrate_appointment_uniqueness` | Transacción implícita de psycopg (`autocommit=False`) + `commit/rollback` | No aplica en PG; la migración legado SQLite se omite |
| Placeholders `?` | todos los repositorios y servicios | `%s` | Traducido en la capa de conexión |
| `cursor.lastrowid` | `appointments_repository.insert_appointment` | `INSERT … RETURNING id` | Emulado; devuelve el id real |
| `executescript` | `database.py::init_db` | Ejecución sentencia a sentencia / DDL propio de PG | Emulado |
| Índice único parcial `ux_appointments_slot_open … WHERE status <> 'cancelled'` | `database.py` | Misma sintaxis en PostgreSQL | **Funciona y se verificó** |
| Respaldo de fichero con `shutil.copy2` | `database.py` (migración legado) | N/A (no hay fichero gestionado por la app) | Fuera de alcance PG |
| Orden de captura `HTTPError` antes de `URLError` (D-010-01) | `automation_service.py` | No es SQLite: jerarquía de excepciones de `urllib` | Sin cambios; los tests de D-010-01 pasan (no se degradó) |

`rowcount` (usado por `update_appointment_status`, `claim_failed_event` y el
reproceso) se mantiene: psycopg lo devuelve para `UPDATE`.

### 3.1 Esquema PostgreSQL utilizado

Se mantuvieron `created_at`/`sent_at` como `TEXT` para **no romper la firma de
los dataclasses ni los tests**; no fue necesario introducir `TIMESTAMP` en este
spike. DDL efectivo:

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
    created_at      TEXT NOT NULL DEFAULT (to_char(now(), 'YYYY-MM-DD HH24:MI:SS'))
);

CREATE TABLE IF NOT EXISTS automation_events (
    id              BIGSERIAL PRIMARY KEY,
    event_id        TEXT NOT NULL UNIQUE,
    event_type      TEXT NOT NULL,
    event_version   INTEGER NOT NULL,
    appointment_id  INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    detail          TEXT,
    created_at      TEXT NOT NULL DEFAULT (to_char(now(), 'YYYY-MM-DD HH24:MI:SS')),
    sent_at         TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_appointments_slot_open
ON appointments(service, date, time) WHERE status <> 'cancelled';
```

Definición real leída desde PostgreSQL en una ejecución de evidencia:

```text
CREATE UNIQUE INDEX ux_appointments_slot_open
ON spike_evidence_xxxxxxxx.appointments
USING btree (service, date, "time")
WHERE (status <> 'cancelled'::text)
```

## 4. Adaptación mínima del prototipo

Se añadió una capa **paralela y parametrizada**; **no se duplicó la lógica de
negocio** (servicios y repositorios son los mismos):

- **Nuevo** `consultorio/persistence/pg_adapter.py` (511 líneas, desechable):
  - `PGTarget(dsn, schema)` identifica un DSN y un esquema aislado por test.
  - `PGConnection` / `PGCursor` emulan el subconjunto de DB-API de `sqlite3`
    que usa el proyecto (`execute`, `executemany`, `executescript`,
    context manager con `commit/rollback`, `rowcount`, `lastrowid`, `Row`).
  - Traduce `?` → `%s`, `datetime('now','localtime')`, `sqlite_master` y los
    `PRAGMA` usados por los tests.
  - Traduce `psycopg.errors.IntegrityError`/`OperationalError` a
    `sqlite3.IntegrityError`/`OperationalError` para no tocar los `except` de
    los servicios.
  - `INSERT` sin `RETURNING` se reescribe a `INSERT … RETURNING id` para
    reconstruir `lastrowid`.
- `consultorio/persistence/database.py`: `get_connection()` e `init_db()`
  delegan en el adaptador cuando el destino es PostgreSQL; la ruta SQLite
  original se conserva intacta.
- `consultorio/web/appointments.py` y `consultorio/web/cancellation.py`: el
  helper `_database_path()` ya no fuerza `Path(...)`, para no convertir el
  objeto de destino PG en una ruta de Windows.
- `tests/conftest.py`: con `SPIKE_DB_BACKEND=postgres` crea un **esquema
  aislado por test** (`spike_<uuid>`), instala un proxy para que
  `sqlite3.connect(str(database_path))` de algunos tests apunte a PG y limpia
  el esquema al final. Sin la variable, el comportamiento SQLite es el
  original.
- **Nuevo** `tests/test_spike_postgres_critical.py`: 5 pruebas críticas del
  spike (se saltan fuera del modo PostgreSQL).

No se modificó ningún módulo de negocio (`appointment_service`,
`automation_service`, `cancellation_flow_service`, `email_service`,
repositorios): las garantías se ejercitaron con el código real.

### 4.1 Limitaciones conocidas del adaptador (no bloqueantes)

Hallazgos de la revisión del spike. No invalidan la viabilidad demostrada, pero
la spec de migración real debe resolverlos.

- **F-01 — `except Exception: pass` en `_rollback_raw()`**
  (`pg_adapter.py`, ~líneas 304-309): el rollback de limpieza silencia cualquier
  excepción. No se demostró que enmascare fallos de negocio (los flujos críticos
  se validaron con rollback real), pero debe eliminarse o registrar/repropagar
  el error en una migración real.
- **F-02 — Emulación de `sqlite_master`**: se sintetiza un `CREATE TABLE`
  textual, por lo que algunos asserts de esquema
  (`test_hu_006:128`, `test_hu_007:44-45`, `test_appointment_persistence:67`)
  pueden pasar con independencia del esquema real de PostgreSQL. Las garantías
  críticas no dependen de ello (se verifican con `pg_indexes` y pruebas de
  comportamiento), pero la futura suite PG debe consultar
  `information_schema`/`pg_indexes` y no la emulación.
- **F-03 — Errores de conexión no traducidos**: los errores de
  `psycopg.connect()` no se traducen a `sqlite3.OperationalError`; una caída de
  conexión no quedaría cubierta por el `except` actual del servicio. La spec de
  migración debe definir este comportamiento (traducir, reintentar o propagar).
- **F-04 — Traducción de SQL no general**: `_translate()` sustituye todos los
  `?` y `executescript()` divide por `;` sin analizar el SQL. Funciona con el SQL
  actual del proyecto, pero no es un traductor general (fallaría con `?` dentro
  de literales/comentarios o con `;` en cuerpos de funciones).

## 5. Resultados de pruebas funcionales contra PostgreSQL

Ejecutado con `SPIKE_DB_BACKEND=postgres` y el DSN local. Resultado **por
archivo**:

| Archivo | Resultado | PASS / total | Observaciones |
|---|---|---|---|
| `tests/test_appointment_persistence.py` | PASS | 4 / 4 | Incluye índice único parcial y conteos |
| `tests/test_double_booking_service.py` | PASS | 5 / 5 | Incluye concurrencia de 8 hilos |
| `tests/test_cancellation_service.py` | PASS | 44 / 44 | Incluye atomicidad, reproceso y D-010-01 |
| `tests/test_hu_010.py` | PASS | 5 / 5 | Usan PostgreSQL `TC-010-013`, `TC-010-015` y `TC-010-017`; `TC-010-014` (migración del esquema legado) usa SQLite por diseño y `TC-010-016` no usa BD |
| `tests/test_appointment_service.py` | PASS | 7 / 7 | Validación y disponibilidad |
| `tests/test_availability_service.py` | PASS | 7 / 7 | Días/horas disponibles |
| **Total solicitado (archivos existentes)** | **PASS** | **72 / 72** | 0 fallos |
| `tests/test_hu_018.py` | **NO EJECUTADO** | — | **El archivo no existe** en la rama del spike (HU-018 vive en `feature/hu-018`, no mergeada) |

Salida real por archivo:

```text
tests/test_appointment_persistence.py => 4 passed in 3.60s
tests/test_double_booking_service.py => 5 passed in 2.73s
tests/test_cancellation_service.py   => 44 passed in 33.13s
tests/test_hu_010.py                 => 5 passed in 2.42s
tests/test_appointment_service.py    => 7 passed in 1.27s
tests/test_availability_service.py   => 7 passed in 96.00s
```

Además, como señal de regresión amplia:

| Suite | Backend | Resultado |
|---|---|---|
| Suite completa | SQLite (baseline intacto) | **302 passed, 5 skipped** en 37.13 s |
| Suite completa | PostgreSQL | **307 passed, 0 failed** en 232.59 s |

Los 5 `skipped` en SQLite son las pruebas críticas del spike, que solo corren
en modo PostgreSQL por diseño.

> **F-07 (alcance de la «suite completa PostgreSQL»):** «307 passed con backend
> PostgreSQL» significa que la suite corre con ese backend configurado, pero
> algunos tests siguen abriendo SQLite directamente por diseño (p. ej.
> `test_hu_006::test_tc_006_015`, que diagnostica duplicados sin índice sobre un
> fichero SQLite temporal). Por tanto, no todos los tests ejecutados ejercitan
> realmente PostgreSQL.

> No hubo fallos que clasificar como “SQLite-especificidad” en los archivos
> solicitados: la capa de traducción cubrió `sqlite_master`, `PRAGMA`,
> `sqlite3.connect` directo y `lastrowid`. En la primera pasada de la suite
> completa sí aparecieron 2 fallos de introspección (`test_hu_006` y
> `test_hu_007`, consultas a `sqlite_master` sin `type =`); se resolvieron
> ampliando la emulación de catálogo y la suite completa quedó en 307/307.

### 5.1 Coste observado

`test_availability_service.py` tardó **96 s** frente a un tiempo mucho menor en
SQLite, porque cada llamada al repositorio abre una **conexión nueva** a
PostgreSQL (no hay pool). Es una señal de rendimiento, no un fallo funcional;
ver riesgos.

## 6. Pruebas críticas explícitas

Archivo `tests/test_spike_postgres_critical.py` — **5/5 PASS** (2.48 s):

| # | Prueba | Resultado | Evidencia |
|---|---|---|---|
| 1 | Reservar → cancelar → re-reservar el mismo slot funciona; dos citas activas en el mismo slot fallan | **PASS** | `test_pg_partial_index_rebook_after_cancel_and_block_two_active` |
| 2 | `INSERT` directo duplicado en slot activo lanza `IntegrityError` | **PASS** | `test_pg_partial_index_direct_insert_raises_integrity_error` |
| 3 | Concurrencia: 2 hilos al mismo slot; exactamente uno gana y el otro recibe `SLOT_TAKEN`, sin excepción no capturada | **PASS** | `test_pg_concurrency_two_threads_exactly_one_wins` (además pasó el test de 8 hilos `TC-006-003`) |
| 4 | Atomicidad Spec 010: cancelación + evento `pending` en la misma transacción; fallo al registrar el evento ⇒ rollback y la cita sigue `confirmed` | **PASS** | `test_pg_atomicity_rollback_when_pending_event_insert_fails` |
| 5 | Dedup `UNIQUE(event_id)` en `automation_events`: segundo `insert_event` devuelve `False` y queda 1 fila | **PASS** | `test_pg_automation_events_unique_event_id_dedup` |

Detalle de la prueba 4: se preinserta una fila con el mismo `event_id` que usará
la cancelación; al ejecutar `update_appointment_status_with_pending_event` el
`UPDATE` se aplica y el `INSERT` del evento viola `UNIQUE(event_id)`. La
conexión hace rollback de **ambas** operaciones, la excepción se propaga y la
cita permanece `confirmed`. Es exactamente la garantía «sin traza local, sin
cancelación confirmada» (Spec 010 RF-11/RF-12).

## 7. Estimación de esfuerzo de una migración real

Dos opciones, ambas sin migración de datos (confirmado: no hay datos reales):

### Opción A — migración nativa (recomendada para producción)

| Archivo | Líneas actuales | Cambio estimado |
|---|---:|---:|
| `consultorio/persistence/database.py` | 140 | ~90–110 (sustituir esquema/migración SQLite por DSN + DDL PG) |
| `consultorio/persistence/appointments_repository.py` | 190 | ~15–25 (`%s`, `RETURNING id`, tipos de fila) |
| `consultorio/persistence/automation_events_repository.py` | 148 | ~10–20 (`%s`, `now()`, excepción PG) |
| `consultorio/services/appointment_service.py` | 275 | ~3–5 (tipos de excepción) |
| `consultorio/config.py` | 49 | ~8–12 (`DATABASE_PATH` → `DATABASE_URL`) |
| `consultorio/web/appointments.py` + `cancellation.py` | 213 + 236 | ~4 (quitar coerción `Path`) |
| `consultorio/__init__.py` | 33 | ~2 |
| `requirements.txt` | 2 | +1 (`psycopg[binary]`) |
| `render.yaml` | 17 | ~6–10 (`DATABASE_URL`, base gestionada) |
| **Producción (neto)** | | **~140–200 líneas modificadas en 9 archivos** |

Tests a parametrizar/reescribir:

- `tests/conftest.py`: fixtura de backend (~40–60 líneas).
- `tests/test_appointment_persistence.py`: `PRAGMA`/`sqlite_master` → catálogo PG (~50–70 líneas).
- `tests/test_hu_010.py`: la prueba de migración del esquema legado SQLite no
  aplica a PG (~60 líneas a mover a una suite SQLite-only o eliminar).
- `test_double_booking_service.py`, `test_cancellation_service.py`,
  `test_automation_service.py`, `test_hu_006.py`, `test_hu_007.py`: helpers que
  usan `sqlite3.connect` directo (~20–40 líneas).
- **Total tests estimado: ~180–250 líneas en 6–8 archivos.**

### Opción B — capa adaptadora (la de este spike)

- `pg_adapter.py` nuevo: **511 líneas**.
- 4 archivos modificados: **63 inserciones / 8 eliminaciones** (según
  `git diff --stat`; incluye comentarios SPIKE).
- Ventaja: 0 duplicación de lógica de negocio y 72/72 + 307/307 tests sin tocar
  servicios.
- Inconveniente: es un emulador de SQLite, no una migración idiomática; no
  incluye pool, introspección completa ni gestión de migraciones. **No
  recomendado como solución final**, sí como evidencia de portabilidad.

### Riesgos de la migración real

1. **Python en Render**: local es 3.14.8; `render.yaml` fija **3.12.7**. El
   wheel `cp314` de psycopg 3.3.8 existe y se usó localmente; para 3.12 hay
   wheels de `psycopg[binary]`, pero **no se verificó en Render**.
2. **Pool de conexiones**: el código abre una conexión por operación. En
   PostgreSQL gestionado (Render/Neon) eso agota conexiones y añade latencia;
   hará falta `psycopg_pool` o reutilización por request.
3. **`datetime`/zona horaria**: `now()` es UTC en el contenedor, mientras que
   `datetime('now','localtime')` era hora local. Los tests no fijan el valor
   exacto, pero una migración real debe decidir UTC + `TIMESTAMPTZ` o mantener
   hora local explícita.
4. **Semántica transaccional**: SQLite y PostgreSQL difieren en aislamiento,
   bloqueos y `rowcount`. La prueba de concurrencia y el índice parcial cubren
   el caso crítico, pero el resto de flujos deben revisarse.
5. **Migración del esquema legado**: la migración SQLite (`sqlite_master`,
   respaldo de fichero, `ALTER TABLE … RENAME`) no tiene equivalente directo;
   como no hay datos reales, se puede crear el esquema nuevo desde cero, pero
   debe decidirse formalmente.
6. **Render Postgres / Neon**: no se verificaron en este spike límites de
   tiers gratuitos, caducidad, TLS, latencia ni región.
7. **`test_hu_018.py`**: no existe en la base del spike; la cobertura de HU-018
   no quedó evaluada.
8. **Dependencia nueva**: `psycopg` no está en `requirements.txt` (prohibido
   modificarlo en este spike) y deberá añadirse en la migración real.
9. **Errores de conexión no traducidos (F-03)**: `psycopg.connect()` puede fallar
   sin que el error se traduzca a `sqlite3.OperationalError`, por lo que una
   caída de conexión no quedaría cubierta por el `except` actual del servicio;
   la migración debe definir la traducción/gestión de esos errores.
10. **Versionado de esquema/migraciones**: SQLite crea y migra el esquema a mano
    en `database.py`; en PostgreSQL gestionado hará falta una herramienta de
    migraciones (p. ej. Alembic u otra) para versionar el esquema y aplicar
    cambios de forma reproducible.

## 8. Dificultades encontradas

- **Tests que abren SQLite directamente**: `sqlite3.connect(str(database_path))`
  aparece en varios tests. Se resolvió con un proxy en `conftest.py` que
  redirige solo los tokens `spike-pg://…`.
- **Introspección de esquema**: `sqlite_master` y `PRAGMA` no existen en PG. Se
  emularon con `pg_indexes`, `pg_index` e `information_schema.columns`.
- **`lastrowid`**: psycopg no lo expone; se reescribió el `INSERT` a
  `RETURNING id`.
- **Tipos de excepción**: los servicios capturan `sqlite3.*`; fue necesario
  traducir las excepciones de psycopg en la frontera.
- **Aislamiento de tests**: se usó un esquema por test (`spike_<uuid>`) para
  reproducir el aislamiento del fichero SQLite temporal.
- **Incidente de entorno**: al ejecutar un script de verificación desde
  `%TEMP%\opencode`, un `inspect.py` ajeno en ese directorio ensombreció el
  módulo estándar (`FileNotFoundError` con un JSON de HU-007). Se resolvió
  moviendo el script a un subdirectorio limpio; no afectó al código ni a los
  resultados.

## 9. NO VERIFICADO

- **`tests/test_hu_018.py`**: no existe en `spike/postgres-evaluacion`
  (base `main` = `9846613`); HU-018 está en `feature/hu-018`. No se ejecutó.
- **Render Postgres**: no se aprovisionó ni probó ninguna instancia real.
- **Neon**: no se aprovisionó ni probó ninguna instancia real (cold starts,
  connection limits, serverless, TLS).
- **Python 3.12.7 en Render**: no se ejecutó el proyecto en esa versión.
- **Carga real / rendimiento**: solo se midió el tiempo de la suite; no hay
  prueba de carga ni de latencia de red.
- **Pool de conexiones**: no implementado ni medido.
- **Migración de datos**: no aplica (confirmado que no hay datos de pacientes).
- **TLS/credenciales gestionadas**: no probado.
- **Comportamiento de `datetime` en el entorno de Render**: no probado.
- **Validación visual/navegador**: no aplica a este spike de backend.

## 10. Archivos creados / modificados en el worktree del spike

Creados:

- `consultorio/persistence/pg_adapter.py` (capa PostgreSQL desechable).
- `tests/test_spike_postgres_critical.py` (5 pruebas críticas del spike).
- `docs/spikes/postgresql-evaluacion-2026-11.md` (este informe).

Modificados (solo en el worktree del spike, sin commit):

- `consultorio/persistence/database.py` (dispatch SQLite/PostgreSQL).
- `consultorio/web/appointments.py` (`_database_path()` sin `Path(...)`).
- `consultorio/web/cancellation.py` (`_database_path()` sin `Path(...)`).
- `tests/conftest.py` (fixtura de backend PG + proxy de tests).

Confirmación expresa:

- No se tocó el worktree principal
  `C:\Users\Jaz\Documents\Proyectos Python\Consultorio_Carolina`.
- No se modificó nada bajo `specs/`.
- No se modificó `requirements.txt` ni `render.yaml`.
- No se hizo commit ni push: `git log --oneline -1` sigue en `9846613` y los
  cambios están sin commitear (`git status --porcelain`).

## 11. Comparativa de infraestructura (documental — NO verificada en vivo)

> Añadida por el coordinador el 2026-11-07 con fuentes oficiales consultadas
> ese mismo día. No sustituye a una prueba de aprovisionamiento real.

### Render Postgres

| Aspecto | Free | Pago (0.1c-256mb) |
|---|---|---|
| Coste | $0 | **$6/mes** + almacenamiento $0.30/GB |
| Vigencia | **Caduca a los 30 días**; 14 días de gracia antes de borrar los datos | Permanente mientras se pague |
| Almacenamiento | 1 GB | 1 GB o múltiplos de 5 GB |
| Conexiones | 100 | 100 |
| Backups / PITR | **No soporta backups** | Export lógico + PITR (ventana de 3 días en Hobby) |
| Pooling gestionado | **No** | Sí |
| Red | URL interna en la misma región; conexión pública solo desde fuera | Privada si el servicio web está en la misma región |
| Versiones | 13–18 | 13–18 |

- Un solo Postgres Free por workspace; Render puede reiniciarlo o hacer
  mantenimiento en cualquier momento.
- El servicio web Free se duerme a los 15 min sin tráfico y tarda ~1 min en
  despertar; 750 horas-instancia gratis al mes.
- Un disco persistente cuesta $0.25/GB/mes, pero **no se puede montar en un
  servicio web Free**: seguir con SQLite exige servicio web de pago ($7/mes).
- Fuentes: `render.com/docs/free`, `render.com/pricing`,
  `render.com/docs/postgresql-creating-connecting`,
  `render.com/changelog/free-postgresql-instances-now-expire-after-30-days-previously-90`
  (consultadas 2026-11-07).

### Neon Free

| Aspecto | Free |
|---|---|
| Coste | **$0**, sin tarjeta, plan permanente (no es trial) |
| Almacenamiento | 1 GB por proyecto; 20 GB por cuenta |
| Compute | 100 CU-hours por proyecto/mes; autoscaling hasta 2 CU (~8 GB) |
| Scale to zero | **Sí, tras 5 min de inactividad** (no se puede desactivar) |
| Transferencia pública | 5 GB por proyecto/mes |
| Restauración | *Instant restore* de 6 horas (hasta 1 GB de cambios); 1 snapshot manual |
| Historial de métricas | 1 día |
| Compliance | SOC 2 / ISO / GDPR / HIPAA **solo en el plan Scale**, no en Free |

- Cold start típico de unos cientos de milisegundos al despertar el compute.
  **NO VERIFICADO:** este dato **no está respaldado por las fuentes citadas** y
  sigue pendiente de comprobación real.
- Fuentes: `neon.com/docs/introduction/plans`,
  `neon.com/faqs/free-plan-limits-and-quotas`,
  `neon.com/blog/neon-free-plan-1-gb-per-project` (2026-10-02), consultadas
  2026-11-07.

### Coste comparado (1 GB de datos, app de bajo tráfico)

| Opción | Coste aproximado/mes | Persistencia | Backups | Cambio de código |
|---|---|---:|---|---|
| Render Postgres Free | $0 | **No** (caduca a 30 días) | No | Sí (migración) |
| Render Postgres pago (0.1c-256mb) | ~$6.30 | Sí | PITR 3 días | Sí (migración) |
| Neon Free | $0 | Sí | Restore 6 h | Sí (migración) |
| SQLite + disco en Render | ~$7.25 (web de pago + disco) | Sí | Manual | **Ninguno** |

## 12. Recomendación del coordinador (PROPUESTA — pendiente de aprobación)

1. **Viabilidad técnica: CONFIRMADA.** El código funciona sobre PostgreSQL 16
   con cambios localizados en la capa de persistencia; el índice único parcial,
   la concurrencia, la atomicidad de la Spec 010 y el dedup se comportan igual.
   No hay datos reales que migrar, así que el esquema se crea desde cero.
2. **Esfuerzo real de migración:** ~140–200 líneas netas en 9 archivos de
   producción y ~180–250 líneas de tests en 6–8 archivos. El adaptador del spike
   (511 líneas) **no** debe usarse como solución final: es un emulador.
3. **Riesgos que la spec de migración debe resolver:** pool de conexiones,
   `DATABASE_URL` frente a `DATABASE_PATH`, política UTC vs hora local,
   traducción de excepciones y parametrización de los tests.
4. **Elección de destino (decisión de la usuaria, no tomada):**
   - Si el objetivo es solo que los datos sobrevivan a los despliegues con
     **mínimo riesgo**: seguir en SQLite + disco persistente (~$7.25/mes), sin
     migración y sin dependencias nuevas.
   - Si se quiere PostgreSQL gestionado con backups y red privada en la misma
     plataforma: **Render Postgres pago 0.1c-256mb (~$6.30/mes)**. El Free de
     Render queda **descartado** por caducidad a 30 días.
   - Si el objetivo es **coste $0**: **Neon Free** es permanente, pero exige
     aceptar cold starts y alojar PII en un tier gratuito sin certificaciones de
     compliance. Esa decisión es de la usuaria.
5. **Secuencia propuesta:** si se aprueba migrar, hacerlo **antes** de la spec
   de acceso/agenda, en una **spec de migración propia** (sin mezclarla con
   acceso), que incluya la dependencia `psycopg` (y pooling) y la política de
   fechas/horas.

**Pendiente de decisión de la usuaria:** destino (Render pago / Neon Free /
seguir en SQLite + disco), presupuesto y aceptación del tratamiento de PII en un
PostgreSQL gestionado externo. Hasta entonces **no se inicia ninguna migración**.
