# E2E Neon — Spec 019 / T13

> **Trazabilidad:** `specs/019_migrar-postgresql/spec.md` (RF-1; RNF-2,
> RNF-4) → `plan.md` (D2, D3, D14; §6.2, §7.1, §11) → `tasks.md` T13 →
> este documento.
>
> **Fecha:** 2026-11-12. **Rama:** `feature/hu-019-migracion-postgres`.
> **HEAD:** `d1e7909` (T12). **Sin commit ni push de T13.**
>
> **Resultado global:** PASS técnico en TLS, creación de esquema desde vacío,
> reserva + eventos y cold start > 5 min. El plan Neon Free y la región se
> verificaron por API el 2026-11-12 (`subscription_type=free_v3`,
> `region_id=aws-us-east-2`). Queda como **NO VERIFICADO** únicamente
> `ensure_schema` a través del pooler con la configuración actual de la app
> (el pooler rechaza el parámetro de arranque `statement_timeout`; ver §5).
> Desde el 2026-11-12 la decisión para T14 es usar el **endpoint directo**.

## 1. Alcance y entorno

- Verificación contra la base gestionada real de Neon, **sin** desplegar el
  servicio web ni usar Render. No se hizo redespliegue ni spin-down del servicio
  web: eso pertenece a T14.
- Entorno controlado: Windows, Python **3.14.8**, `psycopg` **3.3.8**
  (implementación binaria, `libpq` 18.0.4), Flask a través de su cliente de
  pruebas.
- Servidor Neon observado: PostgreSQL **18.6 (ac70818)**.
- Región y plan verificados por API de Neon el 2026-11-12:
  **`region_id=aws-us-east-2` (Ohio)** y **`subscription_type=free_v3`**
  (proyecto `fragrant-silence-79082611`, PostgreSQL 18). El host del endpoint
  coincide con `us-east-2`.
- `DATABASE_URL` se leyó de la variable de entorno del usuario. **No se
  registra el DSN, la contraseña, el usuario ni el host completo.**
- La app se ejecutó con `PERSISTENCE_BACKEND=postgres` y
  `AUTOMATION_WEBHOOK_URL=""` (eventos en estado `skipped`, sin correo ni
  webhook reales).
- Datos de prueba ficticios: `document_type=CC`,
  `document_number=900000001`, `patient_name=Paciente Ficticio T13`,
  `email=t13.e2e@example.invalid`, `phone=3000000000`. No hay PII real.

## 2. Procedimiento ejecutado

1. Se comprobó que `DATABASE_URL` estaba definida y que el DSN contenía
   `sslmode=require` una sola vez y `channel_binding=require`.
2. Se probó TLS y conectividad por el **pooler** y por el **endpoint directo**
   (el mismo host sin `-pooler`). Ambos usaron TLS y `sslmode=require`.
3. Se dejó `public` vacío antes del arranque real para poder demostrar que el
   esquema lo crea la aplicación. El reset solo eliminó las tres tablas de la
   Spec 019 (`appointments`, `automation_events`, `schema_migrations`) y sus
   secuencias; no se tocó ningún otro esquema.
4. Se arrancó la app real con `create_app(T13Config)`; el arranque ejecutó
   `ensure_schema()`. Se verificó el DDL contra catálogos de PostgreSQL.
5. Se reaplicó `ensure_schema()` desde una segunda instancia y desde dos hilos
   concurrentes para comprobar idempotencia y compatibilidad del advisory lock.
6. Se ejecutó una reserva completa por HTTP con el cliente de pruebas de Flask:
   disponibilidad previa, `POST /citas`, redirección 303 a la confirmación,
   página de confirmación, disponibilidad posterior y consulta independiente de
   la cita y sus eventos.
7. Se cerraron las conexiones de la petición y se esperaron **360 s** sin
   actividad. La primera consulta de disponibilidad y una segunda reserva
   completa se ejecutaron después del corte.
