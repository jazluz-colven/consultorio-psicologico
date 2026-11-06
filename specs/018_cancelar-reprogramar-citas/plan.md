# Plan 018 — Cancelar y reprogramar citas por el consultorio

> Trazabilidad: **HU-018 → Spec 018 (`specs/018_cancelar-reprogramar-citas/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs`.
> **Estado: plan revisado — aprobado por la usuaria el 2026-11-05.**
> La spec 018 queda **enmendada y aprobada el 2026-11-05** (enmienda mínima, ver
> `spec.md`). La base del plan se aprobó el **2026-10-13**; esta revisión corrige
> los defectos de la revisión técnica y quedó **aprobado por la usuaria el
> 2026-11-05**; implementación en curso (T1–T5 completadas).
>
> **Decisiones vigentes confirmadas por la usuaria (2026-11-05):**
> - **Modelo A confirmado**: reprogramar = **cancelar primero** la cita original
>   y **después** registrar la nueva; la cancelación confirmada **nunca se
>   revierte**. Se **descarta** la enmienda «reservar primero» del commit
>   `8c0b3a5` de la rama no mergeada `chore/proyecto-docs` como fuente de
>   verdad: es internamente contradictoria y la rama está muy desfasada; **no
>   debe mergearse en bloque**.
> - **Intención funcional**: el **psicólogo/administrador del consultorio** es
>   quien cancela la cita y, si procede, propone/registra la nueva para el mismo
>   paciente. **No hay aceptación del paciente dentro del sistema**: la nueva
>   cita queda registrada y confirmada, y el paciente recibe la notificación de
>   cancelación de la anterior y la confirmación de la nueva (RF-4/RF-5).
> - Rutas internas propias (011/012 intactas); token solo por variable de
>   entorno `CONSULTORIO_ADMIN_TOKEN` (Q1 de la spec, 2026-10-13); paciente
>   recibe cancelación + confirmación; sin límite de 3 h para el consultorio.
> - Dudas de este plan: **Q1 esquema híbrido de entrega del token** y **Q2
>   literal «La cita ya estaba cancelada.»** (aprobadas 2026-10-13). Q2 ya forma
>   parte de la tabla contractual de la spec 018 tras la enmienda de 2026-11-05.
>
> Baseline real en `main` (2026-11-05): **302 PASS / 0 FAIL**.
> Objetivo de esta entrega: **320 PASS / 0 FAIL** (302 + 18 funciones nuevas;
> ver §6). Cifra exacta y funciones en `task.md`.

---

## 0. Alcance y cobertura

Implementa únicamente la interfaz interna de Spec 018: que el consultorio pueda
**cancelar** una cita (RF-3) o **reprogramarla** (RF-4) desde una superficie web
mínima protegida por token (RF-1), mostrando siempre un **resumen previo**
(RF-2), informando del **nuevo id** y generando las **notificaciones ya
aprobadas** (cancelación de la anterior + confirmación de la nueva) sin
reversión de cancelaciones confirmadas (RF-6), con errores claros, sin doble
envío (RF-7) y sin restricción de antelación (RF-9).

La reprogramación es **cancelar primero y registrar después**. La nueva cita
queda **confirmada**; el paciente no acepta nada dentro del sistema: solo recibe
la cancelación de la anterior y la confirmación de la nueva. Este plan **no
implementa** la enmienda «reservar primero» de `chore/proyecto-docs` y no la
considera fuente de verdad.

**Lo que NO cambia** (constitución #2, «no reescribir lo que funciona»):

- Firmas y lógica de `cancel_appointment()` y `create_booking()`
  (`consultorio/services/appointment_service.py`) — la interfaz **delega** en
  ellas (constitución #3); no se modifica su comportamiento.
- Specs 011/012 (agenda, solo lectura), 004/005/006 (reserva/disponibilidad),
  007/008/010 (eventos y correos) y 017 (cancelación por el paciente) — sin
  modificaciones.
- `spec.md` de la Spec 018 — **enmendado y aprobado el 2026-11-05** con los
  cuatro cambios mínimos registrados en §7.1; no se reabre.
- Sin dependencias nuevas (constitución #1): solo stdlib
  (`hmac.compare_digest` para el token) + Flask ya usado.

**Correcciones incorporadas en la revisión 2026-11-05:**

- Cifras reales: baseline **302** y objetivo **320**.
- Token robusto ante `None`/vacío/no ASCII, con cabeceras de no caché y
  `Referrer-Policy`, y `?token=` restringido a GET (D2).
- Orden de reprogramación: cargar → **si ya está cancelada, parar** → validar →
  comprobar hueco → cancelar → crear (D4).
- Campos reales del `Appointment` (`patient_name`, `document_number`, `email`,
  `phone`, `document_type`) (D5).
- Literal contractual de horario ocupado de la Spec 018, sin importar el de la
  Spec 004 (D6).
- Estados RNF mapeados a la UI admin (D7).
- Justificación correcta de la ausencia de capturas 1280/375 (D8).
- Formulario de reprogramación alimentado por `BOOKING_HOURS` (14 slots) y
  `SERVICES_CATALOG`; fecha con `input type="date"` y validación de servidor
  mediante las reglas de la Spec 004 (D4/D8).
- TC-018-014 distingue **14 literales contractuales** (los 13 anteriores + «Cita
  ya cancelada») y **6 etiquetas funcionales**, con **20 constantes** en total.
- El plan usa únicamente las decisiones definidas D1–D12.

## 1. Requisitos → diseño (matriz RF)

| RF | Diseño | Prueba clave |
|---|---|---|
| RF-1 token | `_check_token()` robusto en el blueprint `admin`; sin token, incorrecto, vacío o no ASCII → 403 con el literal de acceso denegado; `?token=` solo en GET; cabeceras `Cache-Control: no-store` y `Referrer-Policy: no-referrer` | TC-018-001 |
| RF-2 resumen | `GET /admin/citas/<id>` con paciente/servicio/fecha/hora/estado; si la cita está cancelada muestra «Cancelada» y **sin formularios operativos** | TC-018-002, TC-018-003 |
| RF-3 cancelar | `POST /admin/citas/<id>/cancelar` → `cancel_appointment()`; si ya estaba cancelada, literal Q2 sin llamar al servicio | TC-018-004, TC-018-005, TC-018-006, TC-018-012, TC-018-019 |
| RF-4 reprogramar | `POST /admin/citas/<id>/reprogramar`: cargar → si cancelada parar → `validate_booking()` → `is_slot_taken()` → `cancel_appointment()` → `create_booking()` con `cancellation_url_builder` | TC-018-007, TC-018-008, TC-018-010, TC-018-017, TC-018-018 |
| RF-5 nuevo id + correos | literal «Cita reprogramada. Nueva cita #{id}.»; eventos de cancelación y confirmación; la confirmación de la nueva contiene el enlace de cancelación | TC-018-007, TC-018-008 |
| RF-6 sin reversión | validación y `is_slot_taken` **antes** de cancelar; si `create_booking()` devuelve `SLOT_TAKEN` tras cancelar, la cancelación permanece y no se revierte | TC-018-009, TC-018-010, TC-018-017 |
| RF-7 doble envío | guard de doble envío en ambos formularios + idempotencia del backend ante refresh/re-POST | TC-018-012, TC-018-013, TC-018-019 |
| RF-8 errores | literales propios: no encontrada, ya cancelada, acceso denegado; sin fuga de datos de otras citas | TC-018-001, TC-018-002, TC-018-003, TC-018-006 |
| RF-9 sin 3 h | sin código extra: se puede cancelar una cita del mismo día o pasada; la **fecha nueva** de la reprogramación sigue las reglas de la Spec 004 | TC-018-011 |

**Cobertura explícita solicitada por la revisión:**

- **RF-6 en carrera** (la reserva nueva falla después de cancelar): TC-018-017.
- **RF-8 en reprogramación de cita ya cancelada**: TC-018-006; **GET de cita
  cancelada**: TC-018-002; **sin fuga de datos**: TC-018-001 (403) y
  TC-018-003 (404).
- **RF-9 en cancelación de cita pasada**: TC-018-011.
- **RF-5 con enlace de cancelación en la confirmación de la nueva cita**:
  TC-018-007.
- **RF-4 con orden cancelar → crear**: TC-018-018.

## 2. Decisiones técnicas

- **D1 — Superficie y resultado (decisión aprobada)**: blueprint nuevo `admin`
  en `consultorio/web/admin.py` (`url_prefix="/admin"`), 3 rutas; registro con
  una línea en `create_app()`:

| Método | Ruta | Comportamiento | Éxito |
|---|---|---|---|
| GET | `/admin/citas/<int:cita_id>` | resumen + formularios cancelar/reprogramar (RF-2); si la cita está `cancelled`, estado «Cancelada» y sin formularios operativos | 200; 404 si no existe; 403 si token inválido |
| POST | `/admin/citas/<int:cita_id>/cancelar` | `cancel_appointment()` | 200 con «Cita cancelada.» |
| POST | `/admin/citas/<int:cita_id>/reprogramar` | cancel + `create_booking()` | 200 con «Cita reprogramada. Nueva cita #{id}.» |

  Los POST renderizan el resultado directamente (200). **Decisión aprobada**:
  se mantiene el POST → 200; **no se cambia a PRG** sin aprobación explícita.
  El PRG (303 + GET de resultado) queda como **alternativa no implementada**.
  **Refresh/re-POST**: un refresh repite el POST; el servicio es idempotente
  (`ALREADY_CANCELLED`/estado ya cancelado, sin segundo correo) y el guard RF-7
  minimiza el caso. El segundo POST **no duplica la cita ni el correo** y
  **puede mostrar un mensaje distinto del original** (p. ej. «La cita ya estaba
  cancelada.» en cancelación, o el mismo literal al reprogramar una original ya
  cancelada). TC-018-019 lo verifica.

- **D2 — Entrega del token** (Q1 aprobada): sin sesiones/cookies en el sitio →
  **cada request porta el token**:
  - GET: cabecera `X-Admin-Token` **y**, como alternativa para navegador sin JS,
    query `?token=...`;
  - POST: campo oculto `admin_token` en el formulario **y** acepta también la
    cabecera (tests/scripts);
  - **`?token=` solo se acepta en GET**; en POST se ignoran los parámetros de
    query;
  - `_check_token` tolera `None`/no ASCII: `given = ... or ""`;
    `if not expected or not given: return False`; comparación con bytes
    `hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))`;
  - `CONSULTORIO_ADMIN_TOKEN` vacío en config → **todas** las rutas responden
    403 (funcionalidad desactivada por defecto, seguro en Render sin
    configurar);
  - las respuestas admin incluyen `Cache-Control: no-store` y
    `Referrer-Policy: no-referrer`;
  - **riesgo residual**: `?token=` puede quedar en logs de acceso, historial del
    navegador o cabecera `Referer`. Se reduce con GET-only y las cabeceras
    anteriores, pero **no se promete** impedir el log de acceso del servidor;
  - el token nunca se loguea ni aparece en plantillas salvo el campo oculto.

- **D3 — Flujo cancelar**: token OK → cargar cita (`None` → «No encontramos esa
  cita. Revisa la referencia.», 404) → si la cita cargada ya está `cancelled`,
  responder `ADMIN_MSG_ALREADY_CANCELLED` sin llamar al servicio → si no,
  `cancel_appointment(id, db, AUTOMATION_*)` con la config de la app → éxito:
  «Cita cancelada.»; `ALREADY_CANCELLED`: mismo literal Q2;
  `APPOINTMENT_NOT_FOUND`: literal de no encontrada. El literal Q2
  («La cita ya estaba cancelada.») ya forma parte de la tabla contractual de la
  spec 018 (enmienda 2026-11-05).

- **D4 — Flujo reprogramar** (orden para minimizar daño, RF-6):
  1. cargar cita vieja (404 si no existe);
  2. **si `status == cancelled` → `ADMIN_MSG_ALREADY_CANCELLED` y parar sin
     validar, sin comprobar hueco y sin cancelar**;
  3. construir `data` nuevo = los 5 datos del paciente copiados de la cita +
     `service/date/time` del formulario (D5);
  4. `validate_booking(data)` → errores → re-render del formulario con
     errores, **sin cancelar nada**;
  5. `is_slot_taken()` → ocupado → `ADMIN_SLOT_TAKEN`, **sin cancelar nada**;
  6. `cancel_appointment(vieja)` → si falla, se para (nada nuevo creado);
  7. `create_booking(data, ..., cancellation_url_builder=lambda id: url_for(
     "cancellation.verify", cita_id=id, _external=True))` → `SLOT_TAKEN` por
     carrera → `ADMIN_SLOT_TAKEN` (la **cancelación permanece**, nunca se
     revierte); éxito → «Cita reprogramada. Nueva cita #{id}.» + eventos
     heredados (`confirmed`, `confirmation_email`, `cancellation_email`,
     `cancelled`).
  El `cancellation_url_builder` hace que la confirmación de la nueva cita
  cumpla la Spec 017 RF-13 y la enmienda coordinada de la Spec 008. El orden
  «cancelar antes de crear» es verificable con un spy/monkeypatch de las
  llamadas (TC-018-018).
  El formulario de reprogramación recibe de la vista
  `services=SERVICES_CATALOG` y `booking_hours=BOOKING_HOURS` (los 14 slots:
  08:00–11:30 y 14:00–16:30); la fecha es un `input type="date"` y la
  validación de servidor con `validate_booking()` aplica las reglas de la
  Spec 004 (lunes a viernes, no anterior a hoy). El HTML5 no sustituye esa
  validación y no se inventan catálogo ni horarios nuevos.

- **D5 — Datos del paciente**: la nueva cita copia `document_type`,
  `document_number`, `patient_name`, `email` y `phone` de la cita vieja; el
  formulario interno **solo** pide `service`, `date` y `time` nuevos. Se usan
  exclusivamente los campos reales del `Appointment`; no se inventan nombres de
  campo. `document_type` es obligatorio para `validate_booking()` y la columna
  es NOT NULL. Ningún dato personal en URLs, mensajes ni logs.

- **D6 — Contenido**: módulo nuevo `consultorio/content/admin_content.py` con
  **20 constantes** y prefijo `ADMIN_` en todas:
  - **14 literales contractuales** de la tabla de la spec 018 (los 13 anteriores
    + `ADMIN_MSG_ALREADY_CANCELLED = "La cita ya estaba cancelada."`, fila «Cita
    ya cancelada» incorporada por la enmienda de 2026-11-05);
  - **6 etiquetas funcionales**: «Servicio», «Nueva fecha», «Hora», «Resumen de
    la cita», «Paciente», «Estado».
  Para «Horario no disponible» se usa el literal contractual de la spec 018:
  `ADMIN_SLOT_TAKEN = "Ese horario ya está ocupado. Elige otro."`; **no se
  importa** `appointment_content.MSG_SLOT_TAKEN` (su texto es «Ese horario ya
  no está disponible. Selecciona otro horario.»; prevalece la spec).
  `ADMIN_ACCESS_DENIED` y `ADMIN_APPOINTMENT_NOT_FOUND` toman la tabla literal.
  Los estados «Confirmada»/«Cancelada» reutilizan
  `STATUS_CONFIRMED_LABEL`/`STATUS_CANCELLED_LABEL` (no se duplican). Espejo
  obligatorio en `tests/expected_content.py`. Si la usuaria aprueba un literal
  de error de persistencia (§7.1), se añadirá como constante y TC condicionado;
  **no se implementa por defecto**.

- **D7 — Estados de la UI admin (RNF)**: se mapean los estados exigidos por la
  spec a la pantalla interna:

| Estado RNF | UI admin |
|---|---|
| disponible | GET 200 con resumen y formularios habilitados |
| validando | validación HTML5 + `admin.js` en cliente y `validate_booking()` en servidor; errores re-render sin cambios |
| procesando | `aria-busy="true"` + botón `disabled`; sin copy nuevo |
| éxito | `result.html` con el literal de éxito correspondiente |
| conflicto | horario ocupado / cita ya cancelada; mensaje coherente con el estado real del backend |
| error | acceso denegado, cita no encontrada o datos inválidos; sin fuga de datos |

- **D8 — Templates**: `templates/admin/appointment_detail.html` (resumen +
  formularios) y `templates/admin/result.html` (resultado con «Volver» →
  `/citas`); heredan `base.html`, paleta Serenidad Natural, texto justificado,
  foco visible. La vista pasa `services=SERVICES_CATALOG` y
  `booking_hours=BOOKING_HOURS`; el formulario de reprogramación usa un
  `select` de servicios del catálogo, un `input type="date"` para la fecha nueva
  y las 14 horas válidas de `BOOKING_HOURS` (08:00–11:30 y 14:00–16:30), sin
  catálogos ni horarios inventados. La pantalla es **visible aunque sea
  interna**: se decide **no generar capturas 1280/375**; la validación será
  funcional manual y la revisión de paleta/contraste se hará en la tarea de
  demo/QA. Si se generan capturas, usar CDP
  (`Emulation.setDeviceMetricsOverride`), no `--window-size`.

- **D9 — Config**: `Config.CONSULTORIO_ADMIN_TOKEN =
  os.environ.get("CONSULTORIO_ADMIN_TOKEN", "")` (mismo patrón de secreto que
  `AUTOMATION_WEBHOOK_AUTH_HEADER`). Tests: valor fijo de prueba
  (`"test-admin-token"`) en un `TempConfig` local — nunca el token real.

- **D10 — Blueprints intactos**: registro único del `admin_bp` en
  `consultorio/__init__.py`; rutas de 011/012 no existen y no se tocan.

- **D11 — Rama y baseline**: `feature/hu-018` desde `main` (con HU-010
  mergeada); baseline real **302 PASS / 0 FAIL**.

- **D12 — Sin PII en logs**: los handlers no loguean datos de pacientes ni el
  token (constitución #6).

## 3. Algoritmo (pseudocódigo de los handlers)

```text
_check_token(config, request):
    expected = config.get("CONSULTORIO_ADMIN_TOKEN") or ""
    given = (request.headers.get("X-Admin-Token")
             or request.form.get("admin_token")
             or (request.args.get("token") if request.method == "GET" else "")
             or "")
    if not expected or not given:
        return False
    return hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))

respuesta_admin(...):
    añade Cache-Control: no-store y Referrer-Policy: no-referrer

GET /admin/citas/<id>:
    token inválido → acceso denegado (403) + cabeceras
    cita = get_appointment_by_id(); None → no encontrada (404)
    si cita.status == cancelled → resumen con «Cancelada», sin formularios operativos
    si no → resumen + formularios (cancelar siempre visible; reprogramar con
           services=SERVICES_CATALOG, booking_hours=BOOKING_HOURS,
           input type="date" para la fecha y las 14 horas válidas)

POST /admin/citas/<id>/cancelar:
    guards token + cita
    si cita.status == cancelled → ADMIN_MSG_ALREADY_CANCELLED (200)
    r = cancel_appointment(id, db, AUTOMATION_*)
    éxito | APPOINTMENT_NOT_FOUND | ALREADY_CANCELLED → result.html (200)

POST /admin/citas/<id>/reprogramar:
    guards token + cita vieja
    si cita.status == cancelled → ADMIN_MSG_ALREADY_CANCELLED (200)
        sin validar, sin comprobar hueco y sin cancelar
    data = copia de document_type/document_number/patient_name/email/phone
           + form (service, date, time)
    validate_booking(data) con errores → detail.html con errores (200)
    is_slot_taken → ADMIN_SLOT_TAKEN (200)
    r = cancel_appointment(vieja); si sentinela → error (200)
    n = create_booking(data, ..., cancellation_url_builder=lambda id: url_for(
            "cancellation.verify", cita_id=id, _external=True))
        SLOT_TAKEN → ADMIN_SLOT_TAKEN (200, la cancelación de la cita
                     anterior se mantiene); éxito → «Cita reprogramada.
                     Nueva cita #{n.id}.» (200)
```

Config de automación heredada: `AUTOMATION_WEBHOOK_URL`,
`AUTOMATION_TIMEOUT_SECONDS`, `AUTOMATION_WEBHOOK_AUTH_HEADER` — pasadas igual
que en `consultorio/web/appointments.py:129-140`.

## 4. Comandos

```powershell
git status                         # rama y estado
git checkout -b feature/hu-018     # desde main (9846613, 302 PASS)
python -m pytest -q                # suite completa por fase
python app.py                      # servidor de revisión (http://127.0.0.1:5000)
```

## 5. Fuera de alcance (spec)

Login/sesiones/roles; agenda diaria (011/012); cancelación/reprogramación por
el paciente (017); `initiated_by` en BD; WhatsApp (009); historial de
reprogramaciones pasadas; reintentos; panel de envíos; cambios en servicios
existentes.

## 6. Estrategia de tests

**6.1 Matriz** (números fijos en `task.md`; archivos nuevos:
`tests/test_admin_routes.py`, `tests/test_hu_018.py`, `tests/test_admin_content.py`):

| TC | Qué | Resultado esperado |
|---|---|---|
| TC-018-001 | GET/POST sin token, token incorrecto, `None`, no ASCII y config vacía; 403 sin datos de la cita | 403 + «No tienes acceso…» + cabeceras `no-store`/`no-referrer`; sin PII |
| TC-018-002 | GET detalle con token en cabecera y en query; cita cancelada | 200 con resumen y estados; servicios/horas desde `SERVICES_CATALOG`/`BOOKING_HOURS`, fecha `input type="date"`; cita cancelada muestra «Cancelada» y sin formularios operativos |
| TC-018-003 | GET detalle de cita inexistente | 404 + literal de no encontrada |
| TC-018-004 | POST cancelar con token en cabecera y en campo oculto | 200 «Cita cancelada.», estado cancelled |
| TC-018-005 | Cancelar genera evento `appointment.cancellation_email` (filtrado por `event_type`) | 1 evento `sent`; evento `appointment.cancelled` presente |
| TC-018-006 | Cancelar cita inexistente / ya cancelada; reprogramar cita ya cancelada | literales correspondientes; sin cambios ni eventos nuevos |
| TC-018-007 | Reprogramar a horario libre | vieja cancelled + nueva confirmed; 1 `sent` de `appointment.cancelled`, `appointment.cancellation_email`, `appointment.confirmed` y `appointment.confirmation_email`; la confirmación contiene el enlace `cancellation.verify` |
| TC-018-008 | Literal de éxito con el id correcto | «Nueva cita #N» con N real; estados vieja/nueva correctos |
| TC-018-009 | Reprogramar a horario ocupado | `ADMIN_SLOT_TAKEN`; **vieja intacta** (RF-6) |
| TC-018-010 | Reprogramar con datos nuevos inválidos (fecha pasada/fin de semana) | errores; **vieja intacta** |
| TC-018-011 | Cancelar cita del mismo día y cita pasada; reprogramar a hoy; fecha nueva inválida | cancelación permitida (RF-9); la fecha nueva sigue las reglas de la Spec 004 |
| TC-018-012 | Doble envío: segundo POST cancelar/reprogramar | sin segunda cita ni segundo correo; filtrado por `event_type` |
| TC-018-013 | Guard RF-7 presente en el HTML | script `admin.js`, formularios asociados, botones inicialmente habilitados y patrón `disabled`/`aria-busy` |
| TC-018-014 | Espejo y naturaleza de las 20 constantes | **14 literales contractuales** contra la tabla de la spec 018 y `expected_content.py`; **6 etiquetas funcionales** contra el espejo y D6 |
| TC-018-015 | Constitución #1: sin dependencias nuevas | import check |
| TC-018-016 | Regresión completa | **320 passed / 0 failed** (302 previos + 18 nuevas) |
| TC-018-017 | Carrera después de cancelar: `create_booking()` devuelve `SLOT_TAKEN` | mensaje de horario ocupado; la cita original queda `cancelled`; no se crea otra; no se revierte |
| TC-018-018 | Orden de llamadas con spy/monkeypatch | primero `cancel_appointment`, después `create_booking` |
| TC-018-019 | Refresh/re-POST | segundo POST no duplica cita ni eventos; se comporta de forma segura (puede mostrar otro mensaje) |

**6.2 Demo manual** (receptor stdlib local, patrón HU-010): reservar cita
pública → cancelar desde `/admin/citas/<id>` → verificar `appointment.cancelled`
+ `appointment.cancellation_email` → comprobar el borrado del evento de Google
Calendar por n8n (Spec 007 RF-8) → reservar otra → reprogramar → verificar
`appointment.cancelled` + `appointment.cancellation_email` +
`appointment.confirmed` + `appointment.confirmation_email`, estados vieja
`cancelled`/nueva `confirmed` y enlace de cancelación en la confirmación →
token inválido → horario ocupado → doble clic → misma fecha (RF-9) →
comportamiento del refresh/re-POST.

**6.3 QA**: `docs/evidencias/hu-018/qa-hu-018.md` con PASS/FAIL por TC,
captura del flujo si aplica y checkbox de aceptación. La pantalla es interna pero
visible; se decide no generar capturas 1280/375 y se revisa paleta/contraste en
T6. Si se generan capturas, usar CDP.

## 7. Aprobación, dudas y enmiendas

### 7.1 Dudas resueltas y pendientes de enmienda de spec

**Dudas resueltas:**

- **[RESUELTA — Q1]** Entrega del token (D2): esquema híbrido aprobado —
  cabecera `X-Admin-Token` para scripts/tests + campo oculto `admin_token` para
  los formularios + `?token=` como alternativa de navegador (2026-10-13),
  restringido a GET en esta revisión.
- **[RESUELTA — Q2]** Literal nuevo (D6): «La cita ya estaba cancelada.» para
  el caso de doble cancelación — **aprobado** (2026-10-13) y **ya incorporado a
  la tabla contractual** por la enmienda de 2026-11-05.
- **[RESUELTA — 2026-11-05]** Modelo A confirmado: cancelar primero y registrar
  después; sin reversión; sin aceptación del paciente en el sistema.
- **[RESUELTA — 2026-11-05]** Se descarta la enmienda «reservar primero» de
  `chore/proyecto-docs` como fuente de verdad.
- **[RESUELTA — 2026-11-05]** Campos reales del `Appointment` y necesidad de
  copiar `document_type` (D5).
- **[RESUELTA — 2026-11-05]** Orden de reprogramación con comprobación previa
  de cita ya cancelada (D4).
- **[RESUELTA — 2026-11-05]** La confirmación de la nueva cita incluye el
  enlace de cancelación mediante `cancellation_url_builder` (D4).
- **[RESUELTA — 2026-11-05]** Refresh/re-POST: POST → 200 se mantiene; la
  idempotencia se documenta y se prueba (D1).
- **[RESUELTA — 2026-11-05]** El plan usa únicamente D1–D12; no quedan
  decisiones referenciadas sin definir.

**Enmiendas aplicadas a `spec.md` — RESUELTAS/APLICADAS el 2026-11-05:**

1. **[RESUELTA/APLICADA — 2026-11-05] Contexto de la spec atribuía a la
   Spec 010 también la reprogramación.** La Spec 010 solo cancela. Aplicado:
   «reutiliza la cancelación y la liberación de horario de la Spec 010, las
   reglas de reserva/disponibilidad de las Specs 004/005/006 y las
   notificaciones de las Specs 008/010».
2. **[RESUELTA/APLICADA — 2026-11-05] La tabla contractual no incluía el
   literal de «ya cancelada».** Aplicada la fila
   `| Cita ya cancelada | La cita ya estaba cancelada. |` con el **literal Q2**
   aprobado el 2026-10-13 (se descarta reutilizar el de la Spec 017).
3. **[RESUELTA/APLICADA — 2026-11-05] RF-9 era ambiguo sobre «citas
   pasadas».** Aplicado el texto que explicita que la fecha nueva de una
   reprogramación sigue las reglas de la Spec 004 (lunes a viernes, no anterior
   a hoy).
4. **[RESUELTA/APLICADA — 2026-11-05] RF-1 decía «no se mostrará nada» pero
   la tabla exige mostrar el mensaje de acceso denegado.** Aplicado el texto que
   aclara que no se muestra información de la cita ni se procesa la
   funcionalidad y la respuesta muestra únicamente el mensaje de acceso
   denegado.

**Pendiente opcional (NO ejecutada; no afecta a la cifra 320):**

5. **[NECESITA APROBACIÓN DE LA USUARIA — opcional] Literal de error de
   persistencia (si se adopta).** Propuesta: «No se pudo completar la operación.
   Inténtalo de nuevo.» **No se implementa** por defecto; si se aprobara, se
   añadiría su TC y la cifra objetivo se recalcularía. Hoy la cifra vigente es
   **320**.

Los puntos 1–4 quedaron aplicados en `spec.md` el 2026-11-05. El plan y el
`task.md` quedaron **aprobados por la usuaria el 2026-11-05**.

### 7.2 Pendientes de ejecución (bloquean declarar COMPLETADO)

- [x] Aprobación de este plan revisado (2026-11-05) y de `task.md`.
- [x] Creación de `feature/hu-018` desde `main` (D11) y verificación del
      baseline **302 PASS / 0 FAIL**.
- [x] Espejo + `admin_content` + `Config.CONSULTORIO_ADMIN_TOKEN`.
- [x] Blueprint `admin` + templates + guard de doble envío + registro en
      `create_app()`.
- [x] Tests §6 en verde: objetivo **320 PASS / 0 FAIL** con los 302 previos
      intactos (cifra exacta y funciones en `task.md`).
- [ ] Demo manual §6.2 + evidencia en `docs/evidencias/hu-018/`.
- [ ] Informe QA `qa-hu-018.md` con PASS/FAIL por TC y checkbox de aceptación.
- [ ] Commit/Push por fases, `MEMORY.md` y aceptación de la HU.
- [ ] Servidor de revisión en marcha (AGENTS.md) y URL comunicada.

> Nota de estado (2026-11-05): T1–T5 ejecutadas y versionadas en
> `feature/hu-018` — `c1d53b5` (T1), `b099104` (T2), `e08c8fe` (T3),
> `f3314d6` (T4), `832149e` (T5) — con suite real **320 PASS** (2026-11-05).

---

## 8. Secuencia de implementación

Cada tarea se cierra con **sus propios tests en verde**, sin depender de tests
posteriores. La cifra acumulada de la suite se indica en cada paso.

0. **Aprobación de este plan revisado** (2026-11-05) y de `task.md` —
   **Aprobado por la usuaria el 2026-11-05**.
1. **Rama y baseline**: `feature/hu-018` desde `main` (`9846613`), baseline
   **302 PASS**; commit de `spec.md` (enmienda 2026-11-05), `plan.md` y
   `task.md` (T1).
2. **Contenido, espejo y config**: `expected_content.py`, `admin_content.py`
   (20 constantes) y `Config.CONSULTORIO_ADMIN_TOKEN`; `test_admin_content.py`
   con TC-018-014 y TC-018-015 → **304 PASS** (T2).
3. **Plantillas, guard, GET y cancelar**: `appointment_detail.html`,
   `result.html`, `admin.js`, blueprint `admin` con token robusto, GET de
   detalle (incluye `SERVICES_CATALOG`, `BOOKING_HOURS` y `input type="date"`),
   POST cancelar y registro en `create_app()`; tests TC-018-001, 002, 003, 004
   y 013 → **309 PASS** (T3).
4. **Reprogramar**: POST reprogramar con el orden D4, campos reales,
   `cancellation_url_builder` y fecha validada en servidor; tests TC-018-006,
   008, 012 y 019 → **313 PASS** (T4).
5. **Tests de HU**: `test_hu_018.py` con TC-018-005, 007, 009, 010, 011, 017 y
   018 → suite completa (TC-018-016) **320 PASS** (T5).
6. **Demo manual y QA**: §6.2 + evidencia con Calendar/n8n, refresh, estados y
   contraste; `qa-hu-018.md` (T6).
7. **Cierre**: commits por fase + push + `MEMORY.md` + servidor de revisión en
   marcha y URL comunicada (T7).
