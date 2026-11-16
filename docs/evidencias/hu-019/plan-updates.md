# HU-019 · T16 — Actualización documental de los planes 004/005/006/007/010

**Estado:** revisada y aprobada por `@revisor` (veredicto `APROBADO`, 2026-11-16); commit `861e3f4` publicado en `main`.
**Alcance:** solo `plan.md` de las specs 004, 005, 006, 007 y 010.
**Referencia:** Spec 019 (`RF-1`, `RF-18`), decisión D15/D16 y tarea T16.
**TC asociado:** TC-019-022 (revisión documental).
**Fecha:** 2026-11-16.

## 1. Método

1. Inventario de menciones a `SQLite`, `sqlite3`, `DATABASE_PATH`,
   `sqlite_master`, `PRAGMA` y `busy_timeout` en los cinco planes, ampliado con
   `init_db`, `get_connection`, `data/consultorio.db`, `database_path`,
   `TC-010-014` y el DDL legado (`AUTOINCREMENT`, `datetime('now','localtime')`,
   `UNIQUE` inline).
2. Lectura del contexto de cada mención y clasificación en:
   - operativa/obsoleta → sustituida por la capa vigente;
   - decisión histórica o justificación aprobada → conservada y marcada;
   - referencia en nota de actualización → conservada.
3. Edición sin tocar requisitos, criterios de aceptación, literales ni números
   de decisión.
4. Verificación con `git diff --check` y búsqueda final de ambos patrones.

No se modificó código, tests, `spec.md`, `AGENTS.md`, `docs/constitution.md` ni
`MEMORY.md`. No se ejecutó la suite: T16 no cambia comportamiento.

## 2. Resumen

| Plan | P1 inventariadas al inicio | P1 tras T16 | P2 tras T16 | Estado |
|---|---:|---:|---:|---|
| `specs/004_agendar-cita/plan.md` | 7 | 6 | 2 | Históricas o en la nota de actualización |
| `specs/005_validar-dis-horarios/plan.md` | 2 | 1 | 0 | Solo en la nota de actualización |
| `specs/006_evitar-doble-reserva/plan.md` | 10 | 3 | 0 | Nota histórica de §2.1 y D1/D3 históricas |
| `specs/007_automatizacion-reservas/plan.md` | 16 | 3 | 1 | Nota de actualización, DDL histórico y D11 |
| `specs/010_notificar-cancelacion/plan.md` | 43 | 17 | 6 | Nota histórica, bloque `HISTÓRICO`, D5, T15 y F2-D12 |

P1 = `DATABASE_PATH|sqlite3|sqlite_master|PRAGMA|busy_timeout|SQLite|sqlite`.
P2 = `init_db|get_connection|data[\\/]consultorio\.db|TC-010-014|database_path|_database_path`.
Las líneas pueden solaparse entre patrones (p. ej. la nota de 004 o TC-010-014).

## 3. Cambios por archivo

### 3.1 `specs/004_agendar-cita/plan.md`

