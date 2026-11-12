# Despliegue en Render — Spec 019 / T14

> **Trazabilidad:** `specs/019_migrar-postgresql/spec.md` (RF-1, RF-2, RF-3,
> RF-15; RNF-1, RNF-3, RNF-6, RNF-7) → `plan.md` D11 (decisión 2026-11-12:
> endpoint directo de Neon) → `tasks.md` T14 → este documento.
>
> **Fecha:** 2026-11-12. **Rama:** `feature/hu-019-migracion-postgres`.
> **HEAD:** `6f5e132` (T13). **Sin commit ni push de T14.**
>
> **Estado global: PREPARADO — PENDIENTE DE ACCIONES EN EL PANEL DE RENDER Y
> DE DESPLIEGUE.** Este documento no declara PASS del despliegue, la reserva, el
> redespliegue ni el spin-down: esos pasos **no se han ejecutado** porque el
> implementador no tiene acceso al panel de Render. Las secciones PENDIENTE se
> completarán tras la ejecución real de la usuaria.

## 1. Alcance de esta parte

Parte local de T14, sin panel de Render ni despliegues:

- actualizar `render.yaml` para el backend PostgreSQL y la región Ohio;
- fijar el contrato del manifiesto en un test automatizado sin dependencias
  nuevas;
- documentar el procedimiento operativo que ejecutará la usuaria;
- registrar lo ya verificable y dejar explícitas las comprobaciones pendientes.

No se han tocado `consultorio/`, `templates/`, `static/` ni `app.py`. No se ha
creado ni borrado ningún servicio de Render ni se ha usado la API de Render.

## 2. Verificado en esta parte (local)

| Comprobación | Resultado | Evidencia |
|---|---|---|
| `render.yaml` declara `region: ohio` | OK | `render.yaml` y `tests/test_render_manifest.py` |
| `render.yaml` declara `plan: free` | OK | ídem |
| `PYTHON_VERSION=3.12.7` se conserva | OK | ídem |
| `PERSISTENCE_BACKEND=postgres` | OK | ídem |
| `DATABASE_URL` con `sync: false` y sin valor | OK | ídem |
| Ausencia de `DATABASE_PATH` | OK | ídem |
| Ausencia de DSN, contraseña, host de Neon o API key en el manifiesto | OK | ídem |
| `healthCheckPath: /`, `buildCommand` y `startCommand` se conservan | OK | ídem |
| Test de contrato del manifiesto | **1 PASS** | `python -m pytest -q tests/test_render_manifest.py` |
| Suite completa local con PostgreSQL en Docker | **398 PASS / 0 FAIL** | §5 |

Contexto heredado de T13 (no reejecutado en T14):

- Neon **Free** (`subscription_type=free_v3`) y región **`aws-us-east-2`
  (Ohio)**, PostgreSQL 18, verificados por API el 2026-11-12.
- Decisión 2026-11-12: la app y Render usan el **endpoint directo** de Neon
  (host sin `-pooler`), porque el pooler rechaza el parámetro de arranque
  `options=-c statement_timeout=...`.
- TLS obligatorio (`sslmode=require`); no se desactiva TLS.

## 3. Configuración esperada en Render

| Elemento | Valor esperado |
|---|---|
| Servicio | `consultorio-psicologico` (tipo web, runtime Python) |
| Región | `ohio` (coincide con `aws-us-east-2` de Neon) |
| Plan | `free` |
| `PYTHON_VERSION` | `3.12.7` |
| `PERSISTENCE_BACKEND` | `postgres` |
| `DATABASE_URL` | Secreto configurado en el panel; endpoint **directo** de Neon, `sslmode=require` |
| `SECRET_KEY` | `generateValue: true` |
| `DATABASE_PATH` | **No debe existir** |
| `buildCommand` | `pip install -r requirements.txt` |
| `startCommand` | `gunicorn app:app` |
| `healthCheckPath` | `/` |

`render.yaml` no contiene ningún valor secreto. El DSN se introduce únicamente
en el panel de Render.

## 4. Contrato del manifiesto

`tests/test_render_manifest.py` lee `render.yaml` como texto con un parser
mínimo de stdlib y comprueba de forma explícita los valores de §3. No se añade
PyYAML ni ninguna otra dependencia (RNF-8 / D1).

Resultado real de la ejecución aislada:

```text
$ python -m pytest -q tests/test_render_manifest.py
1 passed in 0.04s
```

El test falla si se reintroduce `DATABASE_PATH`, si `DATABASE_URL` lleva un
valor versionado, si cambia la región o el plan, o si aparece un DSN,
contraseña, host de Neon o API key en el manifiesto.

## 5. Suite local (PostgreSQL en Docker)

```powershell
$env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m pytest -q
```

Resultado real:

```text
398 passed in 175.88s (0:02:55)
```

- PostgreSQL local **16.15**, contenedor `consultorio-pg-019`,
  `127.0.0.1:55432`.
- Sin `skip`, `xfail` ni fallos.
- La suite no usa Neon: `TEST_DATABASE_URL` apunta al Docker local.
- Baseline previa a T14: **397 PASS**; el test del manifiesto añade **1 PASS**
  (398).

## 6. PENDIENTE — acciones en el panel y despliegue

Todo lo siguiente está **sin ejecutar** y **no se declara PASS**. El
procedimiento exacto está en
`docs/operaciones/postgresql.md`, sección «Despliegue en Render (T14)».

### 6.1 Recreación del servicio

