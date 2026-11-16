# T15 - Rollback temporal a SQLite: verificacion real

> Trazabilidad: Spec 019 (`specs/019_migrar-postgresql/spec.md`, RF-18, RF-19;
> RNF-7; CL-6; RF-28) -> `plan.md` D10 (y riesgos R-07/R-14) -> `tasks.md` T15
> -> este documento.
> Rama: `feature/hu-019-migracion-postgres`. HEAD al ejecutar: `309a442`.
> Fecha de ejecucion: 2026-11-13.
> Procedimiento operativo: `docs/operaciones/postgresql.md`, seccion
> "Rollback temporal a SQLite".

## 1. Alcance y entorno

T15 documenta y prueba la via de repliegue temporal al almacenamiento anterior.
**No es evidencia de paridad**: la suite de paridad se ejecuta siempre contra
PostgreSQL (RF-28) y el resultado de este archivo se registra aparte.

Entorno real de esta verificacion:

| Elemento | Valor |
|---|---|
| PostgreSQL | Docker local, contenedor `consultorio-pg-019`, `postgres:16-alpine`, version real 16.15, `127.0.0.1:55432` |
| Base de pruebas | `consultorio_dev` con esquemas aislados `test_hu019_<uuid>`; nunca se escribe en `public` |
| SQLite | Ficheros temporales creados por pytest en `tmp_path` |
| Driver | `psycopg` 3.3.8 (implementacion local ya documentada en T1) |
| Python / pytest | 3.14.8 / 9.1.1 |

Limites explicitos:

- **No se ejecuto un rollback sobre produccion**: no se toco el servicio de
  Render ni el proyecto de Neon. T14 ya habia verificado el despliegue; T15 se
  ejecuta en local.
- **No se creo un snapshot real en Neon**: el procedimiento (snapshot manual,
  hora de corte UTC y registro) queda documentado en
  `docs/operaciones/postgresql.md`; su ejecucion corresponde a un rollback real
  con datos, que no forma parte de T15.
- En Render, el fichero SQLite del rollback vive en un disco efimero; se pierde
  en redespliegue, reinicio o spin-down. Es una contingencia de corta duracion,
  no almacenamiento duradero.

## 2. Cambios verificados

`tests/test_rollback_sqlite.py` conserva `TC-010-014` y anade `TC-019-021`.

`TC-019-021` comprueba, con persistencia real y sin mocks:

1. crea una cita en PostgreSQL (esquema aislado `test_hu019_<uuid>`);
2. cambia el interruptor a `PERSISTENCE_BACKEND=sqlite` con `DATABASE_PATH`
   temporal (`DatabaseTarget.from_config`) y comprueba que la cita de PostgreSQL
   no es visible en SQLite;
3. crea una cita durante el rollback, solo en SQLite;
4. vuelve a PostgreSQL y comprueba que la cita original sigue intacta y que la
   fila SQLite **no** se traslado (mismo `document_number` ausente y horario
   libre);
5. arranca la app real con `create_app` y configuracion SQLite
   (`DATABASE_URL=""`), escribe una cita a traves del `Database` registrado y
   comprueba que quedo persistida en el fichero SQLite tras el teardown.

`TC-010-014` conserva integra la cobertura de la migracion del esquema SQLite
legado: respaldo `.bak-*`, conservacion de filas, idempotencia y aborto ante
duplicados activos.

## 3. Comandos y resultados reales

Los comandos se ejecutaron en PowerShell con el PostgreSQL local arriba y sin
`DATABASE_URL` de produccion en el entorno.

### 3.1 Suite completa contra PostgreSQL

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m pytest -q
```

Salida real (final):

```text
399 passed in 252.13s (0:04:12)
EXIT_CODE=0
```

Interpretacion: baseline vigente 398 PASS + 1 test nuevo (`TC-019-021`) =
**399 PASS / 0 FAIL / 0 skipped / 0 xfail**. La suite no usa `skip` ni `xfail`.

### 3.2 Archivo de rollback, ejecutado por separado

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m pytest -v tests/test_rollback_sqlite.py
```

Salida real:

```text
collected 2 items

tests/test_rollback_sqlite.py::test_tc_010_014_migracion_indice_parcial_respaldo_idempotente_y_aborto PASSED [ 50%]
tests/test_rollback_sqlite.py::test_tc_019_021_rollback_switch_isolates_stores_and_postgres_data_survives PASSED [100%]

2 passed in 0.53s
```

Resultado: **TC-019-021 PASS** y **TC-010-014 PASS**.

### 3.3 Manifiesto de Render