| Ubicación | Texto anterior | Texto nuevo | Requisito |
|---|---|---|---|
| §0, párrafo «Primera persistencia» | «se crea … con SQLite de la librería estándar … `sqlite3` es stdlib» | Igual contenido marcado como «referencia histórica» + nota de actualización a `Database`/PostgreSQL | RF-1, RF-18 |
| §1, árbol de módulos | `# + DATABASE_PATH (data/consultorio.db)` | `# + DATABASE_URL / PERSISTENCE_BACKEND` | RF-1 |
| §1, árbol de módulos | `get_connection(), init_db(app): esquema +` | `Database/ensure_schema(): esquema +` | RF-1, RF-18 |
| §1, árbol `database.py` (índice) | «índice UNIQUE (service, date, time)» | «índice único parcial de slots abiertos» | RF-1, RF-4 |
| §1, tabla de responsabilidades | «Conexión, `init_db()`, esquema e índice UNIQUE» | «Conexión, `Database`/`ensure_schema()`, esquema e índice de unicidad» | RF-1, RF-18 |
| §1, `create_app()` | «y ejecuta `init_db(app)`» | «y aplica el esquema con `Database`/`ensure_schema()`» | RF-1, RF-18 |
| §2.1, configuración | «`data/consultorio.db` fuera de git…; tests con BD temporal» | «`DATABASE_URL`/`PERSISTENCE_BACKEND`…; tests con base de datos de prueba aislada» | RF-1 |
| §2.1, bloque DDL | DDL SQLite presentado como esquema vigente (`AUTOINCREMENT`, `datetime('now','localtime')`, `UNIQUE` inline) | Nota `> **Nota histórica (Spec 019, T16)**` antes del bloque: esquema original de HU-004; vigente PostgreSQL vía `Database`/`ensure_schema()` e índice parcial `ux_appointments_slot_open` | RF-1, RF-18 |
| §4.1, comando `python app.py` | «crea `data/consultorio.db` si no existe» | «aplica el esquema vigente con `Database.ensure_schema()` si aún no existe» | RF-1, RF-18 |
| §5, D2 | «SQLite con `sqlite3` … sin ORM» | Se conserva la decisión con «(histórico; motor vigente PostgreSQL, Spec 019 RF-1/RF-18)» | RF-1, RF-18 |
| §6, fixtures | «`DATABASE_PATH` en directorio temporal, borrada al cierre» | «`DATABASE_URL` de prueba, base limpiada al cierre» | RF-1 |
| §6.1, TC-004-004 | «`init_db()` crea `appointments`… y el índice `UNIQUE`» | «El catálogo del motor registra… la unicidad de slots abiertos (`ux_appointments_slot_open`)» | RF-4 |
| §7.1, Q4 | «Sí: SQLite + `consultorio/persistence/`» | Se conserva y se añade «(Histórico: motor vigente PostgreSQL con la misma capa)» | RF-1, RF-18 |
| §8, paso 3 | «`Config.DATABASE_PATH`» | «`Config.DATABASE_URL` (y `PERSISTENCE_BACKEND`)» | RF-1 |
| §8, paso 7 | «`init_db()`» | «`Database`/`ensure_schema()`» | RF-1, RF-18 |
| §10, saneamiento | «se elimina `data/consultorio.db` y se regenera con `init_db()`» | Marcado «*histórico:*», con la aplicación vigente vía `Database.ensure_schema()` | RF-1, RF-18 |

### 3.2 `specs/005_validar-dis-horarios/plan.md`

| Ubicación | Texto anterior | Texto nuevo | Requisito |
|---|---|---|---|
| §0, fuera de alcance | «cambios de esquema SQLite» | «cambios de esquema de persistencia» | RF-1, RF-18 |
| §1.3 | «y el esquema SQLite no cambian» | «y el esquema de persistencia no cambian» | RF-1, RF-18 |
| §0, tras «Sin cambios de modelo de datos» | — | Nota de actualización Spec 019/T16 (PostgreSQL, sin cambios de modelo) | RF-1, RF-18 |

### 3.3 `specs/006_evitar-doble-reserva/plan.md`