8. Se eliminaron las dos citas y sus cuatro eventos; se verificó que `public`
   queda sin filas de prueba y que el esquema permanece para T14.

### Reproducción mínima

El harness completo se ejecutó desde un script temporal, fuera del repositorio,
para no añadir utilidades no previstas por la tarea. La secuencia esencial es
reproducible así (los valores entre `<>` se aportan por entorno y **no se
registran**):

```powershell
$env:DATABASE_URL = "<DSN pooler de Neon; no registrar>"
# Endpoint directo (decisión T14, 2026-11-12): mismo DSN cambiando
# el host <host>-pooler por <host>.
$env:T13_DIRECT_DSN = $env:DATABASE_URL.Replace("-pooler.", ".")
$env:PERSISTENCE_BACKEND = "postgres"
# El harness usa create_app(T13Config), test_client(), ensure_schema(),
# /citas/horarios, /citas/disponibilidad y POST /citas.
```

```python
# Esquema del harness (sin secretos): create_app real + cliente HTTP.
import os, tempfile
from pathlib import Path
from consultorio import create_app
from consultorio.config import Config

class T13Config(Config):
    PERSISTENCE_BACKEND = "postgres"
    DATABASE_URL = os.environ["T13_DIRECT_DSN"]  # no se imprime
    DATABASE_PATH = Path(tempfile.mkdtemp()) / "consultorio.db"
    AUTOMATION_WEBHOOK_URL = ""

app = create_app(T13Config)          # ejecuta ensure_schema()
client = app.test_client()
assert client.get("/citas/horarios?service=nutrition&date=<fecha>").status_code == 200
assert client.post("/citas", data=<formulario_ficticio>).status_code == 303
```

La comprobación independiente se hizo con una conexión `psycopg` nueva (sin
pasar el `statement_timeout` de la app), no con la conexión de la petición.

## 3. TLS y endpoint

| Comprobación | Pooler | Directo |
|---|---|---|
| `pgconn.ssl_in_use` | `True` | `True` |
| `sslmode` efectivo (`conn.pgconn.info`) | `require` | `require` |
| `sslnegotiation` efectivo | `postgres` | `postgres` |
| `SHOW server_version` | `18.6 (ac70818)` | `18.6 (ac70818)` |

- El DSN tiene **una sola** aparición de `sslmode=require`; el proyecto lee la
  primera y obtiene `require`. No se reprodujo el riesgo de `sslmode` duplicado
  de T2 en este DSN.
- `channel_binding=require` está presente y la conexión se estableció.
- **No se debilitó TLS** en ninguna prueba.

## 4. Esquema creado desde vacío por la app real

`public` se comprobó vacío antes del arranque. `create_app` tardó **1,873 s** y
creó el esquema. La segunda instancia tardó **1,704 s**; los dos hilos
concurrentes terminaron sin errores (`threads_alive=[False, False]`,
`errors=[]`).

Catálogo observado:

```text
tables=['appointments', 'automation_events', 'schema_migrations']
indexes=['appointments_pkey', 'automation_events_event_id_key',
         'automation_events_pkey', 'schema_migrations_pkey',
         'ux_appointments_slot_open']
partial_index=CREATE UNIQUE INDEX ux_appointments_slot_open
  ON public.appointments USING btree (service, date, "time")
  WHERE (status <> 'cancelled'::text)
unique_constraints=[('automation_events_event_id_key', 'UNIQUE (event_id)')]
schema_migrations=[(1, ...), (2, ...), (3, ...), (4, ...)]
```

- `appointments.id` y `automation_events.id`: `bigint` con `nextval(...)`
  (`BIGSERIAL`).
- `automation_events.appointment_id`: `integer`, según el DDL aprobado.
- `created_at` y `applied_at`: `TEXT` con
  `to_char((now() AT TIME ZONE 'UTC'), 'YYYY-MM-DD HH24:MI:SS')`.