```powershell
python -m pytest -q tests/test_render_manifest.py
```

Salida real:

```text
1 passed in 0.05s
```

### 3.4 Aislamiento de PostgreSQL tras las ejecuciones

Comprobado con `docker exec consultorio-pg-019 psql ...`:

```text
residual_test_schemas (test_hu019_%) = 0
public.appointments.rows            = 0
public.automation_events.rows       = 0
public.schema_migrations.rows       = 4
public.schema_migrations.max_version = 4
SELECT version() = PostgreSQL 16.15 on x86_64-pc-linux-musl
```

Los tests usaron esquemas aislados y los eliminaron; no se escribio en `public`.

## 4. Resultado por caso

| Caso | Ubicacion | Resultado | Naturaleza |
|---|---|---|---|
| TC-019-021 | `tests/test_rollback_sqlite.py` | **PASS** | Verificacion de rollback |
| TC-010-014 | `tests/test_rollback_sqlite.py` | **PASS** | Verificacion de rollback |
| Suite completa | `tests/` | **399 PASS / 0 FAIL** | Total de la suite; incluye los casos de rollback y el residual |
| `test_render_manifest.py` | `tests/test_render_manifest.py` | **PASS (1)** | Configuracion de despliegue |

> **Separacion exigida por T15/RF-28:** `TC-010-014` y `TC-019-021` son
> verificaciones de la ruta de rollback. No se usan como evidencia de paridad de
> las Specs 004-018; esa evidencia es el subconjunto de paridad de la suite contra
> PostgreSQL. Los **399** son el total de `tests/` e incluyen, además de la
> paridad, los casos de rollback (`TC-010-014`, `TC-019-021`), el residual
> `test_sqlite_rollback_route_keeps_repository_contract` y los casos SQLite de
> `test_pg_resilience.py`; el subconjunto de paridad pura es menor.

## 5. Perdida aceptada y snapshot

- No hay migracion automatica de datos entre motores (RF-19). Las filas creadas
  en PostgreSQL despues del corte no estan disponibles durante el rollback y se
  pierden; las filas creadas en SQLite durante el rollback no se trasladan a
  PostgreSQL al volver.
- La perdida esta **aceptada por la usuaria** (decision de aprobacion 6 de la
  Spec 019; CL-6).
- Antes de un rollback con datos reales se exige un **snapshot manual en Neon**
  y registrar la **hora de corte en UTC**. El procedimiento y los datos a
  registrar estan en `docs/operaciones/postgresql.md`.
- En esta ejecucion no se creo snapshot porque no hubo rollback real ni datos
  reales; se documento el procedimiento, no se simula su ejecucion.

## 6. Revision de accesos directos a SQLite

Busqueda realizada sobre `tests/`:

- `sqlite3.connect(...)`: solo en `tests/test_rollback_sqlite.py`.
- `get_connection(...)`/`init_db(...)`: en `tests/test_rollback_sqlite.py` y
  `init_db` en `tests/test_hu_019.py::test_sqlite_rollback_route_keeps_repository_contract`.
  Este ultimo es un test de regresion de la **ruta de rollback** ya documentado
  en T5 y no se usa como paridad; queda fuera del alcance de T15, por lo que no
  se modifica.
- El resto de la suite de paridad usa las fixtures PostgreSQL (`database`,
  `pg_target`, `pg_schema`) y no abre SQLite.

## 7. Limitaciones y pendientes

- No se verifico el interruptor sobre Render/Neon reales (fuera de alcance de
  T15; T14 ya cubrio el despliegue y T17 cubrira el QA de la HU).
- No se ejecuto una restauracion desde un snapshot de Neon.
- La ruta SQLite durante el rollback en Render es efimera: cualquier fila
  creada alli se pierde en el siguiente redespliegue/reinicio y tampoco se
  traslada a PostgreSQL.
- `TC-019-021` usa `DATABASE_URL=""`; el procedimiento documentado conserva el
  DSN durante el rollback. El codigo ignora el DSN cuando el backend es
  `sqlite`, por lo que la diferencia es de configuracion literal, no de
  comportamiento.
- La retirada del interruptor, la ruta SQLite y esta documentacion corresponde a
  T18, solo tras la aceptacion funcional de la migracion (RF-18, R-14).

## 8. Seguridad

No se incluyen secretos, DSN reales, credenciales de Neon/Render ni datos
personales. Los datos de prueba son ficticios: `TC-019-021` usa
`example.invalid` y `TC-010-014` conserva los correos ficticios `@correo.com`
del caso heredado.