| Ubicación | Texto anterior | Texto nuevo | Requisito |
|---|---|---|---|
| §0, fuera de alcance | «cambios de esquema SQLite» | «cambios de esquema de persistencia» | RF-1, RF-18 |
| §0, «Sin cambios de modelo de datos» | «tabla e índice `UNIQUE` intactos» | «en el diseño original… quedaban intactos; el esquema vigente aplica el índice parcial `ux_appointments_slot_open`» | RF-1, RF-18 |
| §0, nota nueva | — | Actualización Spec 019/T16; D1–D3 conservan justificación histórica | RF-1, RF-18 |
| §1, trazabilidad RF-3 | «§3 `IntegrityError`/bloqueo → `SLOT_TAKEN`» | «§3 `IntegrityError`/`UniqueViolation` → `SLOT_TAKEN`» | RF-3 |
| §1, árbol | «`sqlite3.IntegrityError` y bloqueo» | «`IntegrityError`/`UniqueViolation`» | RF-1 |
| §2.1, modelo de datos | «tabla e índice `UNIQUE` se reutilizan tal cual; no hay migraciones» | Nota histórica: diseño de HU-006 sobre SQLite; vigente PostgreSQL vía `Database`/`ensure_schema()` e índice parcial | RF-1, RF-18 |
| §2.3, punto de persistencia | «`UNIQUE (service, date, time)` → `sqlite3.IntegrityError`» | «índice parcial `ux_appointments_slot_open` … → `IntegrityError`/`UniqueViolation`» | RF-1, RF-18 |
| §2.3, concurrencia | «`busy_timeout` de la stdlib serializa las escrituras» | «PostgreSQL resuelve la carrera en el punto de persistencia … sin esperas de bloqueo» | RF-1, RF-18 |
| §3, pseudocódigo | `CATCH sqlite3.IntegrityError` y `OperationalError (locked/busy)` | `CATCH IntegrityError / UniqueViolation`; se elimina la rama de bloqueo | RF-1, RF-18 |
| §5, D1 | «SQLite nativo» | Se conserva con «(histórico; adaptado a PostgreSQL por Spec 019)» | RF-1, RF-18 |
| §5, D2 | «índice `UNIQUE` … sin migraciones» | Se conserva con nota de evolución a índice parcial (Spec 010/019) | RF-1, RF-18 |
| §5, D3 | «capturar `sqlite3.IntegrityError` … `OperationalError` de bloqueo» | Se conserva con nota del mapeo vigente `IntegrityError`/`UniqueViolation` | RF-1, RF-18 |
| §5, D8 | «Limpieza automática en `init_db`» | «Limpieza automática en el arranque» | RF-1 |
| §6, fixtures | «`database_path` con BD temporal» | «base de datos de prueba aislada» | RF-1 |
| §6.1, TC-006-005 | `OperationalError("database is locked")` → `SLOT_TAKEN` | `IntegrityError`/`UniqueViolation` → `SLOT_TAKEN`; `OperationalError`/`InterfaceError` → `PersistenceUnavailable` | RF-1, RF-3 |
| §6.1, TC-006-013 | «consultado sobre `sqlite_master`»; `UNIQUE` inline | «índice parcial `ux_appointments_slot_open`… verificado sobre el catálogo del motor» | RF-1, RF-6 |

### 3.4 `specs/007_automatizacion-reservas/plan.md`

