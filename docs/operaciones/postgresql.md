# PostgreSQL local para desarrollo y pruebas

> Trazabilidad: Spec 019 (`specs/019_migrar-postgresql/spec.md`) → `plan.md`
> (D2, D9, D15; §6.1) → `tasks.md` T1 → este documento.
> Evidencia de la puesta en marcha: `docs/evidencias/hu-019/setup-local.md`.

Este documento describe cómo levantar un PostgreSQL 16 **local y reproducible**
en Docker para desarrollo y para la suite de pruebas. La base gestionada (Neon)
se reserva para la verificación E2E y **no** se usa en el desarrollo diario.

Alcance actual: T1 (entorno local), T2 (dependencia `psycopg` y configuración
por entorno: `DATABASE_URL`, `PERSISTENCE_BACKEND`, límites y timeouts),
T3 (capa de conexiones y traducción de errores), T4 (DDL PostgreSQL
idempotente, advisory lock, arranque tolerante y recuperación perezosa), T5
(repositorios de citas y eventos en dialecto PostgreSQL con adaptador SQLite
de rollback), T6 (servicios y rutas con el objeto `Database`), T7 (atomicidad
de la cancelación 010/017/018), T8 (literal coordinado de indisponibilidad),
T9 (errores HTTP/UX de indisponibilidad), T10/T11 (fixtures PostgreSQL y
migración de la suite de paridad), T12 (pruebas no vacuas de integridad,
concurrencia, atomicidad, cold start y errores), T13 (E2E contra Neon desde
entorno controlado), T14 (recreación del servicio en Render con Neon y
verificación de persistencia tras redespliegue y spin-down) y T15 (rollback
temporal a SQLite documentado y probado, sin evidencia de paridad). Desde T11, los
tests de servicios, rutas y HU de las Specs 004–018 se ejecutan contra
PostgreSQL; la ruta SQLite se conserva únicamente como rollback temporal y su
evidencia vive en `tests/test_rollback_sqlite.py`.

## Requisitos

- Docker Desktop o Docker Engine en marcha. El cliente de este equipo es
  Docker 29.9.2 y la imagen verificada es `postgres:16-alpine`.
- PowerShell en Windows.
- No hace falta instalar `psql` en el host: las comprobaciones se hacen con
  `docker exec`.

Comprobar que el daemon responde antes de continuar:

```powershell
docker info --format '{{.ServerVersion}}'
```

Si falla con `npipe:////./pipe/dockerDesktopLinuxEngine`, Docker Desktop no
está arrancado. Inícialo y espera hasta que el comando anterior devuelva una
versión.

## Driver local: `psycopg` con `libpq` oficial

`requirements.txt` fija `psycopg[binary]==3.3.8` (plan D1). En este equipo la
política de control de aplicaciones bloquea el módulo binario de `psycopg`
(`pq.cp314-win_amd64.pyd`) y no hay `libpq.dll` instalado en el sistema. Para
desarrollo local se usa la implementación Python de `psycopg` con el `libpq`
de los binarios oficiales de PostgreSQL **16.15-5**, sin versionar ningún
binario.

> **Decisión A1 (usuaria, 2026-11-09):** se aceptan los binarios oficiales de
> EDB **sin firma Authenticode**, verificados por el SHA-256 oficial publicado
> por EDB, y se usa **PostgreSQL 16.15-5** en local. El servidor de pruebas
> sigue siendo PostgreSQL **16.15** (imagen Docker `postgres:16-alpine`); solo
> cambia el cliente `libpq` local.

1. Descargar el zip oficial y su checksum (fuera del repositorio):

   ```powershell
   $zip = "$env:LOCALAPPDATA\Temp\opencode\postgresql-16.15-5-windows-x64-binaries.zip"
   curl.exe -L --fail -o $zip "https://get.enterprisedb.com/postgresql/postgresql-16.15-5-windows-x64-binaries.zip"
   curl.exe -L --fail -o "$zip.sha256" "https://get.enterprisedb.com/postgresql/postgresql-16.15-5-windows-x64-binaries.zip.sha256"
   (Get-Item $zip).Length   # 373254386 bytes
   ```

   El checksum oficial esperado es:

   ```text
   43bb45f173a6f08cf1d29a97a6d8deb119e8e8093a24c00d2d1001a0ccaa8281  postgresql-16.15-5-windows-x64-binaries.zip
   ```

2. Verificar el SHA-256 del zip **antes de extraer**:

   ```powershell
   $official = ((Get-Content -LiteralPath "$zip.sha256") -split '\s+')[0].ToLower()
   $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $zip).Hash.ToLower()
   "official: $official"
   "actual:   $actual"
   $official -eq $actual   # debe devolver True
   ```

   Si el hash **no** coincide, detenerse: no extraer ni usar el archivo y
   reportarlo al coordinador. Verificado el 2026-11-09: coincide.