- Columnas exactas verificadas para las tres tablas; no faltan ni sobran.
- El esquema coincide con el DDL aprobado en `schema.md`.

> El reset de `public` forma parte de la preparación de la base de prueba, no de
> la creación del esquema. La creación la hizo `create_app`/`ensure_schema()`.

## 5. Limitación crítica: pooler de Neon y `statement_timeout`

La app configura el timeout de sentencia como parámetro de arranque:

```text
options = "-c statement_timeout=15000"
```

Con ese parámetro, el **pooler** de Neon rechaza la conexión:

```text
psycopg.OperationalError: connection failed: ... ERROR: unsupported startup
parameter in options: statement_timeout. Please use unpooled connection or
remove this parameter from the startup package.
```

Consecuencias comprobadas:

- `Database.ensure_schema()` a través del pooler falla con
  `PersistenceUnavailable` (la causa subyacente es el `OperationalError`
  anterior). **No crea tablas.**
- El **endpoint directo** acepta el mismo `options="-c statement_timeout=15000"`
  y ejecuta `SELECT 1` correctamente.
- Una conexión simple al pooler **sin** ese parámetro de arranque sí funciona;
  por eso la verificación independiente y la limpieza pudieron usar el pooler.

Por tanto:

- **NO VERIFICADO:** `ensure_schema` a través del pooler con la configuración
  actual de producción. Falla antes de ejecutar el DDL.
- **VERIFICADO:** advisory lock e idempotencia en el endpoint directo, incluida
  la concurrencia de dos instancias.
- **Recomendación para T14:** usar el endpoint directo para la app mientras no
  se modifique la configuración, o cambiar el código para fijar
  `statement_timeout` después de conectar en lugar de enviarlo como parámetro de
  arranque. Ese cambio requiere decisión de spec/plan y **no se hizo en T13**.
  No se debe desactivar TLS ni usar `sslmode=disable`.

## 6. Reserva completa y eventos

- Fecha de la cita: **2026-11-19**; horarios **10:00** y **10:30**.
- `GET /citas/horarios?service=nutrition&date=2026-11-19` → 200; el slot estaba
  libre antes y **ocupado después**. Esta es la comprobación fuerte de que el
  slot queda excluido.
- `GET /citas/disponibilidad?service=nutrition&month=2026-11` → 200; el día
  seguía disponible antes y después de reservar. Es una vista mensual de días
  con hueco, por lo que **no demuestra por sí sola** la exclusión del slot
  concreto; esa evidencia es la de `/citas/horarios`.
- `POST /citas` → **303** a `/citas/confirmada/1` y `/citas/confirmada/2`.
- La página de confirmación → 200 y contiene `Confirmada` y `Cita registrada`.
- La cita y los eventos se leyeron desde una **conexión independiente** al
  pooler (conexión simple, sin el `statement_timeout` de la app):

```text
id=1 service=nutrition date=2026-11-19 time=10:00 status=confirmed
  created_at=2026-11-12 13:16:17
event_id=appointment.confirmed:1:v1 type=appointment.confirmed version=1
  status=skipped detail=Automatización no configurada. sent_at=None
event_id=appointment.confirmation_email:1:v1
  type=appointment.confirmation_email version=1 status=skipped
  detail=Envío de correo no configurado. sent_at=None
```

- Dos eventos por cita, `event_id` únicos, `event_version=1`, `status=skipped`,
  `sent_at=NULL`, `created_at` en formato UTC y reciente.
- Se repitió el flujo para `id=2` y `10:30` con el mismo resultado.

## 7. Cold start tras más de 5 minutos

- Última actividad antes del corte: **2026-11-12 13:16:22 UTC**.
- Espera real: **360 s** sin consultas.
- `pg_postmaster_start_time()` antes: **13:03:07.414841+00:00**.
- `pg_postmaster_start_time()` después: **13:22:25.059956+00:00**.
- `compute_restarted_during_idle=True`.
- Primera consulta de disponibilidad tras el corte: **HTTP 200** en **1,491 s**;
  el slot `10:30` estaba libre.