- [ ] **PENDIENTE:** borrar el servicio actual y recrearlo desde el Blueprint
      en **Ohio** (la región no se puede cambiar en caliente).
- [ ] **PENDIENTE:** confirmar que el Blueprint sincroniza una rama con el
      `render.yaml` actualizado.
- [ ] **PENDIENTE:** introducir `DATABASE_URL` como secreto con el endpoint
      **directo** de Neon (sin `-pooler`).
- [ ] **PENDIENTE:** anotar la URL pública asignada al servicio nuevo.

### 6.2 Región, variables y runtime

- [ ] **PENDIENTE:** verificar en el panel `Region = Ohio (us-east-2)`.
- [ ] **PENDIENTE:** verificar `PYTHON_VERSION=3.12.7`,
      `PERSISTENCE_BACKEND=postgres`, `DATABASE_URL` y `SECRET_KEY`; confirmar
      que **no** existe `DATABASE_PATH`.
- [ ] **PENDIENTE:** confirmar en los logs del build Python 3.12.7 y la
      instalación correcta de `psycopg[binary]==3.3.8` (riesgo R-01).
- [ ] **PENDIENTE:** reintroducir/verificar, si se necesitan, las variables
      manuales del panel (`AUTOMATION_WEBHOOK_URL`,
      `AUTOMATION_WEBHOOK_AUTH_HEADER`, `CONSULTORIO_ADMIN_TOKEN`) sin registrar
      sus valores.

### 6.3 Arranque y esquema

- [ ] **PENDIENTE:** deploy en estado **Live** y `/` + `/citas` con HTTP 200
      (no 503).
- [ ] **PENDIENTE:** `schema_migrations` con versiones `1..4` en Neon.
- [ ] **PENDIENTE:** índice `ux_appointments_slot_open` y
      `UNIQUE (event_id)` presentes en Neon.
- [ ] **PENDIENTE:** ausencia de errores de conexión o de DSN en los logs.

### 6.4 Reserva completa

- [ ] **PENDIENTE:** reserva ficticia en `/citas` → 303 a
      `/citas/confirmada/<id>` y página «Confirmada».
- [ ] **PENDIENTE:** horario ocupado en `/citas/horarios` tras la reserva.
- [ ] **PENDIENTE:** cita y sus dos eventos visibles en Neon
      (`appointment.confirmed` y `appointment.confirmation_email`).

### 6.5 Persistencia tras redespliegue

- [ ] **PENDIENTE:** redesplegar el servicio y esperar **Live**.
- [ ] **PENDIENTE:** la cita y sus eventos siguen existiendo tras el
      redespliegue (RF-2).

### 6.6 Persistencia tras spin-down

- [ ] **PENDIENTE:** esperar el spin-down del servicio web (≥ 15 min sin
      tráfico; distinto del cold start de Neon de T13).
- [ ] **PENDIENTE:** primera petición tras el spin-down con éxito.
- [ ] **PENDIENTE:** la cita y sus eventos siguen existiendo (RF-3).

### 6.7 Coste y secretos

- [ ] **PENDIENTE:** confirmar que no hay recursos de pago activos (RNF-1).
- [ ] **PENDIENTE:** revisar que ni el repositorio ni esta evidencia contienen
      DSN, contraseñas, tokens ni PII real (RNF-6).

## 7. Procedimiento operativo

El detalle paso a paso está en `docs/operaciones/postgresql.md`:

- «Despliegue en Render (T14)» → pasos 1–9;
- advertencia sobre el **pooler** y `statement_timeout`;
- rotación de la credencial en Neon.

## 8. Riesgos y bloqueos conocidos

| # | Riesgo / bloqueo | Impacto | Mitigación |
|---|---|---|---|
| 1 | El implementador no tiene acceso al panel de Render ni API key | No puede ejecutar el despliegue | Lo ejecuta la usuaria; esta evidencia queda PREPARADA y PENDIENTE |
| 2 | `render.yaml` actualizado vive en `feature/hu-019-migracion-postgres` y no se ha pusheado | El Blueprint no verá los cambios hasta que lleguen a su rama | El coordinador hará commit/push/merge cuando la usuaria prepare el panel |
| 3 | La región no se puede modificar tras crear el servicio | El servicio actual (Oregón por defecto) no sirve | Borrar y recrear en Ohio (paso 1) |
| 4 | El DSN del pooler no funciona con la app | `ensure_schema()` falla y `/citas` responde 503 | Usar el endpoint directo (sin `-pooler`), decisión D11 |
| 5 | La URL pública puede cambiar al recrear el servicio | Enlaces o pruebas con la URL anterior fallan | Anotar la URL nueva y actualizarla en la evidencia |
| 6 | El spin-down del servicio web no es el cold start de Neon | Confundir ambos ciclos | T13 ya verificó Neon; T14 verifica el servicio web |
| 7 | Al borrar el servicio se pierden variables configuradas solo en el panel | Fallan automatización o superficie admin tras la recreación | Anotar antes del borrado las variables manuales (webhook, token admin) y reintroducirlas sin registrarlas en documentos |

## 9. Criterio de cierre de T14

T14 solo podrá marcarse como completada cuando la usuaria ejecute los pasos del
panel y esta evidencia registre, con resultados reales:

- región Ohio y variables correctas;
- esquema creado en Neon;
- reserva completa persistida;
- persistencia tras **redespliegue**;
- persistencia tras **spin-down**;
- sin recursos de pago ni secretos en el repositorio.

Hasta entonces, el estado es **PREPARADO — PENDIENTE**.
