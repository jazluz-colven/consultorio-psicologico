# T10 — Fixtures y tests de persistencia en PostgreSQL

> Trazabilidad: Spec 019 (`specs/019_migrar-postgresql/spec.md`, RF-28, RF-29;
> RNF-5; CL-10) → `plan.md` D9 y §6.1–§6.3 → `tasks.md` T10 → este documento.
> Rama: `feature/hu-019-migracion-postgres`. HEAD al iniciar: `e38f96f`.
> Fecha de ejecución: 2026-11-10. PostgreSQL local: `postgres:16-alpine`
> (contenedor `consultorio-pg-019`, `127.0.0.1:55432`).

## 1. Alcance y resultado global

T10 migra a PostgreSQL real **solo** la infraestructura de la suite y cuatro
archivos de paridad:

- `tests/conftest.py` (validación de sesión y fixtures).
- `tests/test_appointment_persistence.py`.
- `tests/test_hu_006.py`.
- `tests/test_hu_007.py`.
- `tests/test_hu_010.py`.

Además reubica `TC-010-014` (migración del esquema SQLite legado) a
`tests/test_rollback_sqlite.py`, sin pérdida de cobertura y sin presentarlo como
evidencia de paridad.

Los archivos de T10 y `tests/test_rollback_sqlite.py` **pasan**. La suite
completa todavía tiene fallos en archivos que pertenecen a T11 (ver §7); no se
ocultan ni se silencian.

## 2. Diseño de fixtures y aislamiento

### 2.1 Validación obligatoria al inicio de la sesión

`tests/conftest.py` añade `pytest_configure()` (se ejecuta solo dentro de
pytest, nunca al importar el módulo):

1. Lee `TEST_DATABASE_URL`.
2. Si falta, detiene la sesión con `pytest.exit(..., returncode=1)` y un mensaje
   accionable.
3. Si existe, abre una conexión real con `psycopg.connect(url,
   connect_timeout=5)` y ejecuta `SELECT 1`.
4. Si la conexión falla, detiene la sesión con el mismo tipo de mensaje.

No se usa `skip`, `xfail` ni una emulación. El DSN nunca se imprime.

### 2.2 Esquema aislado por test

- `pg_schema` crea `test_hu019_<uuid>` con `CREATE SCHEMA` y lo elimina con
  `DROP SCHEMA … CASCADE` en el teardown.
- `pg_target` construye un `DatabaseTarget(backend="postgres", dsn=url,
  schema=<uuid>)`. `Database` fija `search_path=<schema>` por conexión
  (opción `-c search_path=…` de libpq), por lo que ninguna sentencia de los
  tests resuelve objetos en `public`.
- `pg_schema`/`pg_target` son la base de `app` y `database`, de modo que el
  teardown de `app` (que cierra la conexión de petición) ocurre **antes** del
  `DROP SCHEMA`.

### 2.3 Fixture `app` en PostgreSQL sin tocar `public`

`app` sigue este orden:

1. Construye `create_app(TempConfig)` con `DATABASE_PATH =
   tmp_path/consultorio.db`, `PERSISTENCE_BACKEND="sqlite"` y
   `DATABASE_URL=""`. Así el bootstrap de `create_app()` trabaja solo sobre el
   SQLite temporal y **no** abre ninguna conexión PostgreSQL a `public`.
2. Construye `Database(pg_target)` y aplica `ensure_schema()` en el esquema
   aislado (crea tablas, índice parcial y `schema_migrations`).
3. Sustituye `app.extensions[DATABASE_EXTENSION_KEY]` por esa instancia
   PostgreSQL y actualiza `app.config["PERSISTENCE_BACKEND"]="postgres"` y
   `app.config["DATABASE_URL"]=<DSN>` para coherencia.
4. En el teardown entra en un `app_context` y llama a `database.close_request()`
   (idempotente), garantizando que no quede ninguna conexión abierta antes del
   `DROP SCHEMA`.

La fixture `database` devuelve la instancia `Database` registrada por `app`, que
es la misma que usan las rutas a través de `consultorio.web.persistence`.

### 2.4 Fixture `database_path` conservada