- Segunda reserva completa: **303**, confirmación 200, **2,381 s** de `POST`.
- La cita `id=2` y sus dos eventos quedaron persistidos y visibles.
- No hubo fallo por cold start: la base despertó y la operación terminó con
  éxito.

## 8. Limpieza y estado final

```text
deleted_appointment_ids=[1, 2]
public_appointments_rows=0
public_automation_events_rows=0
test_appointment_rows_left=0
public_tables=['appointments', 'automation_events', 'schema_migrations']
schema_migrations_versions=[1, 2, 3, 4]
```

- No quedan filas de prueba.
- El esquema permanece, en versiones 1..4, listo para T14.
- No se modificó ningún otro esquema ni dato ajeno a la prueba.

## 9. Suite local (PostgreSQL Docker)

La suite completa se ejecutó contra el PostgreSQL local de Docker, no contra
Neon:

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m pytest -q
```

Resultado real:

```text
397 passed in 177.70s (0:02:57)
```

- PostgreSQL local: **16.15** (`consultorio-pg-019`, `127.0.0.1:55432`).
- Sin `skip`, `xfail` ni fallos.
- La contraseña local del contenedor de pruebas se rotó en la sesión a un valor
  aleatorio no registrado porque la contraseña original no estaba disponible;
  el contenedor es de usar y tirar y no forma parte de producción.
- La suite no usó Neon: `TEST_DATABASE_URL` apunta al Docker local.

## 10. Checklist de aceptación

- [x] Proyecto/base Neon conectado desde el entorno controlado, sin Render.
- [x] TLS real comprobado por pooler y por endpoint directo
      (`ssl_in_use=True`, `sslmode=require`).
- [x] Región `us-east-2` (Ohio) y plan **Neon Free** verificados por API el
      2026-11-12 (`subscription_type=free_v3`).
- [x] Esquema creado desde vacío por `create_app`/`ensure_schema()`, sin pasos
      manuales de DDL, y coincide con `schema.md`.
- [x] `ensure_schema()` idempotente y concurrencia de dos instancias en el
      endpoint directo.
- [ ] `ensure_schema()` a través del pooler con la configuración actual.
      **NO VERIFICADO:** el pooler rechaza `statement_timeout` como parámetro de
      arranque; se usó el endpoint directo.
- [x] Reserva completa y eventos persistidos y visibles desde una conexión
      independiente.
- [x] Cold start tras 360 s: disponibilidad y segunda reserva con éxito;
      `compute_restarted_during_idle=True`.
- [x] Limpieza: 0 filas de prueba; esquema conservado.
- [x] Suite completa: **397 PASS / 0 FAIL** contra PostgreSQL Docker.
- [x] Sin DSN, contraseña ni PII real en este documento.
- [x] Procedimiento reproducible documentado.

## 11. Límites y pendientes

- **Neon Free:** verificado por API el 2026-11-12 (`subscription_type=free_v3`,
  `region_id=aws-us-east-2`); no se midieron cuotas de 1 GB / 100 CU-hours.
- **Pooler + `statement_timeout`:** limitación real de conexión con la
  configuración actual. **Decisión 2026-11-12:** T14 usará el **endpoint
  directo** (sin `-pooler`); el cooldown/alternativa de `SET` tras conectar
  queda descartado salvo que Render no alcance el endpoint directo.
- **Advisory lock vía pooler:** no verificado porque la conexión falla antes;
  sí verificado en el endpoint directo.
- **Harness del E2E:** se ejecutó desde un script temporal no versionado; las
  comprobaciones están descritas por bloques (§2 y §4–§9), pero no se conserva
  una transcripción línea a línea.
- **Render:** fuera de alcance; T14.
- **Validación visual:** no aplica; T13 no cambia frontend. La página de
  confirmación se comprobó por HTTP, no con navegador.