| Ubicación | Texto anterior | Texto nuevo | Requisito |
|---|---|---|---|
| §0, base existente | «Capa de persistencia stdlib (… SQLite …), inyección de `database_path`» | «Capa de persistencia (… sin ORM), abstracción `Database` e inyección de conexión/transacción» | RF-1, RF-18 |
| §0, nota nueva | — | Actualización Spec 019/T16; menciones a SQLite/`database_path` son históricas | RF-1, RF-18 |
| §1 | «mismo patrón DI que `database_path`» | «mismo patrón DI que la capa de persistencia» | RF-1 |
| §1, «Sin cambios» | «`init_db()` sigue siendo `CREATE TABLE IF NOT EXISTS`» | «`Database.ensure_schema()` sigue aplicando `CREATE TABLE IF NOT EXISTS`» | RF-1, RF-18 |
| §2.1, `appointments` | «`appointments` y su `UNIQUE` quedan intactos» | «en el diseño original… quedaban intactos; el esquema vigente aplica el índice parcial `ux_appointments_slot_open`» | RF-1, RF-18 |
| §2.1, bloque DDL | DDL SQLite presentado como vigente (`AUTOINCREMENT`, `datetime('now','localtime')`) | Nota histórica antes del bloque: esquema original de `automation_events`; vigente PostgreSQL vía `Database`/`ensure_schema()`; contrato de columnas y `UNIQUE(event_id)` conservado | RF-1, RF-18 |
| §2.1 | «Sin FK forzada (SQLite la ignora sin PRAGMA)» | «Sin FK declarada: `appointment_id` documenta el vínculo…» | RF-1, RF-18 |
| §3, pseudocódigo | `CATCH sqlite3.IntegrityError` | `CATCH IntegrityError / UniqueViolation` (dos apariciones) | RF-1 |
| §3, pseudocódigo web | `create_booking(data, _database_path(), …)` | `create_booking(data, get_database(), …)` | RF-1 |
| §5, D9 (segunda ocurrencia de DI) | «patrón DI de `database_path`» | «patrón DI de la capa de persistencia» | RF-1 |
| §5, D11 | «`urllib.request`, `json`, `sqlite3` de la stdlib» | Se conserva con «(histórico; Spec 019 incorporó el driver PostgreSQL)» | RF-1, RF-18 |
| §6, fixtures | «`database_path` con BD temporal» | «base de datos de prueba aislada» | RF-1 |
| §6.1, TC-007-010 | «`sqlite_master` con `automation_events`…» | «el catálogo del motor registra `automation_events`…» | RF-1 |
| §9.3.3 | «el esquema SQLite … no cambian» | «el esquema de persistencia … no cambian» | RF-1, RF-18 |
| §9.4.4 | «No hay migración de esquema en SQLite» | «No hay migración de esquema en la base de datos» | RF-1, RF-18 |
| §9.5.7, D-E1 | «Persistir `calendar_event_id` en SQLite» | «Persistir `calendar_event_id` en la base de datos» | RF-1 |
| §9.8, R12 | «no cambiar `DATABASE_PATH` ni Render» | «no cambiar `DATABASE_URL` de producción ni Render» | RF-1 |

### 3.5 `specs/010_notificar-cancelacion/plan.md`

