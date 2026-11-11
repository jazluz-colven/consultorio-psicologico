# T11 — Migración de la suite de servicios, rutas y HU a PostgreSQL

> Trazabilidad: Spec 019 (`specs/019_migrar-postgresql/spec.md`, RF-4..RF-9,
> RF-28; RNF-5; CL-10) → `plan.md` D9 y §6.1–§6.3 → `tasks.md` T11 → este
> documento.
> Rama: `feature/hu-019-migracion-postgres`. HEAD al iniciar: `673d799`.
> Fecha de ejecución: 2026-11-11. PostgreSQL local: `postgres:16-alpine`
> (contenedor `consultorio-pg-019`, `127.0.0.1:55432`).

## 1. Alcance

T11 migra a PostgreSQL real la persistencia de los tests de servicios, rutas y
HU de las Specs 004–018. Los archivos modificados son:

- `tests/conftest.py`
- `tests/test_appointment_routes.py`
- `tests/test_availability_routes.py`
- `tests/test_double_booking_routes.py`
- `tests/test_admin_routes.py`
- `tests/test_appointment_service.py`
- `tests/test_availability_service.py`
- `tests/test_double_booking_service.py`
- `tests/test_email_service.py`
- `tests/test_automation_service.py`
- `tests/test_cancellation_service.py`
- `tests/test_cancellation_flow_service.py`
- `tests/test_hu_008.py`
- `tests/test_hu_017.py`
- `tests/test_hu_018.py`

Además se actualizan solo documentación y trazabilidad:
`docs/operaciones/postgresql.md`, `docs/evidencias/hu-019/suite-postgres.txt`,
`docs/evidencias/hu-019/t11-suite.md` (nuevo) y el marcador de T11 en
`specs/019_migrar-postgresql/tasks.md`.

No se modifica ninguna aserción funcional ni ningún literal contractual. Los
cambios son de acceso a persistencia:

- `database_path` / `app.config["DATABASE_PATH"]` → fixture `database` o
  `app.extensions[DATABASE_EXTENSION_KEY]`.
- `sqlite3.connect(...)` → `Database.connection()` / `Database.transaction()`.
- Marcadores `?` → `%s`; filas leídas por nombre (`dict_row`).
- Catálogos y mocks de errores SQLite → `psycopg.errors` /
  `is_slot_uniqueness_violation` (índice parcial `ux_appointments_slot_open`).

## 2. Estrategia por tipo de archivo

### 2.1 Rutas

Los helpers `_count_appointments(app)` y `_event_counts(app)` usan
`app.extensions[DATABASE_EXTENSION_KEY].connection()`. Las rutas siguen usando
la app real, pero el conteo/lectura se hace contra el esquema PostgreSQL
aislado de la fixture `app`.

`admin_app` y `hu_app` dejan de construir una app SQLite con `TempConfig` y
parten de la fixture `app` (PostgreSQL), actualizando solo la configuración
necesaria (`CONSULTORIO_ADMIN_TOKEN`, `AUTOMATION_WEBHOOK_URL`). El caso de
«token vacío» cambia temporalmente el token sobre la misma app y lo restaura,
sin abrir una segunda base.

### 2.2 Servicios

Las funciones auxiliares reciben el objeto `Database` de la fixture `database`.
Las consultas directas usan `database.connection()` (solo lectura) o
`database.transaction()` (UPDATE/INSERT auxiliar). El test de concurrencia de
HU-006 mantiene su semántica original: ocho hilos, una sola cita.

En `test_double_booking_service.py` el mock de unicidad usa una subclase de
`psycopg.errors.UniqueViolation` cuyo `diag.constraint_name` es
`ux_appointments_slot_open`; la indisponibilidad usa
`psycopg.OperationalError`. Se conservan las aserciones sobre `SLOT_TAKEN`,
`PersistenceUnavailable` y propagación de `ValueError`.

### 2.3 HU-017 y HU-018

Se migran los helpers de eventos, la lectura de estados y los conteos. El flujo
completo de cancelación/reprogramación, los cuatro eventos de la reprogramación,
la ventana de 3 horas, el orden cancelar→crear y los casos de HU-018 se
ejecutan contra PostgreSQL. No se relaja ninguna aserción.

## 3. Resultado de la suite

Comando (sesión PowerShell):

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"
python -m pytest -q
```

| Corrida | Resultado | Duración |
|---|---|---|
| Baseline antes de T11 | 372 passed, 24 failed, 0 skipped | — |
| Primera corrida tras la migración | **396 passed, 0 failed, 0 skipped** | 387.43 s |
| Segunda corrida (evidencia) | **396 passed, 0 failed, 0 skipped** | 421.48 s |

Salida completa real: `docs/evidencias/hu-019/suite-postgres.txt` (UTF-8, sin
BOM).

No se usa `skip` ni `xfail`. Sin `TEST_DATABASE_URL` la sesión se detiene al
inicio (`pytest_configure`), como exige D9/CL-10.

## 4. Aislamiento y estado de `public`

Comprobado tras la segunda corrida contra el contenedor local:

```text
residual_test_schemas = []          # ningún test_hu019_* quedó creado
public.appointments.rows = 0
public.automation_events.rows = 0
public.schema_migrations.max_version = 4
public.schema_migrations.rows = 4
```

Los tests siguen usando `test_hu019_<uuid>` y `DROP SCHEMA ... CASCADE`; no se
escribió en las tablas de `public`.

## 5. Cobertura HU-018

Los casos de HU-018 (`TC-018-001`…`TC-018-019`) se reparten entre
`tests/test_admin_routes.py` (nueve casos de rutas administrativas),
`tests/test_admin_content.py` (`TC-018-014` y `TC-018-015`) y
`tests/test_hu_018.py` (siete casos de eventos y reprogramación): **18 casos en
total**. Los tres archivos pasan íntegros contra PostgreSQL:

- token y 404/403 sin filtrar datos;
- detalle, resumen y formularios;
- cancelación delegada e idempotente;
- reprogramación con sus cuatro eventos y el enlace de cancelación;
- guardas de horario ocupado, fecha inválida y RF-9;
- carrera tras cancelar y orden cancelar→crear.

## 6. Límites deliberados (no son paridad)

- `tests/test_rollback_sqlite.py` sigue verificando la ruta SQLite de rollback
  (T5/D9). No forma parte de la paridad PostgreSQL.
- `tests/test_pg_resilience.py` conserva casos de configuración y de traducción
  de errores del backend SQLite (D6), además de los casos PostgreSQL.
- `tests/test_hu_019.py::test_sqlite_rollback_route_keeps_repository_contract`
  comprueba la compatibilidad del repositorio con la ruta de rollback; es
  evidencia de T5, no de paridad.
- La fixture `app` sigue arrancando `create_app` con configuración SQLite
  temporal para no tocar `public`; la retirada de `init_db` en producción
  pertenece a T18.

## 7. Validación visual

T11 no modifica plantillas, estilos, navegación ni comportamiento visual. No se
requiere comprobación con navegador ni capturas para esta tarea.