3. Extraer en una carpeta estable fuera del repositorio:

   ```powershell
   $dest = "$env:LOCALAPPDATA\opencode\postgresql-16.15-5"
   New-Item -ItemType Directory -Force -Path $dest | Out-Null
   tar.exe -xf $zip -C $dest
   ```

   El zip contiene la carpeta `pgsql\`; el resultado es
   `...\postgresql-16.15-5\pgsql\bin\...`.

4. Comprobar la versión y la firma Authenticode del `libpq.dll`:

   ```powershell
   (Get-Item "$dest\pgsql\bin\libpq.dll").VersionInfo.FileVersion   # 16.15
   Get-AuthenticodeSignature "$dest\pgsql\bin\libpq.dll" |
       Format-List Status, SignerCertificate
   ```

   **Resultado real del zip oficial de EDB 16.15-5:** `FileVersion = 16.15` y
   `Status = NotSigned`. Los DLL del ZIP de EDB **no** llevan firma Authenticode
   embebida (tampoco `postgres.exe` ni `psql.exe`). La autenticidad se establece
   por HTTPS desde el dominio oficial de EDB y por el **SHA-256 oficial
   coincidente** (`43bb45f1…ccaa8281`) y el tamaño exacto (`373254386` bytes).
   La **decisión A1 del 2026-11-09** acepta esta limitación con el hash
   verificado; no se exige firma. No se versiona ningún binario.

5. Añadir `pgsql\bin` al `PATH` y forzar la implementación Python **solo en la
   sesión** de PowerShell (no se fija en el repositorio ni en Render):

   ```powershell
   $env:PATH = "$env:LOCALAPPDATA\opencode\postgresql-16.15-5\pgsql\bin;$env:PATH"
   $env:PSYCOPG_IMPL = "python"
   python -c "import psycopg; print(psycopg.__version__)"   # 3.3.8
   python -c "import psycopg; print(psycopg.pq.__impl__, psycopg.pq.version())"   # python 160015
   ```

6. Comprobar una conexión real (sustituir el DSN por el local; no pegarlo en
   documentación ni en evidencias):

   ```powershell
   python -c "import psycopg; conn = psycopg.connect('postgresql://consultorio_dev:<password-local>@localhost:55432/consultorio_dev?sslmode=disable&connect_timeout=5'); print('SELECT 1 ->', conn.execute('SELECT 1').fetchone()[0]); print(conn.execute('SELECT version()').fetchone()[0]); conn.close()"
   ```

   Debe devolver `SELECT 1 -> 1` y `PostgreSQL 16.15 ...`.

En Render **no** se usa este procedimiento: `psycopg[binary]` incluye su propio
`libpq` y se instala con `requirements.txt`. El `PATH` y `PSYCOPG_IMPL` de esta
sección son solo para el desarrollo local en Windows.

Si la política del equipo bloquea también este `libpq`, **no** se cambia de
driver ni se instala un driver alternativo: se detiene la tarea y se reporta el
error exacto al coordinador.

## Crear el contenedor

Comando reproducible (una sola línea):

```powershell
docker run -d --name consultorio-pg-019 -e POSTGRES_DB=consultorio_dev -e POSTGRES_USER=consultorio_dev -e POSTGRES_PASSWORD=<password-local> -p 127.0.0.1:55432:5432 -v consultorio-pgdata-019:/var/lib/postgresql/data postgres:16-alpine
```

Parámetros:

| Parámetro | Valor | Motivo |
|---|---|---|
| Nombre | `consultorio-pg-019` | Aísla el contenedor de otros contenedores locales |
| Imagen | `postgres:16-alpine` | PostgreSQL 16, requisito de la Spec 019 |
| Base de datos | `consultorio_dev` | Base de desarrollo y pruebas |
| Usuario | `consultorio_dev` | Usuario de desarrollo |
| Contraseña | `<password-local>` | **Contraseña local de usar y tirar, elegida al crear el contenedor; no es un secreto del proyecto** |
| Puerto | `127.0.0.1:55432` → `5432` | Evita el 5432 habitual y solo escucha en loopback |
| Volumen | `consultorio-pgdata-019` | Conserva los datos entre reinicios del contenedor |

> **Seguridad:** la contraseña local del contenedor solo existe para desarrollo
> local. No es una credencial real, no debe reutilizarse en Neon, Render ni en
> ningún entorno compartido, y no debe publicarse fuera de este repositorio. El
> puerto se publica solo en `127.0.0.1`, no en la red local.

Si el contenedor ya existe, no vuelvas a ejecutar `docker run`: usa
`docker start consultorio-pg-019` (ver más abajo).

## Comprobar que está arriba

```powershell
docker ps --filter "name=consultorio-pg-019" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
```

Debe aparecer `consultorio-pg-019`, la imagen `postgres:16-alpine`, estado
`Up` y el puerto `127.0.0.1:55432->5432/tcp`.

Comprobar que acepta conexiones y consultar la versión:

```powershell
docker exec consultorio-pg-019 pg_isready -U consultorio_dev -d consultorio_dev
docker exec consultorio-pg-019 psql -U consultorio_dev -d consultorio_dev -c "SELECT version();"
```

`SELECT version()` debe devolver una versión **16.x** (verificado: 16.15).

## `TEST_DATABASE_URL` para la suite

La suite de paridad de la Spec 019 se ejecuta **siempre** contra PostgreSQL
(plan D9). En la sesión actual de PowerShell, define:

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"
```

Notas:

- `sslmode=disable` solo es aceptable para el PostgreSQL local en
  `localhost`/`127.0.0.1` (plan D2). En Neon/Render se exige TLS.