| Ubicación | Texto anterior | Texto nuevo | Requisito |
|---|---|---|---|
| §1, árbol `database.py` | «SCHEMA… + migración idempotente con respaldo» | «`Database/ensure_schema()`: DDL vigente + índice parcial; migración SQLite marcada histórica» | RF-1, RF-18 |
| §1, árbol de tests | `test_hu_010.py` incluye «migración» | Se separa `tests/test_rollback_sqlite.py` (T15) y se deja `test_hu_010.py` para disponibilidad/HTTP/regresión | RF-1, RF-18 |
| §1, responsabilidades | «DDL nuevo + migración idempotente con respaldo» | «DDL vigente (`Database`/`ensure_schema`) + índice parcial; migración SQLite histórica» | RF-1, RF-18 |
| §2.1.2 | «SQLite no permite eliminar un `UNIQUE` inline…» | Bloque marcado con «Nota histórica (Spec 019, T16)»; el esquema PostgreSQL se aplica con `Database`/`ensure_schema` | RF-1, RF-18 |
| §2.1.2 | «→ `sqlite3.IntegrityError` → `SLOT_TAKEN`» | «→ `IntegrityError`/`UniqueViolation` → `SLOT_TAKEN`» | RF-1 |
| §3, pseudocódigo | `init_db(database_path)` sin marca | `ensure_schema(database)` + bloque `HISTÓRICO` para la ruta SQLite de referencia | RF-1, RF-18 |
| §3, comentarios de errores | `# sqlite3.IntegrityError/OperationalError propagan` | `# IntegrityError/UniqueViolation propagan` (dos apariciones) | RF-1, RF-18 |
| §3 | `cancel_appointment(..., database_path, ...)` y llamadas | `cancel_appointment(..., database, ...)` y llamadas con `database` | RF-1 |
| §6, fixtures | «BD temporal por fixture; el `init_db()` de la fixture…» | «base de datos aislada por fixture; esquema vía `Database`/`ensure_schema()`; rollback SQLite en T15» | RF-1, RF-18 |
| §6.1, TC-010-014 | `test_hu_010.py`; migración SQLite | `tests/test_rollback_sqlite.py`; histórico T15; evidencia `docs/evidencias/hu-019/rollback.md` | RNF-2, RF-4 |
| §6.2, pirámide | «BD con esquema antiguo → `init_db()` migra» | «Persistencia vigente…; migración SQLite histórica en `tests/test_rollback_sqlite.py`» | RF-4, RNF-2 |
| §6.3, ejecución | «BD temporal…; la migración se prueba con una BD vieja» | «base de datos de prueba aislada…; el rollback SQLite se prueba en `tests/test_rollback_sqlite.py` (T15)» | RF-1, RF-18 |
| §8, paso 5 | «SCHEMA nuevo + `init_db()` con migración y respaldo» | «DDL vigente (`Database`/`ensure_schema`) + índice parcial; TC-010-014 histórico» | RF-1, RF-18 |
| §9.1 | «una única transacción … sobre la misma conexión SQLite» | «una única transacción de persistencia del motor de base de datos» | RF-1, RF-18 |
| §9.3, tabla de módulos | `claim_failed_event(..., database_path, ...)`; helper con `database_path` | Parámetro `database` | RF-1 |
| §9.3, `database.py` | «SIN CAMBIOS» | «SIN CAMBIOS por esta HU» | RNF-7 (aclaración no funcional) |
| §9.4, pseudocódigo | `database_path` en servicios/repositorios; `get_connection`/`commit`/`rollback`/`close` manuales | `database` y `WITH database.transaction() AS connection` | RF-1 |
| §9.4, pseudocódigo | `CATCH (sqlite3.IntegrityError, sqlite3.OperationalError)` | `CATCH IntegrityError / UniqueViolation` | RF-1 |
| §9.7, D5 | «SQLite no admite `DROP CONSTRAINT`» | Se conserva con «(histórico de HU-010 sobre SQLite; en PostgreSQL … DDL/migraciones de la Spec 019)» | RF-1, RF-18 |
| §9.7, F2-D11 | «misma conexión y transacción SQLite» | «misma conexión y transacción del motor de base de datos» | RF-1, RF-18 |
| §9.7, F2-D12 | «SQLite serializa escrituras…» | Se restaura la justificación original y se marca «*(histórico; motor vigente PostgreSQL, Spec 019 RF-1/RF-18)*» | RF-1, RF-18 |
| §9.8, tests | «BD temporal por fixture» | «base de datos de prueba aislada por fixture; esquema vía `Database`/`ensure_schema`» | RF-1, RF-18 |

## 4. Menciones conservadas y justificación

Todas las coincidencias restantes están en contexto histórico explícito, en una
nota de actualización o en la ruta de rollback aprobada por T15:

| Archivo | Línea(s) exactas (P1) | Motivo |
|---|---|---|
| 004 | 27 | Párrafo marcado «referencia histórica» |
| 004 | 30 | Cierre del mismo párrafo histórico (`sqlite3` stdlib) |
| 004 | 35 | Nota de actualización que explica la sustitución |
| 004 | 156 | Nota histórica del DDL de §2.1 (esquema original de HU-004) |
| 004 | 398 | D2 conserva la decisión original y su justificación; lleva marca histórica |
| 004 | 503 | Q4 conserva la respuesta de la usuaria (2026-10-09); lleva marca histórica |
| 005 | 40 | Nota de actualización (menciona el término para explicar el cambio) |
| 006 | 155 | Nota histórica de §2.1 (diseño de HU-006 sobre SQLite) |
| 006 | 295 | D1 histórica; se conserva la justificación y se añade la adaptación a PostgreSQL |
| 006 | 297 | D3 histórica; se conserva la justificación y se añade el mapeo vigente |
| 007 | 37 | Nota de actualización |
| 007 | 165 | Nota histórica del DDL de `automation_events` |
| 007 | 397 | D11 histórica; se conserva la decisión y se aclara el driver aprobado por Spec 019 |
| 010 | 153 | Marca histórica en el árbol de módulos |
| 010 | 164 | Nombre del archivo de rollback aprobado por T15 |
| 010 | 183 | Tabla de responsabilidades: migración SQLite marcada histórica |
| 010 | 217 | Nota histórica de la migración Q4 sobre SQLite |
| 010 | 226 | Desarrollo de la migración histórica, dentro del bloque marcado por la nota |
| 010 | 369 | Bloque `HISTÓRICO` del pseudocódigo |
| 010 | 370 | `init_db()` conservado dentro del bloque `HISTÓRICO` |
| 010 | 504 | D5 histórica; se conserva la justificación y se indica el procedimiento vigente |
| 010 | 524 | Ruta de migración SQLite derivada a T15 |
| 010 | 525 | Referencia a `tests/test_rollback_sqlite.py` y su evidencia |
| 010 | 546 | TC-010-014 reubicado y marcado como histórico/T15 |
| 010 | 567 | Pirámide: migración SQLite histórica en T15 |
| 010 | 568 | Referencia a `tests/test_rollback_sqlite.py` (T15) |
| 010 | 588 | §6.3: rollback SQLite derivado a T15 |
| 010 | 589 | §6.3: referencia a `tests/test_rollback_sqlite.py` |
| 010 | 665 | §8, paso 5: TC-010-014 histórico/T15 |
| 010 | 1060 | F2-D12: justificación original restaurada y marcada histórica |

