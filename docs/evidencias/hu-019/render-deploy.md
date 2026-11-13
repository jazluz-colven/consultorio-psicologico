# Despliegue en Render — Spec 019 / T14

> **Trazabilidad:** `specs/019_migrar-postgresql/spec.md` (RF-1, RF-2, RF-3,
> RF-15; RNF-1, RNF-3, RNF-6, RNF-7) → `plan.md` D11 (decisión 2026-11-12:
> endpoint directo de Neon) → `tasks.md` T14 → este documento.
>
> **Ejecución:** 2026-11-12 (UTC). **Rama:** `feature/hu-019-migracion-postgres`.
> **HEAD:** `dde4461`, publicado en `main` (`9846613..dde4461`).
>
> **Estado: EJECUTADO — PENDIENTE DE REVISIÓN TÉCNICA.** Todos los criterios de
> aceptación de T14 se ejecutaron contra el servicio real de Render y Neon. El
> veredicto final corresponde a `@revisor`.

## 1. Resultado del despliegue

| Elemento | Valor real |
|---|---|
| Servicio | `consultorio-psicologico` (`srv-dbr08jk9v7es73agc110`) |
| URL pública | `https://consultorio-psicologico-z1o5.onrender.com` |
| Región | **ohio** (`aws-us-east-2`, misma que Neon Free) |
| Plan | **free** |
| Runtime | Python **3.12.7** |
| Backend | `PERSISTENCE_BACKEND=postgres` |
| Blueprint | `exs-db6f05gn74is73aq3070`, estado `in_sync`, `lastSync` 2026-11-12T18:25:15Z |
| Creado | 2026-11-12T18:24:14Z |
| Servicio anterior | `srv-db6f4v0473hc73e9ovg0` (oregón, suspendido), **eliminado**; su URL `c6g6` responde 404 |

La recreación fue necesaria porque Render no permite cambiar la región de un
servicio existente (`services[0].region changing region not supported`). El
Blueprint creó el servicio nuevo en Ohio sin recursos de pago.

## 2. Configuración verificada por API de Render

| Variable | Estado |
|---|---|
| `PYTHON_VERSION` | `3.12.7` |
| `PERSISTENCE_BACKEND` | `postgres` |
| `DATABASE_URL` | Secreto presente (138 caracteres), endpoint **directo** de Neon, `sslmode=require`. Valor **no registrado** en este documento. |
| `SECRET_KEY` | Generada por Render (44 caracteres), valor no registrado |
| `DATABASE_PATH` | **No existe** |
| `AUTOMATION_WEBHOOK_URL` / `AUTOMATION_WEBHOOK_AUTH_HEADER` | **No configuradas** tras la recreación (ver §8) |
| `CONSULTORIO_ADMIN_TOKEN` | **No configurada** tras la recreación (ver §8) |

```text
env-var keys: PERSISTENCE_BACKEND, SECRET_KEY, PYTHON_VERSION, DATABASE_URL
```

La API key de Render se usó solo desde el entorno local de la usuaria; no está
en el repositorio ni en esta evidencia.

## 3. Build y runtime

Logs de build reales (dos despliegues):

```text
==> Using Python version 3.12.7 via environment variable PYTHON_VERSION
==> Installing Python version 3.12.7...
Collecting psycopg==3.3.8 (from psycopg[binary]==3.3.8->-r requirements.txt)
  Using cached psycopg_binary-3.3.8-cp312-cp312-manylinux2014_x86_64...whl
Successfully installed Flask-3.1.3 ... psycopg-3.3.8 psycopg-binary-3.3.8 ...
```

- `psycopg[binary]==3.3.8` instala correctamente en Python 3.12.7 (riesgo R-01
  descartado).
- En los 100 registros de log de aplicación más recientes no aparecieron
  `Traceback`, `ERROR`, `Exception`, `statement_timeout` ni cadenas de DSN.

## 4. Despliegues

| Deploy | Commit | Creado (UTC) | Live (UTC) | Resultado |
|---|---|---|---|---|
| `dep-dbr08js9v7es73agc1i0` | `dde4461` | 18:24:15 | 18:24:54 | Live (sin secreto aún) |
| `dep-dbr0a2e7bikc73c2q0dg` | `dde4461` | 18:27:22 | 18:27:59 | Live con `DATABASE_URL` directa |
| `dep-dbr0aumc6qcc73dieh20` | `dde4461` | 18:29:14 | 18:30:07 | Live (redespliegue de verificación) |

## 5. Arranque y esquema en Neon

Con el servicio Live y el secreto configurado:

| Comprobación | Resultado |
|---|---|
| `GET /` | **200** |
| `GET /citas` | **200** |
| `schema_migrations` | versiones **1, 2, 3, 4** |
| Índice parcial | `ux_appointments_slot_open` con `WHERE (status <> 'cancelled'::text)` sobre `(service, date, "time")` |
| Unicidad de eventos | `automation_events_event_id_key` `UNIQUE (event_id)` |
| Claves primarias | `appointments_pkey`, `automation_events_pkey` |
| Error de conexión/DSN en logs | No observado |

El esquema ya existía desde T13 (`schema_migrations.applied_at` =
2026-11-12T13:16:02Z, anterior a la creación del servicio a las 18:24:14Z).
T14 verificó su **presencia e idempotencia** en el servicio desplegado; la
creación inicial desde una base vacía corresponde a T13 y no se atribuye a T14.