- `TEST_DATABASE_URL` es **obligatoria**. Según el plan aprobado (D9, CL-10),
  si falta o la base no responde, la sesión de `pytest` **falla explícitamente
  al inicio** con instrucciones para levantar este contenedor. **No se usa
  `skip`** para ocultar la ausencia de base de datos.
- Desde **T4**, los tests de esquema (`tests/test_pg_schema.py`) y el caso de
  resiliencia `TC-019-016` se ejecutan contra PostgreSQL real y exigen esta
  variable. Desde **T11**, toda la suite de paridad (Specs 004–018) usa la
  misma base y el mismo esquema aislado.
- Las pruebas usan un esquema aislado por test (`test_hu019_<uuid>`), no la base
  `consultorio_dev` directamente, pero comparten este servidor; el esquema se
  elimina con `DROP SCHEMA … CASCADE` al terminar.
- En este equipo Windows, `localhost` resuelve primero a IPv6 (`::1`) y cada
  conexión puede esperar el `connect_timeout` (≈5 s) antes de caer a IPv4. El
  contenedor publica solo `127.0.0.1:55432`, así que en local conviene usar
  `127.0.0.1` en el DSN. No es un problema de la aplicación ni afecta a Neon.

Comprobar que la variable está definida **sin imprimir la contraseña**:

```powershell
if ($env:TEST_DATABASE_URL) { "TEST_DATABASE_URL definida" } else { "TEST_DATABASE_URL NO definida" }
```

## Esquema: DDL idempotente y advisory lock

El esquema PostgreSQL se crea y evoluciona con **SQL explícito** en
`consultorio/persistence/database.py` (sin ORM, sin Alembic y sin
`executescript`; plan D4 y §3.1). `Database.ensure_schema()` aplica estos pasos
**uno a uno** dentro de una única transacción:

| Versión | Paso DDL |
|---|---|
| 1 | `CREATE TABLE IF NOT EXISTS schema_migrations` |
| 2 | `CREATE TABLE IF NOT EXISTS appointments` (`BIGSERIAL`, `TEXT`, `created_at` UTC) |
| 3 | `CREATE TABLE IF NOT EXISTS automation_events` (`event_id TEXT NOT NULL UNIQUE`) |
| 4 | `CREATE UNIQUE INDEX IF NOT EXISTS ux_appointments_slot_open ON appointments(service, date, time) WHERE status <> 'cancelled'` |

Detalles operativos:

- La transacción empieza con `SELECT pg_advisory_xact_lock(719019)`. Dos
  instancias que arranquen a la vez se serializan: la segunda espera el commit
  de la primera y ve los objetos ya creados (CL-7). El lock se libera al
  terminar la transacción; no hay locks persistentes.
- Cada paso registra su versión en `schema_migrations` con
  `INSERT … ON CONFLICT DO NOTHING`. Reaplicar el DDL no duplica filas ni
  objetos.
- Si un paso falla, se hace rollback de todo el lote: no queda un esquema a
  medias ni un marcador de migración huérfano.
- Los pasos son **aditivos**. `CREATE TABLE IF NOT EXISTS` no transforma una
  tabla preexistente con otra forma; un cambio destructivo exigirá una decisión
  documentada y su respaldo (D4), fuera de esta tarea.
- `created_at` y `applied_at` usan UTC:
  `to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')` (D7).
- El DDL SQLite de rollback sigue siendo idempotente y sus defaults
  `created_at` también se alinearon a UTC con `datetime('now')` (RF-30, D7).

### Dialecto SQL y adaptador SQLite (T5)

Los repositorios de citas y eventos (`consultorio/persistence/`) tienen **un
solo juego de sentencias** escrito en dialecto PostgreSQL (plan D8):

- marcadores `%s`, `INSERT ... RETURNING id`, `rowcount` y acceso por nombre
  (`dict_row` en PostgreSQL; `sqlite3.Row` en SQLite);
- la ruta PostgreSQL usa `Database.connection()`/`transaction()` y aplica el
  esquema de forma perezosa;
- la ruta SQLite de rollback conserva `get_connection` y ejecuta las mismas
  sentencias mediante un **adaptador mínimo y controlado** que sustituye `%s`
  por `?`. No es un traductor general: las sentencias del proyecto no contienen
  `?` dentro de literales ni `%` fuera de los marcadores.

La única expresión que difiere por motor es `sent_at` en `mark_sent()`:
PostgreSQL usa `to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')` y
SQLite `datetime('now')`, también UTC. Desde T6 los servicios y rutas usan el
objeto `Database`, y desde T11 la suite de paridad pasa ese mismo objeto; la
ruta SQLite solo se ejerce en `tests/test_rollback_sqlite.py`, en los casos de
configuración y errores del backend SQLite de `tests/test_pg_resilience.py` y
en el contrato del repositorio de
`tests/test_hu_019.py::test_sqlite_rollback_route_keeps_repository_contract`,
además del adaptador de rollback (T18 retirará la convivencia).

Para inspeccionar el resultado (sustituir `<schema>` por el esquema real):

```sql
SELECT indexdef FROM pg_indexes
 WHERE schemaname = '<schema>' AND indexname = 'ux_appointments_slot_open';

SELECT conname, pg_get_constraintdef(c.oid)
  FROM pg_constraint c
  JOIN pg_class t ON t.oid = c.conrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
 WHERE n.nspname = '<schema>' AND t.relname = 'automation_events' AND c.contype = 'u';

SELECT version, applied_at FROM "<schema>".schema_migrations ORDER BY version;
```