Coincidencias del patrón P2 conservadas:

| Archivo | Línea(s) exactas (P2) | Motivo |
|---|---|---|
| 004 | 35 | Nota de actualización que nombra `DATABASE_PATH` para explicar el cambio |
| 004 | 586 | Saneamiento histórico: `data/consultorio.db` + `init_db()` en pasado |
| 007 | 37 | Nota de actualización que nombra `database_path` |
| 010 | 239 | Copia de respaldo dentro del bloque histórico de §2.1.2 |
| 010 | 245 | `init_db()` dentro del bloque histórico de §2.1.2 |
| 010 | 370 | Pseudocódigo histórico de `init_db(database_path)` |
| 010 | 377 | Respaldo del fichero dentro del pseudocódigo histórico |
| 010 | 546 | TC-010-014 histórico (T15) |
| 010 | 665 | §8, paso 5 con TC-010-014 histórico (T15) |

No se eliminó ninguna decisión ni justificación aprobada. Las decisiones D2
(004), D1/D2/D3 (006), D11 (007) y D5 (010) mantienen su texto original y su
número; solo se les añadió la marca histórica y la referencia a la Spec 019.

## 5. Verificación ejecutada

### 5.1 Estado de Git

```text
$ git status --short
 M specs/004_agendar-cita/plan.md
 M specs/005_validar-dis-horarios/plan.md
 M specs/006_evitar-doble-reserva/plan.md
 M specs/007_automatizacion-reservas/plan.md
 M specs/010_notificar-cancelacion/plan.md
?? .agents/skills/sdd/
?? .opencode/
?? docs/evidencias/hu-019/plan-updates.md
```

`docs/evidencias/hu-019/plan-updates.md` es la evidencia nueva de T16.
`.agents/skills/sdd/` y `.opencode/` son untracked preexistentes y no forman
parte de este cambio.

### 5.2 Diff

```text
$ git diff --stat
 specs/004_agendar-cita/plan.md            |  65 ++++++++-----
 specs/005_validar-dis-horarios/plan.md    |   8 +-
 specs/006_evitar-doble-reserva/plan.md    |  58 ++++++-----
 specs/007_automatizacion-reservas/plan.md |  58 ++++++-----
 specs/010_notificar-cancelacion/plan.md   | 154 ++++++++++++++++--------------
 5 files changed, 201 insertions(+), 142 deletions(-)
```

```text
$ git diff --check
warning: in the working copy of 'specs/010_notificar-cancelacion/plan.md', LF will be replaced by CRLF the next time Git touches it
$ echo $LASTEXITCODE
0
```

