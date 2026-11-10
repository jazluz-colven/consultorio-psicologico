# Evidencia T1 — PostgreSQL 16 local en Docker

- **Fecha:** 2026-11-09
- **Rama:** `feature/hu-019-migracion-postgres`
- **HEAD:** `8ce511f`
- **Ámbito:** T1 de `specs/019_migrar-postgresql/tasks.md` (RF-29; RNF-2,
  RNF-7; CL-10).
- **Resultado de la verificación E-019-01: PASS**, con el contenedor en marcha
  al cierre.

## Entorno

| Elemento | Valor verificado |
|---|---|
| Sistema | Windows (win32), PowerShell 5.1 |
| Docker client / daemon | 29.9.2 |
| Imagen | `postgres:16-alpine` |
| Contenedor | `consultorio-pg-019` |
| Puerto local | `127.0.0.1:55432` → `5432` |
| Base de datos | `consultorio_dev` |
| Usuario | `consultorio_dev` |
| Volumen | `consultorio-pgdata-019` |
| PostgreSQL | 16.15 |

## Incidencia inicial (resuelta)

El daemon no estaba arrancado. `docker info --format '{{.ServerVersion}}'`
devolvió:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: El sistema no puede encontrar el archivo especificado.
```

Se arrancó Docker Desktop con
`Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"` (sin
instalar nada ni cambiar la configuración del sistema). El daemon respondió
**5 segundos después**:

```text
29.9.2
```

## Creación del contenedor

Comando ejecutado (contraseña local de usar y tirar **redactada** en esta
evidencia; no es un secreto):

```powershell
docker run -d --name consultorio-pg-019 -e POSTGRES_DB=consultorio_dev -e POSTGRES_USER=consultorio_dev -e POSTGRES_PASSWORD=<redactada: contraseña local de usar y tirar> -p 127.0.0.1:55432:5432 -v consultorio-pgdata-019:/var/lib/postgresql/data postgres:16-alpine
```

Salida:

```text
15d1e4acf225da5e23c3e45ccb40c6b2a46648ca5edc951dce436c9e77bde2e8
```

`pg_isready` confirmó la disponibilidad **2 segundos después** de arrancar:

```text
/var/run/postgresql:5432 - accepting connections
```

## Comprobaciones E-019-01

### `docker ps`

```text
NAMES                IMAGE                STATUS         PORTS
consultorio-pg-019   postgres:16-alpine   Up 2 minutes   127.0.0.1:55432->5432/tcp
```

### `SELECT version()`

```text
                                         version
------------------------------------------------------------------------------------------
 PostgreSQL 16.15 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
(1 row)
```

### Versión, base y usuario

```text
$ docker exec consultorio-pg-019 psql -U consultorio_dev -d consultorio_dev -tAc "SHOW server_version;"
16.15

$ docker exec consultorio-pg-019 psql -U consultorio_dev -d consultorio_dev -tAc "SELECT current_database(), current_user;"
consultorio_dev|consultorio_dev
```

### Puerto accesible desde el host

```text
$ (TcpClient) Connect('127.0.0.1', 55432)
TCP 127.0.0.1:55432 OPEN
```

### Volumen

```text
$ docker volume ls --filter "name=consultorio-pgdata-019" --format "{{.Name}}"
consultorio-pgdata-019
```

## Criterios de aceptación de T1

- [x] `docs/operaciones/postgresql.md` contiene el comando `docker run`
  reproducible con `postgres:16-alpine`, puerto 55432, base y usuario de
  desarrollo y contraseña local de usar y tirar marcada como no secreta.
- [x] `SELECT version()` devuelve **PostgreSQL 16.15** (16.x).
- [x] El documento explica `TEST_DATABASE_URL` y el fallo explícito de la suite
  sin PostgreSQL (sin `skip`).
- [x] No se han incluido credenciales de Neon/Render, DSN reales ni datos de
  pacientes. La contraseña del contenedor local está redactada en esta
  evidencia.
- [x] Evidencia real registrada tras ejecutar el contenedor; no se declara PASS
  por inspección.

## Regresión de la suite vigente

T1 es documental y de infraestructura: no modifica código ni pruebas. Aun así
se ejecutó la suite vigente (todavía en SQLite; la migración a PostgreSQL
corresponde a T10–T11):

```text
$ python -m pytest -q
320 passed in 41.65s
```

## Estado del contenedor al cierre

```text
consultorio-pg-019   postgres:16-alpine   Up   127.0.0.1:55432->5432/tcp
```

El contenedor se deja **en marcha** para las siguientes tareas de la Spec 019.

## Observación para tareas posteriores (no bloquea T1)

En el Python del sistema hay un `psycopg` instalado previamente, pero su
importación falla por AppLocker al cargar la implementación binaria:

```text
ImportError: no pq wrapper available.
- couldn't import psycopg 'binary' implementation: DLL load failed while importing pq: Una directiva de Control de aplicaciones bloqueó este archivo.
- couldn't import psycopg 'python' implementation: libpq library not found
```

Esto no afecta a T1 (la verificación se hizo con `psql` dentro del contenedor)
y deberá resolverse o verificarse al implementar la dependencia en T2.