Salida esperada (PostgreSQL 16.15): `UNIQUE (event_id)`, el índice
`ux_appointments_slot_open` con `(service, date, "time") WHERE (status <>
'cancelled'::text)` y las versiones `1..4` en `schema_migrations`.

## Arranque sin base de datos y recuperación perezosa

- `create_app()` intenta inicializar el esquema al arrancar. Si la base no
  está disponible (`PersistenceUnavailable`), **no aborta**: registra una
  advertencia con un mensaje constante (sin DSN, credenciales ni PII) y sigue
  sirviendo las páginas que no requieren persistencia (RF-22).
- `Database.ensure_schema()` es perezoso: usa `threading.Lock` y un flag. El
  flag solo se marca como listo tras un commit correcto; si falla, el
  siguiente intento **reintenta** sin reiniciar el proceso ni un bucle en
  segundo plano (RF-23). Desde T5, los repositorios llaman a `ensure_schema()`
  cuando reciben un `Database`/`DatabaseTarget`; las rutas web lo harán al
  pasar al nuevo objeto de persistencia en T6.
- Mientras dure la convivencia transitoria, la aplicación sigue inicializando
  el esquema SQLite de rollback con `init_db(DATABASE_PATH)`; las rutas y
  servicios ya operan con el objeto `Database`. La retirada de esta llamada
  pertenece a T18.

## Indisponibilidad de la base de datos (503)

Cuando la base no responde, la frontera de persistencia traduce el error del
driver a `PersistenceUnavailable` y un único handler en
`consultorio/errors.py` responde **503** con el literal contractual
`MSG_PERSISTENCE_UNAVAILABLE`:

```text
No pudimos completar tu solicitud en este momento. Inténtalo de nuevo en unos minutos.
```

| Superficie | Respuesta |
|---|---|
| Peticiones HTML (`/citas`, confirmación, cancelación 017, admin 018) | `templates/errors/persistence_unavailable.html` con el literal y un enlace «Volver» a `/citas` |
| `GET /citas/horarios` y `GET /citas/disponibilidad` | JSON `{"error": MSG_PERSISTENCE_UNAVAILABLE}` con 503 |
| `availability.js` | Limpia las horas, muestra el literal servido por el backend y **no** pinta badges «Ocupado» ni estados de día engañosos |

El handler decide HTML/JSON por el `endpoint` de la petición
(`appointments.horarios` y `appointments.disponibilidad`), no por la cabecera
`Accept`. El log es un mensaje constante: **nunca** incluye DSN, contraseña ni
datos del paciente (RNF-6). El fallo no se presenta como horario ocupado, cita
inexistente ni cita cancelada (RF-21).

Para reproducirlo en local, apunta `DATABASE_URL` a un puerto sin servidor
(DSN ficticio, sin credenciales reales) y arranca la app sin *reloader*:

```powershell
$env:PERSISTENCE_BACKEND = "postgres"
$env:DATABASE_URL = "postgresql://consultorio_dev:local-placeholder@127.0.0.1:1/consultorio_dev?sslmode=disable"
$env:DATABASE_CONNECT_TIMEOUT = "1"
python -m flask --app app run --host 127.0.0.1 --port 5001 --no-reload
```

```powershell
curl.exe -i http://127.0.0.1:5001/citas
curl.exe -i "http://127.0.0.1:5001/citas/horarios?service=nutrition&date=2026-11-11"
curl.exe -i "http://127.0.0.1:5001/citas/disponibilidad?service=nutrition&month=2026-11"
```

Las tres peticiones responden 503 con el literal (las dos últimas en JSON). La
evidencia de T9, con la captura de la pantalla, está en
`docs/evidencias/hu-019/t9-unavailable.md`.

## Ejecutar y aislar los tests de esquema

```powershell
# Solo T4 (requiere PostgreSQL real)
python -m pytest -v tests/test_pg_schema.py `
  "tests/test_pg_resilience.py::test_tc_019_016_startup_tolerates_outage_and_recovers"

# Suite completa de la rama
python -m pytest -q
```

- `TEST_DATABASE_URL` es obligatoria. Sin ella, los tests de esquema **fallan**
  con un mensaje claro; no se usa `skip` ni `xfail` (D9/CL-10).
- `tests/conftest.py` expone las fixtures `pg_schema` (crea un esquema
  `test_hu019_<uuid>` y lo elimina con `DROP SCHEMA … CASCADE`) y `pg_target`
  (`DatabaseTarget` con `schema=<temporal>`). `Database` aplica ese
  `search_path` por conexión, así que los tests nunca escriben en `public`.
- Los helpers de test siempre pasan `connect_timeout`. En este entorno, una
  conexión sin `connect_timeout` puede bloquearse indefinidamente.
- La evidencia de T4 (catálogos reales, concurrencia y suite) está en
  `docs/evidencias/hu-019/schema.md`.

## Parar, reiniciar y eliminar

```powershell
# Parar sin borrar el contenedor ni el volumen
docker stop consultorio-pg-019

# Volver a arrancarlo
docker start consultorio-pg-019

# Reiniciarlo
docker restart consultorio-pg-019

