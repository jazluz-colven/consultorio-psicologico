# Evidencia T18 — Retirada del rollback SQLite

- **Fecha:** 2026-11-16
- **Rama:** `feature/hu-019-migracion-postgres`
- **HEAD:** `73743c7`
- **Tarea:** T18 — Retirar el rollback y el almacenamiento anterior tras la
  aceptación.
- **Autorización:** aceptación funcional de la migración y autorización expresa
  de la retirada el 2026-11-16.
- **Alcance:** eliminar `PERSISTENCE_BACKEND`, `DATABASE_PATH`, el DDL y la ruta
  SQLite, la prueba de rollback y su documentación operativa. No se modifican
  requisitos, literales, reglas de negocio ni UX.

## 1. Trazabilidad

`Spec 019 RF-18 / RNF-7` → `plan.md` D10 → `tasks.md` T18 → `TC-019-024`.

- **RF-18:** la vía de rollback era temporal y debía retirarse tras la
  aceptación de la migración.
- **RNF-7:** la documentación operativa debe describir una sola persistencia y
  no conservar procedimientos ambiguos.
- **TC-019-024:** retirada del interruptor, la ruta SQLite, el DDL y las pruebas
  de rollback, manteniendo la suite en verde.

## 2. Retiradas realizadas

### Código

- `consultorio/config.py`: eliminados `PERSISTENCE_BACKEND`, `DATABASE_PATH`,
  `_parse_persistence_backend`, `_parse_database_path` y la configuración SQLite
  de `TestConfig`. `_validate_postgres_tls` ya no recibe un backend.
- `consultorio/persistence/database.py`: eliminados `SCHEMA`,
  `APPOINTMENTS_TABLE_SQL`, `_PARTIAL_INDEX_SQL`, `get_connection`, `init_db`,
  `_migrate_appointment_uniqueness` y las ramas SQLite de `DatabaseTarget`,
  `from_config`, `ensure_schema` y `_default_connect`. `DatabaseTarget` ya no
  tiene `backend` ni `sqlite_path`.
- `consultorio/persistence/appointments_repository.py` y
  `consultorio/persistence/automation_events_repository.py`: eliminados el
  adaptador `%s`→`?`, las ramas por backend y los tipos `str | Path`. El
  recurso admitido es solo `Database | DatabaseTarget`.
- `consultorio/services/automation_service.py` y
  `consultorio/services/email_service.py`: el parámetro `database_path` pasa a
  `database: DatabaseResource`.
- `consultorio/__init__.py`: retirada la llamada transitoria a
  `init_db(app.config["DATABASE_PATH"])`.
- `consultorio/web/persistence.py`: docstring actualizado a PostgreSQL.
- `render.yaml`: retirada la variable `PERSISTENCE_BACKEND`.
- `consultorio/services/cancellation_flow_service.py`: docstrings sin la ruta
  SQLite transitoria.

### Pruebas

- Eliminado `tests/test_rollback_sqlite.py`.
- `tests/conftest.py`: la app de prueba ya no define `DATABASE_PATH` ni
  `PERSISTENCE_BACKEND`; el `DatabaseTarget` de test no recibe backend.
- `tests/test_pg_resilience.py`: retiradas las pruebas SQLite y añadida
  `test_removed_sqlite_configuration_is_not_exposed`, que comprueba que las
  variables heredadas no crean atributos de configuración.
- `tests/test_hu_019.py`: retirada la prueba de la ruta SQLite y sus imports.
- `tests/test_hu_010.py`: actualizada la lista de imports permitidos a los
  módulos reales.
- `tests/test_render_manifest.py`: exige la ausencia de
  `PERSISTENCE_BACKEND` y `DATABASE_PATH`.

### Documentación

- `docs/operaciones/postgresql.md`: eliminada la sección de rollback SQLite y
  las referencias operativas al interruptor, `DATABASE_PATH` y el adaptador de
  dialecto. El documento describe solo PostgreSQL.
- Se conservan referencias históricas en `specs/`, evidencias anteriores y
  spikes, como registros de la migración.

## 3. Comprobaciones ejecutadas

### Suite completa contra PostgreSQL

Comando real, sin imprimir el DSN:

```powershell
$env:TEST_DATABASE_URL = '<DSN local>'
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
py -3.14 -m pytest -q
```

Resultado real del implementador:

```text
392 passed in 188.84s (0:03:08)
```

Corrida independiente de verificación del coordinador:

```text
392 passed in 192.92s (0:03:12)
```

En ambas ejecuciones no hubo `FAIL`, `ERROR`, `skip` ni `xfail`.

### Compilación

```powershell
py -3.14 -m compileall -q consultorio tests app.py
```

Resultado: exit code `0` (`compileall ok`).

### Búsqueda de restos

Búsqueda en código de aplicación y tests:

```powershell
Get-ChildItem -Recurse -File -Include *.py |
  Where-Object { $_.FullName -notmatch '\\(specs|docs|\.git|\.agents|\.opencode)\\' } |
  Select-String -Pattern 'PERSISTENCE_BACKEND|DATABASE_PATH|sqlite3|\binit_db\b|\bget_connection\b|database_path|sqlite_path|backend="sqlite"' -CaseSensitive:$false
```

Resultado: solo las comprobaciones intencionadas de ausencia en
`tests/test_pg_resilience.py` y `tests/test_render_manifest.py`. No hay
referencias en `consultorio/`, `app.py` ni `render.yaml`.

### Diff

```powershell
git diff --check
```

Resultado: exit code `0`. Git solo advierte de la conversión esperada de LF a
CRLF en los archivos tocados; no hay errores de whitespace.

`git diff --shortstat` en el momento de la revisión técnica, antes del cierre
documental: 19 archivos afectados, 251 inserciones y 1212 eliminaciones,
incluida la eliminación de 360 líneas de `tests/test_rollback_sqlite.py` y los
ajustes acotados de `tests/test_appointment_persistence.py`.

Tras el cierre documental (T18, `MEMORY.md` y la referencia de T14), el mismo
comando da 20 archivos, 271 inserciones y 1213 eliminaciones. Ninguna de las dos
cifras incluye `t18-removal.md`, que todavía no está versionado.

## 4. Estado de TC-019-024

**PASS.**

- Interruptor, ruta SQLite, DDL y pruebas de rollback retirados.
- La suite completa pasa contra PostgreSQL.
- `render.yaml` no contiene variables SQLite.
- La documentación operativa queda centrada en PostgreSQL.
- No se ha modificado ningún requisito, literal ni regla de negocio.

## 5. Revisión técnica

`@revisor` emitió **APROBADO** el 2026-11-17 para RF-18, RNF-7 y TC-019-024,
sin defectos bloqueantes. La revisión no pudo reproducir la suite completa
porque el entorno del revisor no tenía Docker/PostgreSQL local activo; el
resultado se sustenta en la corrida independiente del coordinador y en la
evidencia anterior.

## 6. Limitaciones y pendientes

- El DSN local no se reproduce en esta evidencia.
- No hay cambios visuales en T18; no requiere comprobación de navegador.
- El cierre documental, la marca `[x]` de T18 y la actualización de `MEMORY.md`
  los realiza el coordinador tras la aprobación técnica.
- Commit `61f358a` publicado en `origin/feature/hu-019-migracion-postgres`
  (2026-11-17); T18 marcada `[x]`.