## 6. Reserva completa contra el servicio desplegado

Petición real a la URL pública (datos ficticios, sin PII real):

```text
GET /citas/horarios?service=nutrition&date=2026-11-17  -> 200
  available: 08:00 ... 16:30; occupied: []
POST /citas (nutrition, 2026-11-17, 10:00, paciente ficticio) -> 303
  Location: /citas/confirmada/3
GET /citas/confirmada/3 -> 200
  contiene «Confirmada», el nombre ficticio, la fecha y la hora
GET /citas/horarios?... -> 200
  occupied: ["10:00"]
```

Filas en Neon inmediatamente después de la reserva:

```text
appointments: (3, 'nutrition', '2026-11-17', '10:00', 'confirmed')
events:
  appointment.confirmation_email:3:v1 | appointment.confirmation_email | skipped
  appointment.confirmed:3:v1          | appointment.confirmed          | skipped
```

Los dos eventos quedan `skipped` porque `AUTOMATION_WEBHOOK_URL` está vacía
(comportamiento definido en HU-007). No se declara envío de correo.

## 7. Persistencia tras redespliegue y spin-down

### 7.1 Redespliegue

- Deploy `dep-dbr0aumc6qcc73dieh20`: 18:29:14Z → 18:30:07Z (**Live**).
- Tras el redespliegue, en Neon siguen la cita `id=3` y sus dos eventos.
- `GET /citas/confirmada/3` → **200**; `/citas/horarios` sigue con
  `occupied: ["10:00"]`.

### 7.2 Spin-down del servicio web

- Último tráfico: **2026-11-12T18:31:00Z**.
- Primera petición tras 17 min sin tráfico: **2026-11-12T18:48:00Z**.
- Resultado: **HTTP 200** en **32,7 s** (arranque del servicio web; no se mide
  aquí el cold start de Neon, ya cubierto en T13).
- Tras el arranque, la cita `id=3` y sus dos eventos siguen en Neon;
  `/citas/confirmada/3` → 200 y el horario `10:00` sigue ocupado.

### 7.3 Limpieza

Tras las comprobaciones se eliminaron los datos ficticios:

```text
deleted_events = 2
deleted_appointments = 1
appointments = 0, automation_events = 0, schema_migrations = 4
```

## 8. Hallazgos y pendientes operativos

1. **Servicio n8n eliminado por la usuaria.** La automatización de HU-007/008
   no está operativa: por eso los eventos quedan `skipped`. La usuaria asume la
   restauración de n8n; queda **fuera del alcance de T14/Spec 019**.
2. **Variables manuales no reintroducidas:** `AUTOMATION_WEBHOOK_URL`,
   `AUTOMATION_WEBHOOK_AUTH_HEADER` y `CONSULTORIO_ADMIN_TOKEN`. Se
   reintroducirán cuando n8n esté restaurado y la usuaria lo indique. No se
   registran valores.
3. **URL pública nueva:** `https://consultorio-psicologico-z1o5.onrender.com`;
   la anterior (`c6g6`) devuelve 404.
4. **API key de Render:** usada solo durante esta verificación; debe revocarse
   en el panel al cerrar T14.
5. **Artefacto bruto del spin-down:** la evidencia registra horas y latencia;
   para T17 conviene adjuntar un extracto fechado de la primera petición tras
   el spin-down. No afecta al veredicto de T14.

## 9. Coste y secretos

| Comprobación | Resultado |
|---|---|
| Recursos de pago | **Ninguno**: único servicio web, `plan: free`; sin bases, cron jobs ni workers |
| Facturación | **No verificada por API** (limitación): solo se inspeccionó el inventario de planes y recursos |
| DSN/contraseña en repositorio o evidencia | **No** |
| Tokens/API keys en repositorio | **No** |
| PII real en la reserva de prueba | **No** (datos ficticios, eliminados) |

## 10. Suite local (sin cambios en esta parte)

No se modificó código de producción durante la verificación. Se mantiene el
resultado de la suite local con PostgreSQL en Docker:

```text
398 passed in 175.88s (0:02:55)
```

## 11. Riesgos y estado

| # | Riesgo | Estado |
|---|---|---|
| 1 | Región inmutable | **Resuelto**: servicio recreado en Ohio desde el Blueprint |
| 2 | Sync bloqueado por servicio anterior | **Resuelto**: servicio de Oregón eliminado; Blueprint `in_sync` |
| 3 | Pooler rechaza `statement_timeout` | **Mitigado**: endpoint directo (D11) |
| 4 | URL pública cambia al recrear | **Asumido**: URL nueva documentada |
| 5 | n8n eliminado y variables de automatización ausentes | **Abierto**, fuera de T14; lo asume la usuaria |
| 6 | `CONSULTORIO_ADMIN_TOKEN` ausente | **Abierto**: reintroducir si se necesita la superficie admin |

**Criterio de cierre de T14:** los **ocho criterios de aceptación** de T14 en
`tasks.md` están ejecutados y registrados con resultados reales. `@revisor`
emitió veredicto **APROBADO**; queda pendiente la autorización de commit de la
usuaria.