# Ver logs si no arranca
docker logs consultorio-pg-019 --tail 50

# Eliminar el contenedor (conserva el volumen y sus datos)
docker rm -f consultorio-pg-019

# Eliminar también el volumen y, con él, los datos locales de desarrollo
docker volume rm consultorio-pgdata-019
```

Todos los comandos identifican el contenedor y el volumen por nombre, así que
**no afectan a otros contenedores ni volúmenes** del equipo. La eliminación del
volumen es irreversible: no úsala si necesitas conservar datos locales.

Si el puerto 55432 está ocupado, identifica el proceso antes de cambiar el
puerto del comando:

```powershell
Get-NetTCPConnection -LocalPort 55432 -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, State, OwningProcess
```

## Base gestionada (Neon)

Neon Free se reserva para la verificación E2E desde un entorno controlado
(T13) y para el despliegue en Render (T14). No se usa en el desarrollo diario:
el contenedor local de este documento cubre desarrollo y suite.

Nunca guardes el DSN de Neon, su contraseña ni credenciales de Render en el
repositorio, en la documentación, en las pruebas o en las evidencias. La
variable `DATABASE_URL` de producción se configura como secreto en Render
(`sync: false`).

### Endpoints y TLS

Neon ofrece dos hosts para el mismo proyecto y base:

| Endpoint | Host | Uso comprobado en T13 |
|---|---|---|
| Pooler | `<host>-pooler.<region>.aws.neon.tech` | Conexiones simples de verificación; **no** válido con la configuración actual de la app (ver más abajo) |
| Directo | `<host>.<region>.aws.neon.tech` (sin `-pooler`) | Arranque real, `ensure_schema()`, reserva y cold start |

- Ambos endpoints exigen TLS: `sslmode=require` (no se usa
  `sslmode=disable` fuera de `localhost`/`127.0.0.1`).
- En T13 se comprobó `pgconn.ssl_in_use=True` y `sslmode=require` efectivo en
  ambos. El DSN debe contener `sslmode` **una sola vez**; el proyecto valida la
  primera aparición. No introduzcas un segundo `sslmode` con otro valor.
- `channel_binding=require` es compatible con la conexión observada.
- Región verificada en T13: `us-east-2` (Ohio). Debe coincidir con la región de
  Render en T14 (RNF-3).

### Arranque y creación del esquema

Con `PERSISTENCE_BACKEND=postgres` y `DATABASE_URL` apuntando a Neon, la
aplicación ejecuta `ensure_schema()` en el arranque y aplica el mismo DDL
idempotente de la sección anterior. En T13 se partió de `public` vacío y el
esquema lo creó la app real, sin DDL manual:

- tablas `appointments`, `automation_events`, `schema_migrations`;
- índice parcial `ux_appointments_slot_open`;
- `UNIQUE(event_id)` en `automation_events`;
- migraciones 1..4 y defaults UTC.

La evidencia completa está en
`docs/evidencias/hu-019/e2e-neon.md`.

### Limitación conocida: pooler y `statement_timeout`

La app envía el timeout como parámetro de arranque de la conexión:

```text
options = "-c statement_timeout=15000"
```

El **pooler** de Neon rechaza ese parámetro:

```text
ERROR: unsupported startup parameter in options: statement_timeout.
Please use unpooled connection or remove this parameter from the startup package.
```

Consecuencias:

- `ensure_schema()` a través del pooler falla con `PersistenceUnavailable`
  (causa subyacente: `psycopg.OperationalError`) antes de ejecutar el DDL.
- El **endpoint directo** acepta el mismo `options` y funciona.
- Una conexión simple al pooler **sin** `options` funciona; por eso las
  consultas independientes y la limpieza de T13 pudieron usar el pooler.

**Decisión 2026-11-12:** para la aplicación y para Render se usa el
**endpoint directo** de Neon (host sin `-pooler`), que acepta el mismo
`options` y conserva TLS. No desactives TLS para evitar el problema. La
alternativa técnica —fijar `statement_timeout` con un `SET` después de
conectar— queda descartada salvo que Render no alcance el endpoint directo;
en ese caso requiere una tarea y una decisión documentada.

### Cold start

En T13 se dejó de consultar la base durante **360 s**. Neon detuvo y reinició el
compute (`pg_postmaster_start_time()` cambió) y la primera consulta de
disponibilidad respondió 200 en ~1,5 s; una reserva posterior terminó con
normalidad. No hay que confundir este cold start de la base con el spin-down del
servicio web de Render (T14).

### Despliegue en Render (T14)

> Trazabilidad: RF-1, RF-2, RF-3, RF-15; RNF-1, RNF-3, RNF-6, RNF-7 → plan
> D11 → `tasks.md` T14 → evidencia
> `docs/evidencias/hu-019/render-deploy.md`.

Esta sección describe la **recreación del servicio web** en Render con Neon. Las
acciones del panel las ejecuta la usuaria; el repositorio solo aporta
`render.yaml` y este procedimiento. Aquí no se guardan DSN, contraseñas ni
tokens.

#### Requisitos previos

- Proyecto/base de Neon Free en `aws-us-east-2` (**Ohio**), PostgreSQL 18
  (verificado en T13) y el **endpoint directo** (host sin `-pooler`).
- La rama que sincroniza el Blueprint contiene el `render.yaml` actualizado:
  `region: ohio`, `PERSISTENCE_BACKEND=postgres`, `DATABASE_URL` con
  `sync: false` y sin `DATABASE_PATH`. Si el cambio está solo en una rama
  `feature/*`, primero debe llegar a la rama del Blueprint; ese push lo
  coordina el responsable del repositorio.
- El DSN de Neon **no** se pega en el repositorio, la documentación, el chat ni
  la evidencia.

#### Paso 1 — Borrar el servicio actual

`region` no se puede modificar después de crear un servicio. En
<https://dashboard.render.com>:

> **Antes de borrar:** revisar **Environment** y anotar, sin copiar valores a
> documentos, las variables configuradas manualmente que no estén en
> `render.yaml` (por ejemplo `AUTOMATION_WEBHOOK_URL`,
> `AUTOMATION_WEBHOOK_AUTH_HEADER` y `CONSULTORIO_ADMIN_TOKEN`). Al recrear el
> servicio hay que volver a introducirlas en el panel si se necesitan; sus
> valores son secretos y no se versionan.

1. Abrir el Blueprint `exs-db6f05gn74is73aq3070` (o el Blueprint vinculado al
   repositorio).
2. Entrar en el servicio `consultorio-psicologico`.
3. En **Settings**, borrar el servicio web (**Delete Web Service**).

Borrar el servicio no borra el repositorio ni el Blueprint. La URL pública deja
de responder hasta terminar el paso 2 y **puede cambiar**: anotar la que asigne
Render.

#### Paso 2 — Sincronizar el Blueprint

1. En el Blueprint, ejecutar **Manual Sync** (o **Sync**).
2. Revisar el diff que muestra Render: debe incluir `region: ohio`,
   `PERSISTENCE_BACKEND=postgres`, `DATABASE_URL` y la desaparición de
   `DATABASE_PATH`.
3. Cuando Render pida el valor de `DATABASE_URL` (`sync: false`), introducir el
   DSN del **endpoint directo** de Neon. Forma, sin valores reales:

   ```text
   postgresql://<usuario>:<contraseña>@<host>.us-east-2.aws.neon.tech/<base>?sslmode=require
   ```

   - El host **no** lleva `-pooler`.
   - `sslmode=require` debe aparecer **una sola vez**; no añadir un segundo
     `sslmode` con otro valor.
   - No pegar el DSN en ningún otro campo, documento ni conversación.
4. Aplicar el Blueprint (**Apply**).

#### Paso 3 — Comprobar región y variables

En el servicio recién creado:

- **Settings → Region**: `Ohio (us-east-2)`.
- **Environment**:
  - `PYTHON_VERSION` = `3.12.7`
  - `PERSISTENCE_BACKEND` = `postgres`
  - `DATABASE_URL` presente, con valor oculto (secreto)
  - `SECRET_KEY` presente (generada por Render)
  - **no** debe existir `DATABASE_PATH`
- **Logs** del build: `Python 3.12.7` y la instalación de
  `psycopg[binary]==3.3.8` sin errores (RNF-3; riesgo R-01 del plan).

#### Paso 4 — Verificar el arranque

- Esperar a que el deploy termine en **Live**.
- Abrir `/` y comprobar que responde 200.
- Abrir `/citas` y comprobar que responde 200 (no 503).
- En los logs no debe aparecer el aviso de persistencia no disponible ni un
  DSN.

#### Paso 5 — Verificar el esquema en Neon

En el **SQL Editor** del proyecto de Neon (no desde la app), comprobar:

```sql
SELECT version, applied_at FROM schema_migrations ORDER BY version;
SELECT indexname FROM pg_indexes
 WHERE schemaname = 'public' AND indexname = 'ux_appointments_slot_open';
SELECT conname FROM pg_constraint c
  JOIN pg_class t ON t.oid = c.conrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
 WHERE n.nspname = 'public' AND t.relname = 'automation_events'
   AND c.contype = 'u';
```

Resultado esperado: versiones `1..4`, el índice `ux_appointments_slot_open` y la
restricción `UNIQUE (event_id)`.

#### Paso 6 — Reserva completa

En la web desplegada, en `/citas`:

1. Elegir servicio, fecha y hora.
2. Enviar el formulario con datos **ficticios** (por ejemplo
   `Paciente Prueba Render`, documento `900000002`,
   `render.e2e@example.invalid`, teléfono `3000000001`).
3. Comprobar la redirección 303 a `/citas/confirmada/<id>` y la página de
   confirmación con «Confirmada».
4. Comprobar que el horario aparece como ocupado en `/citas/horarios`.
5. En Neon, verificar la cita y sus eventos:

   ```sql
   SELECT id, service, date, time, status, created_at
     FROM appointments ORDER BY id DESC LIMIT 5;
   SELECT event_id, event_type, status, detail
     FROM automation_events ORDER BY id DESC LIMIT 10;
   ```

Cada cita debe tener dos eventos (`appointment.confirmed` y
`appointment.confirmation_email`). El estado depende de la configuración de
automatización (sin webhook: `skipped`); lo importante es que queden
persistidos.

#### Paso 7 — Persistencia tras redespliegue

1. En Render, **Manual Deploy → Deploy latest commit** (o **Clear build cache &
   deploy**).
2. Esperar a **Live**.
3. Abrir `/citas/confirmada/<id>` y comprobar que la cita sigue existiendo.
4. Repetir las consultas del paso 6: la cita y sus eventos deben seguir ahí.

Antes de la migración, un redeploy vaciaba la base SQLite efímera; con
PostgreSQL la cita debe sobrevivir (RF-2).

#### Paso 8 — Persistencia tras spin-down

El plan Free suspende el servicio web tras ~15 minutos sin tráfico (esto es
distinto del cold start de Neon ya verificado en T13).

1. Dejar de enviar tráfico y esperar a que el servicio muestre el estado de
   suspendido (≥ 15 min).
2. Hacer una petición a `/` (puede tardar ~1 min en despertar).
3. Abrir `/citas/confirmada/<id>` y comprobar que la cita sigue existiendo y que
   la primera petición termina con éxito.
4. Verificar de nuevo cita y eventos en Neon.

#### Paso 9 — Limpieza (opcional)

Si la cita de prueba no se conserva como evidencia, borrar solo las filas
ficticias identificadas por su `id`:

```sql
DELETE FROM automation_events WHERE appointment_id IN (<ids>);
DELETE FROM appointments WHERE id IN (<ids>);
```

No borrar tablas ni el esquema: `schema_migrations` y el DDL deben permanecer.

> **Advertencia — pooler:** si `DATABASE_URL` usa el host con `-pooler`,
> `ensure_schema()` falla con `unsupported startup parameter in options:
> statement_timeout` y la app responde 503 sin crear el esquema (T13). Usar
> siempre el endpoint directo. **No** desactivar TLS ni usar
> `sslmode=disable` fuera de `localhost`/`127.0.0.1`.

> **Rotación de credenciales:** si hay que rotar la contraseña de Neon, se hace
> en el panel de Neon (rol de la base) y se actualiza `DATABASE_URL` en Render;
> después se redespliega. El valor nuevo no se registra en el repositorio ni en
> la evidencia.

## Rollback temporal a SQLite

> Trazabilidad: Spec 019 (RF-18, RF-19; RNF-7; CL-6) → `plan.md` D10 y riesgos
> R-07/R-14 → `tasks.md` T15 → este documento y
> `docs/evidencias/hu-019/rollback.md`.
> Verificación automatizada: `tests/test_rollback_sqlite.py` (TC-010-014 y
> TC-019-021).

Esta es una **vía de repliegue temporal**, no una arquitectura permanente ni un
modo de desarrollo o de pruebas. Sirve para volver al almacenamiento anterior
mientras se investiga un problema de la migración. Tras la aceptación de la
migración, **T18 retira** el interruptor, la ruta SQLite, el DDL SQLite y esta
documentación de rollback (RF-18, R-14).

El rollback **no es evidencia de paridad**: la suite de paridad se ejecuta
siempre contra PostgreSQL (RF-28); `tests/test_rollback_sqlite.py` verifica solo
la ruta de repliegue y su resultado se registra aparte.

### Pérdida de datos aceptada

No existe migración automática de datos en ninguna dirección (RF-19):

- las filas creadas en **PostgreSQL después del corte no se trasladan** al
  almacenamiento anterior y no son visibles durante el rollback; se pierden;
- las filas creadas en **SQLite durante el rollback no se trasladan** a
  PostgreSQL al volver;
- la pérdida de las filas posteriores al corte está **aceptada por la usuaria**
  (decisión de aprobación 6 de la Spec 019; CL-6).

Por eso, antes de un rollback con datos reales se exige un **snapshot manual en
Neon** y registrar la **hora de corte en UTC**. El snapshot permite restaurar el
estado de PostgreSQL en el momento del corte; no es un sistema de backups
automático ni recupera datos creados después del corte (RNF-7).

### Procedimiento

#### Paso 1 - Snapshot manual en Neon y hora de corte

Se ejecuta **antes** de cambiar el interruptor. En el panel de Neon:

1. Identificar el proyecto, la rama y la base que usa el servicio de Render
   (endpoint directo de `DATABASE_URL`; no se copia el DSN a la documentación).
2. Crear un **snapshot/rama de respaldo** de esa rama en el estado actual
   (en Neon, una rama de restauración desde el punto actual). Ponerle un nombre
   inequívoco, por ejemplo `rollback-<YYYYMMDD-HHMM>`.
3. Registrar en el parte de incidencia, sin secretos:
   - fecha y **hora de corte en UTC** (formato `YYYY-MM-DD HH:MM:SSZ`);
   - nombre e identificador del snapshot/rama creada;
   - rama y base de origen;
   - commit desplegado en Render en ese momento;
   - persona que ejecuta el rollback y motivo.
4. Comprobar que el snapshot/rama existe antes de continuar. Si no se puede
   crear, **no** se ejecuta el rollback con datos reales.

#### Paso 2 - Activar el interruptor SQLite

En Render, servicio `consultorio-psicologico`, **Environment**:

| Variable | Valor para el rollback |
|---|---|
| `PERSISTENCE_BACKEND` | `sqlite` |
| `DATABASE_PATH` | Ruta absoluta del fichero SQLite dentro del servicio, por ejemplo `/opt/render/project/src/data/consultorio-rollback.db` |
| `DATABASE_URL` | Se conserva intacta (secreta) para la vuelta a PostgreSQL; mientras el backend es `sqlite` no se usa |

No se cambia ningún fichero de código: la aplicación elige el almacenamiento por
configuración (`DatabaseTarget.from_config`). `DATABASE_PATH` debe ser una ruta
absoluta o relativa al directorio de trabajo del proceso; el directorio debe
existir o ser creable.

> **Aviso de disco efímero:** en el plan Free de Render el sistema de ficheros
> del servicio es efímero. El fichero SQLite del rollback se pierde en un
> redespliegue, reinicio o spin-down y no debe considerarse almacenamiento
> duradero. El rollback es una medida de contingencia de corta duración.

#### Paso 3 - Reiniciar o redesplegar

Guardar las variables y ejecutar **Manual Deploy → Deploy latest commit** (o
reiniciar el servicio). El cambio de `PERSISTENCE_BACKEND` exige reinicio: el
valor se lee al arrancar el proceso.

Comprobar en **Logs** que el arranque termina en **Live** y que no aparece el
aviso de persistencia no disponible.

#### Paso 4 - Verificar el rollback

1. Abrir `/` y `/citas`; deben responder 200 (no 503).
2. Comprobar en la interfaz que las citas visibles son las del almacenamiento
   SQLite. Las citas que solo existían en PostgreSQL **no** aparecerán: es el
   comportamiento aprobado (RF-19).
3. Si se necesita una cita de prueba, crearla con datos ficticios y comprobar
   que se persiste en el SQLite del servicio.

#### Paso 5 - Volver a PostgreSQL

1. Cambiar `PERSISTENCE_BACKEND` a `postgres` (mantener el `DATABASE_URL`
   secreto del endpoint directo de Neon).
2. Redesplegar y esperar a **Live**.
3. Comprobar `/citas` y que las filas de PostgreSQL anteriores al corte siguen
   ahí. Las filas creadas en SQLite durante el rollback **no** se trasladan y no
   aparecerán: la pérdida está aceptada (CL-6).
4. El snapshot del paso 1 permite volver al estado de PostgreSQL en el momento
   del corte si la vuelta falla; no contiene las filas creadas después del
   corte. Si hay que conservar filas creadas durante el rollback, exportarlas
   manualmente del fichero SQLite antes de retirarlo; no se trasladan de forma
   automática.
5. Registrar en el parte la hora de vuelta a PostgreSQL y el resultado.

### Verificación automatizada del rollback

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m pytest -q tests/test_rollback_sqlite.py
```

- `TC-019-021` crea una cita en PostgreSQL (esquema aislado), cambia el
  interruptor a SQLite con un `DATABASE_PATH` temporal, comprueba que la cita de
  PostgreSQL no es visible, crea una cita SQLite, vuelve a PostgreSQL y verifica
  que la fila SQLite no se trasladó y que la cita original sigue intacta.
  También arranca la app con la configuración SQLite y `DATABASE_URL` vacía.
- `TC-010-014` conserva la cobertura de respaldo, idempotencia y aborto ante
  duplicados de la migración del esquema SQLite legado.
- Ambos se registran en `docs/evidencias/hu-019/rollback.md` **aparte** de la
  suite de paridad (RF-28).

## Incidencias habituales

- **`docker info` falla con `npipe:////./pipe/dockerDesktopLinuxEngine`**:
  Docker Desktop no está arrancado. Inícialo con
  `Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"` y espera
  a que `docker info` responda.
- **El contenedor no pasa de `starting`**: revisa `docker logs
  consultorio-pg-019 --tail 50`. Si el volumen quedó de una versión anterior
  incompatible, solo para datos locales de usar y tirar, elimina contenedor y
  volumen y repite el `docker run`.
- **La imagen no está descargada**: el `docker run` la descarga de
  `postgres:16-alpine` automáticamente; requiere conexión a Internet.
- **Una conexión se queda bloqueada sin error**: en este entorno, omitir
  `connect_timeout` puede colgar la conexión. La aplicación y los tests siempre
  lo pasan; si escribes un script manual, inclúyelo.

## Referencias

- Plan D2 (configuración por entorno y TLS), D4 (DDL idempotente y advisory
  lock), D5 (transacciones), D6 (errores), D7 (UTC), D9 (suite siempre
  PostgreSQL), D14 (arranque tolerante y reintento perezoso), D15
  (documentación operativa) y §3.1/§6.1.
- Evidencia real de T1: `docs/evidencias/hu-019/setup-local.md`.
- Evidencia real de T3: `docs/evidencias/hu-019/t3-connection-layer.md`.
- Evidencia real de T4: `docs/evidencias/hu-019/schema.md`.
- Evidencia real de T6: `docs/evidencias/hu-019/t6-services.md`.
- Evidencia real de T7: `docs/evidencias/hu-019/t7-atomicity.md`.
- Evidencia real de T8: `docs/evidencias/hu-019/t8-literal.md`.
- Evidencia real de T9: `docs/evidencias/hu-019/t9-unavailable.md`.
- Evidencia real de T13 (Neon): `docs/evidencias/hu-019/e2e-neon.md`.
- Evidencia de T14 (Render): `docs/evidencias/hu-019/render-deploy.md`
  (preliminar; despliegue, reserva, redespliegue y spin-down pendientes).
