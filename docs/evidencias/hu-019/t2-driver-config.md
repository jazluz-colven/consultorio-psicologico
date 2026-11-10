# Evidencia T2 — Dependencia `psycopg` y configuración por entorno

- **Fecha:** 2026-11-09
- **Rama:** `feature/hu-019-migracion-postgres`
- **HEAD:** `8ce511f`
- **Tarea:** T2 de `specs/019_migrar-postgresql/tasks.md`
- **Requisitos cubiertos:** RF-15, RF-16, RF-17; RNF-1, RNF-6, RNF-8
- **Prueba:** TC-019-001 (`tests/test_pg_resilience.py`)
- **Alcance:** dependencia + configuración + pruebas de configuración. No se
  modificaron servicios, capa de persistencia, plantillas ni cableado de la
  aplicación (T3/T4).
- **Estado:** **COMPLETADA** (2026-11-09); **APROBADA por `@revisor`** y
  cerrada por el coordinador. La usuaria aceptó los binarios oficiales de
  EDB sin firma Authenticode, verificados por SHA-256 oficial, y el uso de
  PostgreSQL 16.15-5 en local (ver §2).

## 1. Driver local (opción A)

- `psycopg` instalado: **3.3.8**.
- Implementación usada en local: `python` (`PSYCOPG_IMPL=python`), con
  `libpq.dll` de los binarios oficiales de PostgreSQL **16.15-5**.
- El servidor local de pruebas sigue siendo PostgreSQL **16.15** (contenedor
  `consultorio-pg-019`); el cliente `libpq` local es 16.15-5.
- El módulo binario de `psycopg` (`pq.cp314-win_amd64.pyd`) está bloqueado por
  la política de control de aplicaciones del equipo, por eso se usa la
  implementación Python.

Comprobación de versión:

```text
$ python -c "import psycopg; print(psycopg.__version__)"
3.3.8
```

## 2. Binarios 16.15-5, SHA-256 y firma del `libpq.dll`

- Origen: zip oficial de EDB
  `https://get.enterprisedb.com/postgresql/postgresql-16.15-5-windows-x64-binaries.zip`
- Tamaño verificado: `373254386` bytes.
- Checksum oficial:
  `https://get.enterprisedb.com/postgresql/postgresql-16.15-5-windows-x64-binaries.zip.sha256`
- SHA-256 oficial publicado por EDB:
  `43bb45f173a6f08cf1d29a97a6d8deb119e8e8093a24c00d2d1001a0ccaa8281`
- SHA-256 calculado con `Get-FileHash -Algorithm SHA256`: **coincidente** con
  el oficial (verificado el 2026-11-09 antes de extraer).