`database_path` (SQLite temporal con `init_db`) se conserva intacta para los
archivos que T11 migrará después. T10 no los modifica.

### 2.5 Resultado sobre `public`

Tras la corrida completa:

```text
SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'test_hu019_%';  -- 0
public.appointments        0 filas
public.automation_events   0 filas
public.schema_migrations   4 filas (DDL previo, sin datos de test)
```

No queda ningún esquema de prueba y los fixtures no escriben en `public`.

## 3. Mensajes reales de fallo de sesión

### 3.1 Sin `TEST_DATABASE_URL`

```text
Exit: TEST_DATABASE_URL no está definida. La Spec 019 (plan D9,
RF-28/RF-29, CL-10) exige que la suite se ejecute SIEMPRE contra PostgreSQL.
No se usa `skip` ni `xfail`: sin base de datos la sesión se detiene al inicio.

1) Levanta el contenedor local reproducible (si ya existe, usa `docker start`):

   docker run -d --name consultorio-pg-019 -e POSTGRES_DB=consultorio_dev -e POSTGRES_USER=consultorio_dev -e POSTGRES_PASSWORD=<password-local> -p 127.0.0.1:55432:5432 -v consultorio-pgdata-019:/var/lib/postgresql/data postgres:16-alpine

   docker start consultorio-pg-019

2) Define el DSN solo en la sesión de PowerShell:

   $env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"

3) Repite:

   python -m pytest -q

Procedimiento completo: docs/operaciones/postgresql.md
```

### 3.2 Con `TEST_DATABASE_URL` pero sin base levantada

Probado con un DSN local inalcanzable (`127.0.0.1:1`, sin credenciales reales):

```text
Exit: No se pudo conectar a TEST_DATABASE_URL (ConnectionTimeout). La Spec 019
(plan D9, RF-28/RF-29, CL-10) exige que la suite se ejecute SIEMPRE contra
PostgreSQL. No se usa `skip` ni `xfail`: sin base de datos la sesión se detiene
al inicio.
```

El proceso termina antes de recolectar y ejecutar tests.

## 4. Archivos migrados

### 4.1 `tests/test_appointment_persistence.py`

- `PRAGMA table_info` → `information_schema.columns`.
- `PRAGMA index_list`/`index_info` → `pg_indexes`, `pg_index` (`indisunique`,
  `indpred IS NOT NULL`) y `pg_constraint`.
- Se verifica que el índice `ux_appointments_slot_open` es único, parcial
  (`WHERE status <> 'cancelled'`) y que **no** existe una restricción UNIQUE
  inline sobre `(service, date, time)`.
- `sqlite3.IntegrityError` → `psycopg.errors.UniqueViolation`.
- Repositorio y conteos usan la fixture `database` (PostgreSQL).

### 4.2 `tests/test_hu_006.py`

- `TC-006-013`: consulta `pg_constraint` y `pg_indexes` del esquema aislado en
  lugar de `sqlite_master`; el diagnóstico de duplicados se ejecuta sobre
  PostgreSQL.
- `TC-006-015`: crea un esquema PostgreSQL desechable con la tabla
  `appointments` **sin** el índice parcial e inserta dos filas idénticas para
  comprobar que el diagnóstico detecta el duplicado. Ya no abre SQLite.
- El resto de TC (JS, CSS y literales) queda igual.

### 4.3 `tests/test_hu_007.py`

- `TC-007-010`: `UNIQUE(event_id)` se comprueba con `pg_constraint`; el dedup se
  cuenta con `COUNT(*)` sobre `automation_events` en PostgreSQL.
- `TC-007-012`: la reserva directa y el flujo HTTP usan la misma base
  PostgreSQL de `app` (`database`), no `Path(app.config["DATABASE_PATH"])`.

### 4.4 `tests/test_hu_010.py`

- `TC-010-013`, `TC-010-015` y `TC-010-017` usan la fixture `database`; los
  conteos se hacen con `SELECT COUNT(*)` sobre PostgreSQL.
- Se conservan `TC-010-016` (espejo de literales y config) y la comprobación
  AST de imports de `TC-010-017`.
