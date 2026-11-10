# Evidencia T6 — Servicios de reserva, disponibilidad y mapeo de errores

> Trazabilidad: **Spec 019** (`RF-4`, `RF-5`, `RF-6`, `RF-14`, `RF-20`,
> `RF-21`; `CL-8`) → `plan.md` (D6, D13) → `tasks.md` **T6** → código →
> tests → esta evidencia.
> Fecha de ejecución: **2026-11-10**. Rama
> `feature/hu-019-migracion-postgres`.
> PostgreSQL real: **16.15** (`consultorio-pg-019`, `127.0.0.1:55432`).

## Alcance

- `consultorio/services/appointment_service.py`: `DatabaseResource` en las
  firmas, sin `sqlite3`/`Path`; la precomprobación y el `INSERT` se ejecutan
  dentro del mismo mapeo de errores.
- `consultorio/services/cancellation_flow_service.py`: recibe el recurso de
  persistencia y delega igual que antes en `cancel_appointment()`.
- `consultorio/web/appointments.py`, `consultorio/web/cancellation.py` y
  `consultorio/web/admin.py`: resuelven el `Database` registrado por
  `create_app()` mediante `consultorio/web/persistence.py`.
- `consultorio/persistence/database.py`:
  - `is_slot_uniqueness_violation()`: solo la violación del índice parcial
    `ux_appointments_slot_open`.
  - `is_persistence_unavailable()`: reconoce `sqlite3.OperationalError`,
    `sqlite3.InterfaceError`, `psycopg.OperationalError` e
    `psycopg.InterfaceError`.
  - `translate_persistence_error()`: traduce indisponibilidad a
    `PersistenceUnavailable`; devuelve intactos los demás errores.
  - `Database._is_unavailable_error()` usa el helper compartido.
- `consultorio/config.py`: `TestConfig.PERSISTENCE_BACKEND = "sqlite"` para
  mantener la suite general en SQLite durante T6/T10.
- `tests/test_pg_persistence.py`: TC-019-008 (mapeo de errores y concurrencia
  de 8 hilos).
- `tests/test_double_booking_service.py`: TC-006-005 actualizado; un
  lock/`OperationalError` ahora es `PersistenceUnavailable`, no `SLOT_TAKEN`.
- `tests/test_pg_resilience.py`: cobertura mínima de la traducción de
  `sqlite3.OperationalError`/`InterfaceError` en `Database.connection()`.
- `tests/test_hu_010.py`: se retira `sqlite3` de la lista blanca de
  `appointment_service`; no hay imports de driver en los servicios.

T6 no modificó `specs/`, `MEMORY.md` ni `tasks.md`; el worktree contiene cambios
previos de esas fuentes (enmiendas de 2026-11-08 y memoria de 2026-11-09). No se
implementó T7+.
No se añadieron literales, respuestas 503 ni cambios visuales. No se
reescribió la lógica de `automation_service`/`email_service`; ambas reciben el
mismo recurso `Database` en runtime sin cambios funcionales. No se hizo commit
ni push.

## Corrección aplicada (D6)

La primera versión de T6 dejaba escapar `sqlite3.OperationalError` desde
`create_booking()` cuando el repositorio se usaba con la ruta SQLite
transitoria. Eso evitaba `SLOT_TAKEN`, pero no cumplía D6: la indisponibilidad
debe convertirse en `PersistenceUnavailable` en la frontera de persistencia.

Ahora:

| Situación | Resultado |
|---|---|
| `IntegrityError`/`UniqueViolation` del slot activo | `SLOT_TAKEN` |
| `OperationalError`, `InterfaceError`, timeout/límite de conexión | `PersistenceUnavailable` |
| `ValueError` u otro error de programación | Se propaga sin cambios |
| `PersistenceUnavailable` ya traducida | Se vuelve a lanzar sin envolver |

`create_booking()` no captura `sqlite3` ni ningún driver: usa el helper de
`consultorio.persistence.database`.

## Comandos ejecutados

Sesión de PowerShell (el DSN real no se escribe en la evidencia):

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"

python -m pytest -q tests/test_double_booking_service.py tests/test_pg_persistence.py
python -m pytest -q
```

## Mapeo de errores y concurrencia — TC-019-008 / TC-006-005

Salida literal:

```text
............                                                             [100%]
12 passed in 5.19s
```

| Comprobación | Resultado |
|---|---|
| Insertar en un slot ya ocupado en PostgreSQL produce `UniqueViolation` con `constraint_name = ux_appointments_slot_open` y `create_booking()` devuelve `SLOT_TAKEN`. | PASS |
| Un `Database` apuntando a un puerto cerrado produce `PersistenceUnavailable` al reservar; **no** devuelve `SLOT_TAKEN` y no inserta filas. | PASS |
| Un `sqlite3.OperationalError("database is locked")` en el repositorio se traduce a `PersistenceUnavailable`; el mensaje del driver no se filtra. | PASS |
| `ValueError` sigue propagándose sin traducción. | PASS |
| 8 hilos llaman simultáneamente a `create_booking()` sobre el mismo slot: exactamente 1 retorna `Appointment`, 7 retornan `SLOT_TAKEN`, no hay excepciones no controladas y la tabla queda con 1 fila. | PASS |
| `Database.connection()` traduce `sqlite3.OperationalError` y `sqlite3.InterfaceError` a `PersistenceUnavailable`. | PASS |

## Regresión de rutas y servicios

La suite completa mantiene la configuración SQLite de la suite general y las
rutas resuelven el `Database` registrado en `app.extensions`.

## Suite completa

```text
........................................................................ [ 18%]
........................................................................ [ 37%]
........................................................................ [ 56%]
........................................................................ [ 75%]
........................................................................ [ 94%]
......................                                                   [100%]
382 passed in 49.92s
```

## Comprobación de no vacuidad

1. Se sustituyó temporalmente `translate_persistence_error()` por
   `return error` y se ejecutó TC-006-005: el test **falló** porque recibió
   `sqlite3.OperationalError: database is locked` en lugar de
   `PersistenceUnavailable`. Después se restauró el helper y el test volvió a
   PASS.
2. En la comprobación anterior de T6, desactivar el clasificador de unicidad
   hizo fallar TC-019-008 con `psycopg.errors.UniqueViolation` en lugar de
   `SLOT_TAKEN`; restaurado, volvió a PASS.

Ambas comprobaciones demuestran que los tests detectan la pérdida de cada
mapeo y no pasan por vacuidad.

## Revisión técnica

El `@revisor` emitió **APROBADO** para T6 el **2026-11-10**, tras verificar de
forma independiente:

- suite completa: **382 PASS**, sin `skip`;
- tests T6: **12 PASS**; regresión T6 + HU-010: **64 PASS**;
- sin `TEST_DATABASE_URL`, los tests PostgreSQL fallan explícitamente (no
  `skip`);
- no-vacuidad de ambos mapeos D6 comprobada por mutación;
- no se detectaron defectos bloqueantes en el alcance T6.

## Pendientes y límites

- La suite general sigue en SQLite por decisión transitoria de T6/T10; la
  migración completa de fixtures es T10.
- No se ejecutó validación visual porque T6 no modifica plantillas, estilos ni
  navegación.
- El cierre documental (`MEMORY.md` y `tasks.md`) lo realiza el coordinador.