`git diff --check` no emitió contenido de error: solo el aviso de normalización
LF→CRLF en `specs/010_notificar-cancelacion/plan.md` (stderr) y exit code `0`.

### 5.3 Búsqueda final

`rg` no está disponible en el entorno (`El término 'rg' no se reconoce`). Se usó
el equivalente de PowerShell:

```powershell
$files = @(
  "specs\004_agendar-cita\plan.md",
  "specs\005_validar-dis-horarios\plan.md",
  "specs\006_evitar-doble-reserva\plan.md",
  "specs\007_automatizacion-reservas\plan.md",
  "specs\010_notificar-cancelacion\plan.md"
)
Select-String -Path $files -Pattern "DATABASE_PATH|sqlite3|sqlite_master|PRAGMA|busy_timeout|SQLite|sqlite"
Select-String -Path $files -Pattern "init_db|get_connection|data[\\/]consultorio\.db|TC-010-014|database_path|_database_path"
```

Resultado real de P1: **30 líneas** —
004: 27, 30, 35, 156, 398, 503 · 005: 40 · 006: 155, 295, 297 · 007: 37, 165, 397 ·
010: 153, 164, 183, 217, 226, 369, 370, 504, 524, 525, 546, 567, 568, 588, 589, 665, 1060.

Resultado real de P2: **9 líneas** —
004: 35, 586 · 007: 37 · 010: 239, 245, 370, 377, 546, 665.

El incremento de P1 (26 → 30) corresponde a las nuevas notas históricas de
H-05/H-06/H-07 y a la marca histórica de F2-D12; no añade menciones operativas.

Todas están justificadas en §4. No queda ninguna mención operativa a SQLite,
`sqlite3`, `sqlite_master`, `PRAGMA`, `busy_timeout`, `DATABASE_PATH`,
`get_connection`, `database_path` ni `data/consultorio.db` como API vigente.

`TC-010-014` solo aparece con su ubicación vigente
(`tests/test_rollback_sqlite.py`) o en contexto histórico explícito (T15 y
`docs/evidencias/hu-019/rollback.md`).

Verificación DDL legado (`AUTOINCREMENT|datetime\('now'|UNIQUE \(service, date, time\)`):
**19 líneas**. Los únicos bloques con `AUTOINCREMENT`/`datetime('now')` son el de
004 §2.1 (163, 173) y el de 007 §2.1 (171, 178), ambos inmediatamente precedidos
por su nota histórica; 006 no contiene bloque DDL. El `UNIQUE` inline de 004
(174) queda bajo esa nota. El `UNIQUE(event_id)` de `automation_events` se
conserva como contrato de la tabla, no como DDL vigente de SQLite.

## 6. Invariantes respetados

- [x] No se modificó ningún RF, CA, caso límite ni literal contractual.
- [x] No se renumeraron ni eliminaron decisiones técnicas.
- [x] No se tocaron `spec.md`, código, tests, `AGENTS.md`, `docs/constitution.md`
      ni `MEMORY.md`.
- [x] No se añadieron requisitos nuevos; las notas solo trazan la adaptación a la
      Spec 019 (RF-1/RF-18).
- [x] No se ejecutó la suite (cambio exclusivamente documental).
- [x] No se hizo commit ni push.

## 7. Observaciones y pendientes

- El código conserva la ruta de rollback SQLite en
  `consultorio/persistence/database.py` mientras se completan las tareas de
  migración de la Spec 019. Este cambio documental no altera esa convivencia ni
  declara completada la migración del código.
- La aprobación de esta actualización documental corresponde al coordinador y a la
  usuaria. T16 no se declara aprobada por la sola ejecución de los comandos.
- **Revisión (2026-11-16):** `@revisor` emitió **APROBADO** tras dos ciclos de
  corrección (H-01..H-07). Se verificaron el cierre de los hallazgos, la ausencia
  de cambios en `spec.md`/código/tests y la coherencia con
  `tests/test_rollback_sqlite.py`. No se ejecutó `pytest` (cambio documental).