- La idempotencia PostgreSQL del esquema sigue cubierta por `TC-019-004` y
  `TC-019-018` en `tests/test_pg_schema.py` (incluidos en la corrida de T10).

## 5. Reubicación de `TC-010-014` (rollback SQLite)

`tests/test_rollback_sqlite.py` (nuevo) conserva **literalmente** la cobertura
anterior:

- respaldo `legacy.db.bak-*` antes de migrar;
- conservación de las tres filas y del estado `cancelled`;
- creación del índice parcial y ausencia del UNIQUE inline;
- segunda ejecución idempotente sin respaldo adicional;
- aborto con `RuntimeError("appointments migration aborted…")` ante duplicados
  activos, dejando la tabla y las filas intactas.

El archivo se identifica como verificación de rollback (plan D9/D10, T15) y
**no** como evidencia de paridad. Se incluye en la corrida completa para
reportar el número real; su resultado se registrará aparte en
`docs/evidencias/hu-019/rollback.md` durante T15.

## 6. Resultados reales

Todos los comandos se ejecutaron con:

```powershell
$env:TEST_DATABASE_URL='postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable'
```

### 6.1 Archivos de T10 + rollback

```text
python -m pytest -q tests/test_appointment_persistence.py tests/test_hu_006.py tests/test_hu_007.py tests/test_hu_010.py tests/test_rollback_sqlite.py
18 passed in 5.53s
```

### 6.2 Pruebas PostgreSQL existentes + archivos de T10 + rollback

```text
python -m pytest -q tests/test_pg_schema.py tests/test_pg_persistence.py tests/test_appointment_persistence.py tests/test_hu_006.py tests/test_hu_007.py tests/test_hu_010.py tests/test_rollback_sqlite.py
32 passed in 11.13s
```

Incluye `TC-019-003` a `TC-019-007` y `TC-019-018` contra catálogos reales y
concurrencia real.

### 6.3 Suite completa

```text
python -m pytest -q
24 failed, 372 passed in 116.01s
```

Salida completa en `docs/evidencias/hu-019/suite-postgres.txt` (primera corrida
completa contra PostgreSQL). **La paridad total es T11**; los 24 fallos
pertenecen a archivos que aún resuelven la persistencia por
`app.config["DATABASE_PATH"]` (SQLite) mientras `app` ya usa PostgreSQL.

## 7. Fallos pendientes de T11 (exactos)

| Archivo | Causa raíz | Tests afectados |
|---|---|---|
| `tests/test_appointment_routes.py` | `_count_appointments()` lee `app.config["DATABASE_PATH"]` (SQLite) tras un POST que escribe en PostgreSQL | `test_post_valido_redirige_a_confirmacion_y_crea_1_fila`; `test_post_horario_ocupado_da_slot_taken_y_exactamente_1_fila` |
| `tests/test_availability_routes.py` | `create_booking(..., app.config["DATABASE_PATH"])` siembra SQLite mientras las rutas leen PostgreSQL | `test_horarios_json_claves_available_y_occupied`; `test_disponibilidad_dia_lleno_ausente_en_a_presente_en_b` |
| `tests/test_double_booking_routes.py` | `_count_appointments()` y siembras usan `app.config["DATABASE_PATH"]` (SQLite) | `test_tc_006_006_post_sobre_ocupado_da_conflicto_claro`; `test_tc_006_007_ocho_post_concurrentes_una_sola_cita`; `test_tc_006_008_hora_ocupada_en_a_libre_en_servicio_b`; `test_tc_006_010_regresion_disponibilidad_tras_reserva_y_errores` |
| `tests/test_hu_008.py` | `_events_of_type()`/`_count_event_id()` y `Path(app.config["DATABASE_PATH"])` leen SQLite tras el flujo HTTP en PostgreSQL | `test_tc_008_015_http_end_to_end_303_y_evento_sent`; `test_tc_008_016_regresion_funcional_y_email_invalido` |
| `tests/test_hu_017.py` | `_database_path(app)` devuelve SQLite mientras las rutas leen PostgreSQL; los helpers insertan/leen en SQLite | `test_tc_017_002_post_correcto_renderiza_resumen_sin_cambios`; `test_tc_017_003_cita_a_dos_horas_muestra_restriccion_sin_cambios`; `test_tc_017_003_cita_a_seis_horas_muestra_resumen_sin_cambios`; `test_tc_017_004_flujo_completo_cancela_libera_horario_y_permite_rereserva`; `test_tc_017_004_confirmar_too_soon_no_cambia_nada`; `test_tc_017_005_primera_cancelacion_exactamente_un_evento`; `test_tc_017_005_webhook_caido_evento_failed_y_cancelacion_intacta`; `test_tc_017_006_reenvio_muestra_ya_cancelada_un_evento_cero_posts`; `test_tc_017_007_resumen_con_guard_y_doble_post_sin_duplicar`; `test_tc_017_008_cita_confirmada_muestra_estado_y_boton_cancelar`; `test_tc_017_008_cita_cancelada_muestra_estado_sin_boton`; `test_tc_017_009_enlace_del_correo_en_cita_cancelada_muestra_ya_cancelada`; `test_tc_017_012_mensajes_de_verificacion_corresponden_al_resultado`; `test_tc_017_012_mensajes_de_confirmacion_corresponden_al_resultado` |