- Extracción: `%LOCALAPPDATA%\opencode\postgresql-16.15-5\` (fuera del
  repositorio; no se versiona ningún binario).
- Versión del archivo `libpq.dll`: `16.15`; `libpq` reportado por `psycopg`:
  `160015`.

Verificación:

```text
$ (Get-Item "%LOCALAPPDATA%\opencode\postgresql-16.15-5\pgsql\bin\libpq.dll").VersionInfo.FileVersion
16.15
$ Get-AuthenticodeSignature "%LOCALAPPDATA%\opencode\postgresql-16.15-5\pgsql\bin\libpq.dll"
Status: NotSigned
```

**Hallazgo y decisión A1:** en el zip oficial de EDB 16.15-5, `libpq.dll`
**no** lleva firma Authenticode embebida (`Get-AuthenticodeSignature` devuelve
`NotSigned`); el resto de binarios comprobados (`postgres.exe`, `psql.exe`)
tampoco. La **usuaria aprobó A1 el 2026-11-09**: se aceptan los binarios
oficiales de EDB sin firma Authenticode, verificados por el SHA-256 oficial, y
se usa PostgreSQL **16.15-5** en local. La autenticidad se controla, por tanto,
con el hash oficial coincidente y el tamaño exacto; no se exige firma. El
servidor local de pruebas sigue siendo PostgreSQL **16.15** (contenedor
`consultorio-pg-019`); solo cambia el cliente `libpq`. No se versiona ningún
binario.

## 3. Conexión real (DSN redactado)

Sesión: `pgsql\bin` de 16.15-5 en el `PATH` y `PSYCOPG_IMPL=python`. Comando
(contraseña local sustituida):

```text
$ python -c "import psycopg; print(psycopg.__version__, psycopg.pq.__impl__, psycopg.pq.version())"
3.3.8 python 160015
$ python -c "import psycopg; conn = psycopg.connect('postgresql://consultorio_dev:<redactado>@localhost:55432/consultorio_dev?sslmode=disable&connect_timeout=5'); print('SELECT 1 ->', conn.execute('SELECT 1').fetchone()[0]); print(conn.execute('SELECT version()').fetchone()[0]); conn.close()"
```

Salida:

```text
SELECT 1 -> 1
PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
```

El cliente 16.15-5 conecta sin errores contra el servidor PostgreSQL 16.15.

## 4. TC-019-001

```text
$ python -m pytest tests/test_pg_resilience.py -q
..................                                                       [100%]
18 passed in 0.16s
```

Casos cubiertos:

- Backend por defecto `postgres`.
- `PERSISTENCE_BACKEND` inválido lanza `ValueError`.
- `DATABASE_URL` ausente no lanza error.
- Host no local sin `sslmode=require`/`verify-ca`/`verify-full` lanza
  `ValueError` y el mensaje no filtra el DSN.
- Host no local con `sslmode=require` se acepta.
- Hosts locales (`localhost`, `127.0.0.1`, `::1`) con `sslmode=disable` se
  aceptan.
- `PERSISTENCE_BACKEND=sqlite` + `DATABASE_PATH` se acepta e ignora TLS.
- Parseo de límites/timeouts y caída a defaults seguros con valores inválidos o
  no positivos.

## 5. Suite completa

```text
$ python -m pytest -q
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 63%]
........................................................................ [ 85%]
..................................................                       [100%]
338 passed in 30.39s
```

Corrida repetida el 2026-11-09 con el `PATH` de 16.15-5 y `PSYCOPG_IMPL=python`
en la sesión: **338 PASS / 0 FAIL**. Sin regresiones. El baseline de 2026-11-08
era 320 PASS; los 18 casos nuevos de TC-019-001 elevan el total a 338 PASS.

## 6. Archivos de la tarea

- `requirements.txt` (`psycopg[binary]==3.3.8`).
- `consultorio/config.py` (`DATABASE_URL`, `PERSISTENCE_BACKEND`, límites,
  timeouts y validación TLS).
- `tests/test_pg_resilience.py` (TC-019-001).
- `tests/test_admin_content.py` (actualización mínima del listado esperado de
  dependencias para incluir la dependencia aprobada por la Spec 019).
- `docs/operaciones/postgresql.md` (preparación local del `libpq`).
- `docs/evidencias/hu-019/t2-driver-config.md` (este documento).

## 7. Trazabilidad

Spec 019 (`RF-15`, `RF-16`, `RF-17`; `RNF-6`, `RNF-8`) → plan D1, D2, D9 →
`tasks.md` T2 → `consultorio/config.py`, `requirements.txt` →
`tests/test_pg_resilience.py` → esta evidencia.

## 8. Revisión técnica y riesgos no bloqueantes

- **Revisor:** `@revisor` emitió **APROBADO** el 2026-11-09, sin defectos
  bloqueantes. T2 cerrada por el coordinador.
- **Riesgos no bloqueantes registrados:**
  - Un DSN con `sslmode` duplicado podría eludir la validación TLS; endurecer
    la comprobación (usar el último valor o rechazar duplicados) antes de T14.
  - `DATABASE_PATH` se lee con cualquier backend; condicionarlo al rollback
    SQLite en T3/T4/T15.
  - RF-17 y la indisponibilidad de rutas quedan parcialmente cubiertas en T2 y
    se completan en T3/T4/T9; no se declaran verificadas aquí.
  - Robustecer la restauración del fixture de TC-019-001 y corregir el
    docstring de `tests/test_admin_content.py`.