Estos fallos son **esperados y de alcance T11**: no se ha relajado ninguna
aserción. T11 debe sustituir `DATABASE_PATH` por la fixture `database` (o por
`app.extensions[DATABASE_EXTENSION_KEY]`) en esos archivos.

Archivos que aún ejecutan SQLite de forma aislada y por eso no fallan, pero que
T11 también debe migrar: `tests/test_admin_routes.py`, `tests/test_hu_018.py`,
`tests/test_automation_service.py`, `tests/test_cancellation_service.py`,
`tests/test_availability_service.py`, `tests/test_appointment_service.py`,
`tests/test_double_booking_service.py` y los que aún usan `database_path`.

## 8. No vacuidad y comprobaciones adicionales

- Los tests de esquema consultan `information_schema.columns`, `pg_indexes`,
  `pg_index` y `pg_constraint` reales; ninguno usa `sqlite_master` ni `PRAGMA`.
- `TC-006-015` provoca duplicados reales en una tabla PostgreSQL **sin** índice
  parcial y el diagnóstico los detecta.
- Los tests de integridad provocan `psycopg.errors.UniqueViolation` real.
- `grep` de control sobre los cinco archivos de paridad de T10: no hay
  `sqlite3.connect`, `sqlite_master`, `PRAGMA` ni `database_path` ejecutables.
  `tests/test_rollback_sqlite.py` es la excepción deliberada.
- No se modificó código de producción.

## 9. Limitaciones y pendientes

- La paridad completa de la suite (0 FAIL, sin `skip`, Specs 004–018) queda para
  T11. El número real de esta corrida es **372 PASS / 24 FAIL**.
- `tests/test_rollback_sqlite.py` se recolecta en la corrida completa para
  reportar el total real, pero su PASS corresponde a la ruta SQLite de rollback,
  no a la paridad PostgreSQL. T15 lo ejecutará y registrará aparte.
- Como la sesión exige PostgreSQL siempre (D9), incluso ejecutar solo
  `tests/test_rollback_sqlite.py` requiere `TEST_DATABASE_URL` y el contenedor
  en marcha, aunque el test use SQLite internamente.
- `docs/operaciones/postgresql.md` conserva afirmaciones de la convivencia
  anterior («la suite general sigue en SQLite hasta T10/T11»); su actualización
  final corresponde a las tareas de documentación/cierre, no a T10.
- Sin commit ni push.

## 10. Reproducción

```powershell
# 1) Contenedor local (ver docs/operaciones/postgresql.md)
docker start consultorio-pg-019

# 2) DSN local de usar y tirar
$env:TEST_DATABASE_URL='postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable'

# 3) Archivos de T10 y rollback
python -m pytest -q tests/test_appointment_persistence.py tests/test_hu_006.py tests/test_hu_007.py tests/test_hu_010.py tests/test_rollback_sqlite.py

# 4) Suite completa (T11 pendiente)
python -m pytest -q
```
