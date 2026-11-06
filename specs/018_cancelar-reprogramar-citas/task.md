# Tareas — Spec 018: Cancelar y reprogramar citas por el consultorio

Estado: **borrador para aprobación de la usuaria (2026-11-05)**.

> Trazabilidad: **HU-018 → Spec 018 (`spec.md`, enmendada y aprobada
> 2026-11-05) → `plan.md`
> (base aprobada 2026-10-13; revisión 2026-11-05 pendiente de aprobación,
> D1–D12, Q1/Q2) → este `task.md` → código → tests → evidencia → commit.**
> Rama a crear: **`feature/hu-018` desde `main`** (`9846613`, baseline real
> **302 passed / 0 failed**). Comandos: `python -m pytest -q`, `python app.py`.
> **7 tareas** ordenadas por dependencia, y **cada una se cierra con sus propios
> tests en verde o con la evidencia que ella misma produce**, sin depender de
> tests de tareas posteriores. Todas nacen **sin marcar** (`[ ]`): ninguna se
> considera completada por estar redactada.
>
> **Intención funcional confirmada (2026-11-05):** el **psicólogo/administrador
> del consultorio** es quien cancela la cita y, si procede, propone/registra la
> nueva para el mismo paciente. **No hay aceptación del paciente dentro del
> sistema**: la nueva cita queda registrada y confirmada, y el paciente recibe
> la notificación de cancelación de la anterior y la confirmación de la nueva
> (RF-4/RF-5).
>
> **Decisión A confirmada (2026-11-05):** reprogramar = **cancelar primero** la
> cita original y **después** registrar la nueva; la cancelación confirmada
> **nunca se revierte**. Se descarta la enmienda «reservar primero» del commit
> `8c0b3a5` de la rama no mergeada `chore/proyecto-docs` como fuente de verdad;
> esa rama **no debe mergearse en bloque**.
>
> Restricciones transversales: la Spec 018 queda **enmendada y aprobada
> (2026-11-05)** y no se reabre; no se tocan las Specs
> **004/005/006/007/008/010/011/012/017**; no se modifican
> `cancel_appointment()` ni `create_booking()` (la interfaz **solo delega** en
> ellas); sin dependencias nuevas; sin PII ni token real en logs, docs, tests o
> memoria. En tests se usa el valor ficticio **`test-admin-token`**.

## Estado, alcance y decisiones fijadas

- **Spec 018 ENMENDADA Y APROBADA (2026-11-05)**: RF-1..RF-9, tabla de textos
  contractuales (14 literales, incluido «Cita ya cancelada» → «La cita ya estaba
  cancelada.») y «Fuera de alcance» vigentes. No se reabre. Las enmiendas 1–4
  ya están aplicadas en `spec.md` (enmienda 2026-11-05); solo queda el literal
  opcional de error de persistencia.
- **Plan 018**: base **aprobada 2026-10-13**; revisión **2026-11-05 pendiente de
  aprobación**. Decisiones D1–D12 y Q1/Q2. Q2 («La cita ya estaba cancelada.»)
  es un literal aprobado que **ya está en la tabla contractual** de la spec 018
  (enmienda 2026-11-05).
- **Baseline real medido el 2026-11-05**: `python -m pytest -q` → **302 passed,
  0 failed** (79,48 s). Es el baseline que usan estas tareas.
- **Objetivo de esta entrega**: **320 passed / 0 failed** = 302 + **18 funciones
  de test nuevas** (cálculo detallado más abajo). **TC-018-016 es la corrida
  completa, no una función.**
- **Token**: `CONSULTORIO_ADMIN_TOKEN` **solo por variable de entorno**
  (`Config.CONSULTORIO_ADMIN_TOKEN = os.environ.get("CONSULTORIO_ADMIN_TOKEN", "")`).
  En tests se usa un `TempConfig` local con el valor ficticio
  **`test-admin-token`**. Nunca se versiona un token real.
- **Decisiones que condicionan las tareas**: D1 (3 rutas internas; POST responde
  200; refresh/re-POST idempotente), D2 (token robusto + cabeceras + `?token=`
  solo GET), D3 (cancelar delega en `cancel_appointment()`), D4 (reprogramar:
  cargar → si ya cancelada parar → validar → comprobar hueco → cancelar →
  crear; sin reversión; con `cancellation_url_builder`; fecha validada en
  servidor), D5 (copiar los 5 datos reales del paciente, incluido
  `document_type`; el formulario solo pide servicio/fecha/hora), D6 (20
  constantes en `admin_content.py` + espejo; literal contractual de horario
  ocupado), D7 (estados RNF mapeados a la UI), D8 (templates; servicios y horas
  desde `SERVICES_CATALOG`/`BOOKING_HOURS`, fecha `input type="date"`; sin
  capturas 1280/375, validación manual y contraste en T6), D9 (config), D10
  (registro único del blueprint), D11 (rama y baseline 302), D12 (sin PII en
  logs).
- **Nota de revisión 2026-10-23 (obligatoria en tests)**: una reserva/cancelación
  emite **varios eventos**. Al cancelar: `appointment.cancelled` y
  `appointment.cancellation_email`. Al reprogramar se añaden
  `appointment.confirmed` y `appointment.confirmation_email`. Por tanto
  **TC-018-005, TC-018-007 y TC-018-012 filtran por `event_type`**; no cuentan
  POSTs, eventos ni correos a ciegas.
- **Estado de evidencias**: `docs/evidencias/hu-018/` **no existe**; se crea en
  T6.

## Cálculo de la suite (exacto)

| Concepto | Funciones |
|---|---:|
| Baseline real en `main` (2026-11-05) | 302 |
| `tests/test_admin_content.py` | +2 |
| `tests/test_admin_routes.py` | +9 |
| `tests/test_hu_018.py` | +7 |
| **Nuevas** | **+18** |
| **Total esperado** | **320** |

### Cifras incrementales por tarea

| Tarea | Funciones nuevas | Suite acumulada |
|---|---:|---:|
| T1 — rama, baseline y commit de plan/task | 0 | 302 |
| T2 — contenido/espejo/config + tests 014/015 | +2 | 304 |
| T3 — plantillas, guard, GET y cancelar + tests 001/002/003/004/013 | +5 | 309 |
| T4 — reprogramar + tests 006/008/012/019 | +4 | 313 |
| T5 — tests de HU 005/007/009/010/011/017/018 | +7 | 320 |
| T6 — demo manual y QA | 0 | 320 |
| T7 — cierre | 0 | 320 |

Funciones nuevas (nombres exactos; TC-018-016 no es función):

| # | Tarea | Archivo | Función | TC |
|---:|---|---|---|---|
| 1 | T2 | `tests/test_admin_content.py` | `test_tc_018_014_literales_admin_coinciden_con_expected_content_y_tabla_spec` | TC-018-014 |
| 2 | T2 | `tests/test_admin_content.py` | `test_tc_018_015_sin_dependencias_nuevas` | TC-018-015 |
| 3 | T3 | `tests/test_admin_routes.py` | `test_tc_018_001_token_ausente_incorrecto_vacio_o_no_ascii_devuelve_403_sin_datos` | TC-018-001 |
| 4 | T3 | `tests/test_admin_routes.py` | `test_tc_018_002_get_detalle_con_token_en_cabecera_y_query_y_cita_cancelada` | TC-018-002 |
| 5 | T3 | `tests/test_admin_routes.py` | `test_tc_018_003_get_cita_inexistente_404_y_literal` | TC-018-003 |
| 6 | T3 | `tests/test_admin_routes.py` | `test_tc_018_004_post_cancelar_con_token_en_cabecera_y_campo_oculto` | TC-018-004 |
| 7 | T3 | `tests/test_admin_routes.py` | `test_tc_018_013_guard_de_doble_envio_presente_en_el_html` | TC-018-013 |
| 8 | T4 | `tests/test_admin_routes.py` | `test_tc_018_006_cancelar_inexistente_ya_cancelada_y_reprogramar_ya_cancelada` | TC-018-006 |
| 9 | T4 | `tests/test_admin_routes.py` | `test_tc_018_008_reprogramar_muestra_el_id_real` | TC-018-008 |
| 10 | T4 | `tests/test_admin_routes.py` | `test_tc_018_012_doble_post_cancelar_y_reprogramar_sin_segundo_correo` | TC-018-012 |
| 11 | T4 | `tests/test_admin_routes.py` | `test_tc_018_019_refresh_repost_no_duplica_cita_ni_eventos` | TC-018-019 |
| 12 | T5 | `tests/test_hu_018.py` | `test_tc_018_005_cancelar_emite_un_evento_cancellation_email` | TC-018-005 |
| 13 | T5 | `tests/test_hu_018.py` | `test_tc_018_007_reprogramar_deja_vieja_cancelada_y_nueva_confirmada_con_cuatro_eventos_y_enlace` | TC-018-007 |
| 14 | T5 | `tests/test_hu_018.py` | `test_tc_018_009_reprogramar_a_horario_ocupado_no_cancela_la_vieja` | TC-018-009 |
| 15 | T5 | `tests/test_hu_018.py` | `test_tc_018_010_reprogramar_con_datos_invalidos_no_cancela_la_vieja` | TC-018-010 |
| 16 | T5 | `tests/test_hu_018.py` | `test_tc_018_011_misma_fecha_hoy_y_fecha_pasada_permitidas_sin_restriccion_de_tres_horas` | TC-018-011 |
| 17 | T5 | `tests/test_hu_018.py` | `test_tc_018_017_carrera_post_cancelacion_slot_taken_mantiene_cancelacion` | TC-018-017 |
| 18 | T5 | `tests/test_hu_018.py` | `test_tc_018_018_orden_cancelar_antes_de_crear` | TC-018-018 |

## Matriz de trazabilidad RF ↔ Tarea ↔ TC

| TC (sin renumerar) | RF | Tareas | Archivo / evidencia |
|---|---|---|---|
| TC-018-001 | RF-1, RF-8 | T2, T3 | `tests/test_admin_routes.py` :: `test_tc_018_001_…` |
| TC-018-002 | RF-2, RF-8 | T2, T3 | `tests/test_admin_routes.py` :: `test_tc_018_002_…` |
| TC-018-003 | RF-2, RF-8 | T2, T3 | `tests/test_admin_routes.py` :: `test_tc_018_003_…` |
| TC-018-004 | RF-3 | T2, T3 | `tests/test_admin_routes.py` :: `test_tc_018_004_…` |
| TC-018-005 | RF-3, RF-5 | T3, T5 | `tests/test_hu_018.py` :: `test_tc_018_005_…` (filtra `event_type`) |
| TC-018-006 | RF-3, RF-8 | T3, T4 | `tests/test_admin_routes.py` :: `test_tc_018_006_…` |
| TC-018-007 | RF-4, RF-5 | T4, T5 | `tests/test_hu_018.py` :: `test_tc_018_007_…` (filtra `event_type`; enlace) |
| TC-018-008 | RF-5 | T4 | `tests/test_admin_routes.py` :: `test_tc_018_008_…` |
| TC-018-009 | RF-6 | T4, T5 | `tests/test_hu_018.py` :: `test_tc_018_009_…` |
| TC-018-010 | RF-4, RF-6 | T4, T5 | `tests/test_hu_018.py` :: `test_tc_018_010_…` |
| TC-018-011 | RF-9 | T4, T5 | `tests/test_hu_018.py` :: `test_tc_018_011_…` |
| TC-018-012 | RF-7 | T3, T4 | `tests/test_admin_routes.py` :: `test_tc_018_012_…` |
| TC-018-013 | RF-7 | T3 | `tests/test_admin_routes.py` :: `test_tc_018_013_…` |
| TC-018-014 | RNF literales / espejo | T2 | `tests/test_admin_content.py` :: `test_tc_018_014_…` |
| TC-018-015 | RNF constitución #1 | T2 | `tests/test_admin_content.py` :: `test_tc_018_015_…` |
| TC-018-016 | RF-1..RF-9 + RNF (regresión) | T5 | **Corrida completa**: `python -m pytest -q` (no es función) |
| TC-018-017 | RF-6 (carrera post-cancelación) | T4, T5 | `tests/test_hu_018.py` :: `test_tc_018_017_…` |
| TC-018-018 | RF-4, RF-6 (orden cancelar→crear) | T4, T5 | `tests/test_hu_018.py` :: `test_tc_018_018_…` |
| TC-018-019 | RF-7 (refresh/re-POST) | T4 | `tests/test_admin_routes.py` :: `test_tc_018_019_…` |

**Cobertura explícita:** RF-6 en carrera → TC-018-017; RF-8 en reprogramación ya
cancelada → TC-018-006, GET cancelada → TC-018-002, sin fuga de datos →
TC-018-001/003; RF-9 en cancelación de cita pasada → TC-018-011; RF-5 con
enlace de cancelación → TC-018-007; RF-4 con orden cancelar→crear →
TC-018-018.

## Tareas

- [x] **T1. Crear `feature/hu-018` desde `main`, verificar el baseline real y versionar la spec enmendada, la revisión del plan y estas tareas.** RF-1..RF-9 (base y trazabilidad)
  - Alcance: `git status`; `git checkout -b feature/hu-018` desde `main`
    (`9846613`); confirmar `python -m pytest -q` → **302 passed / 0 failed**;
    commitear `specs/018_cancelar-reprogramar-citas/spec.md` (enmienda
    2026-11-05), `plan.md` (revisión 2026-11-05) y `task.md` citando HU-018 /
    Spec 018.
  - Hecho cuando: `git branch --show-current` → `feature/hu-018`;
    `git merge-base --is-ancestor main feature/hu-018` → exit 0;
    `python -m pytest -q` → **302 passed / 0 failed**; `git status` **sin
    cambios tracked pendientes** (los untracked `.opencode/` y
    `.agents/skills/sdd/` quedan fuera de la HU); el commit de docs cita HU-018 /
    Spec 018 e incluye la enmienda de `spec.md`.

- [x] **T2. Crear el espejo en `tests/expected_content.py`, `consultorio/content/admin_content.py` y `Config.CONSULTORIO_ADMIN_TOKEN`, con `tests/test_admin_content.py` (2 funciones).**
  RF-1, RF-2, RF-3, RF-4, RF-5, RF-6, RF-7, RF-8, RNF literales
  - Alcance: **20 constantes** en `admin_content.py` con prefijo `ADMIN_`:
    **14 literales contractuales** de la tabla de la spec 018 (los 13 anteriores
    + `ADMIN_MSG_ALREADY_CANCELLED = "La cita ya estaba cancelada."`, fila «Cita
    ya cancelada» de la enmienda 2026-11-05) + 6 etiquetas funcionales
    («Servicio», «Nueva fecha», «Hora», «Resumen de la cita», «Paciente»,
    «Estado»). Para «Horario no disponible»
    usar el literal contractual de la spec 018:
    `ADMIN_SLOT_TAKEN = "Ese horario ya está ocupado. Elige otro."`; **no
    importar** `appointment_content.MSG_SLOT_TAKEN` (texto distinto).
    `ADMIN_ACCESS_DENIED` y `ADMIN_APPOINTMENT_NOT_FOUND` toman la tabla
    literal. Los estados «Confirmada»/«Cancelada» reutilizan
    `STATUS_CONFIRMED_LABEL`/`STATUS_CANCELLED_LABEL` (no se duplican).
    `Config.CONSULTORIO_ADMIN_TOKEN = os.environ.get("CONSULTORIO_ADMIN_TOKEN", "")`
    en `consultorio/config.py` (mismo patrón que
    `AUTOMATION_WEBHOOK_AUTH_HEADER`). Espejo en `tests/expected_content.py`.
  - Tests (2 funciones, se escriben y ejecutan en esta tarea):
    `test_tc_018_014_…` compara las **14 constantes contractuales** contra la
    tabla de la spec 018 **y** contra `expected_content.py` (incluida «Cita ya
    cancelada»); y compara las **6 etiquetas funcionales** contra el espejo y
    D6. No da por contractual ninguna etiqueta funcional.
    `test_tc_018_015_…` verifica con `ast` que `admin_content.py` solo importa
    stdlib y `consultorio` (sin terceros) y que `requirements.txt` sigue
    conteniendo únicamente `Flask` y `gunicorn`.
  - Hecho cuando: `python -m pytest -q tests/test_admin_content.py -v` →
    **2 passed / 0 failed**; `python -m pytest -q` → **304 passed / 0 failed**.

- [x] **T3. Crear las plantillas y el guard, implementar el blueprint con el guard de token, `GET /admin/citas/<int:cita_id>` y `POST /admin/citas/<int:cita_id>/cancelar`, y escribir los 5 tests de rutas de esta tarea (TC-018-001, 002, 003, 004 y 013).**
  RF-1, RF-2, RF-3, RF-7, RF-8, RNF identidad visual / estados
  - Alcance web: `bp = Blueprint("admin", __name__, url_prefix="/admin")`;
    `_check_token()` con `hmac.compare_digest` sobre bytes, que acepta
    `X-Admin-Token`, `?token=` **solo en GET** y `admin_token` en POST, tolera
    `None`/vacío/no ASCII y devuelve `False` si `CONSULTORIO_ADMIN_TOKEN` está
    vacío. Respuestas admin con `Cache-Control: no-store` y
    `Referrer-Policy: no-referrer`. GET con 403 + `ADMIN_ACCESS_DENIED`, 404 +
    `ADMIN_APPOINTMENT_NOT_FOUND`, o 200 con resumen/formularios; si la cita
    está `cancelled`, muestra «Cancelada» y **sin formularios operativos**.
    POST cancelar: carga la cita (404 si no existe), si ya está `cancelled`
    responde `ADMIN_MSG_ALREADY_CANCELLED` sin llamar al servicio, y si no
    **delega** en `cancel_appointment()` con
    `AUTOMATION_WEBHOOK_URL/TIMEOUT_SECONDS/AUTH_HEADER` (sin lógica propia),
    mapeando éxito → `ADMIN_CANCEL_SUCCESS`, `ALREADY_CANCELLED` →
    `ADMIN_MSG_ALREADY_CANCELLED`, `APPOINTMENT_NOT_FOUND` → 404 + literal.
    Registro único de `admin_bp` en `consultorio/__init__.py`.
  - Alcance de plantillas y guard: `templates/admin/appointment_detail.html`
    con el resumen obligatorio (paciente, servicio, fecha legible, hora,
    estado), el formulario de cancelación (aviso + «Sí, cancelar cita» +
    `admin_token` oculto) y el de reprogramación: `select` de servicios desde
    `SERVICES_CATALOG`, `input type="date"` para la fecha nueva y las **14 horas
    válidas de `BOOKING_HOURS`** (08:00–11:30 y 14:00–16:30), aviso + «Sí,
    reprogramar» + `admin_token` oculto. La vista pasa
    `services=SERVICES_CATALOG` y `booking_hours=BOOKING_HOURS` a la plantilla;
    no se inventan catálogo ni horarios. `templates/admin/result.html` con el
    mensaje de resultado y «Volver» → `/citas`. Ambos heredan `base.html`,
    usan la paleta Serenidad Natural y párrafos justificados. `static/js/admin.js`
    aplica el patrón HU-006 (flag + `preventDefault()` + `disabled` +
    `aria-busy`) a **los dos** formularios. Mapeo D7: disponible, validando,
    procesando, éxito, conflicto y error. Decisión D8: la pantalla es interna
    pero visible; **no se generan capturas 1280/375**; validación funcional
    manual y revisión de paleta/contraste en T6.
  - Tests (5 funciones, se escriben y ejecutan en esta tarea): `TempConfig`
    local con `CONSULTORIO_ADMIN_TOKEN = "test-admin-token"`. TC-018-001 cubre
    token ausente/incorrecto/`None`/no ASCII en GET y POST, config vacía, 403 +
    `ADMIN_ACCESS_DENIED`, cabeceras `no-store`/`no-referrer` y **ningún dato de
    la cita**. TC-018-002 cubre GET con `X-Admin-Token` y con `?token=` → 200
    con paciente, servicio, fecha, hora, estado y ambos formularios; además,
    comprueba que los servicios y las 14 horas provienen de
    `SERVICES_CATALOG`/`BOOKING_HOURS` y que la fecha nueva es un
    `input type="date"`; una cita ya cancelada muestra «Cancelada» y **sin
    formularios operativos**.
    TC-018-003 cubre cita inexistente → 404 + `ADMIN_APPOINTMENT_NOT_FOUND`.
    TC-018-004 cubre POST cancelar con cabecera y con campo oculto → 200 +
    `ADMIN_CANCEL_SUCCESS` y fila `cancelled`. TC-018-013 verifica en el HTML
    el guard RF-7 (script `admin.js`, formularios asociados, botones inicialmente
    habilitados y patrón `disabled`/`aria-busy`).
  - Hecho cuando: `python -m pytest -q tests/test_admin_routes.py -v` →
    **5 passed / 0 failed** (TC-018-001, 002, 003, 004 y 013);
    `python -m pytest -q` → **309 passed / 0 failed**. No se cierra por
    inspección estática: los 5 TC de esta tarea deben estar en verde.

- [ ] **T4. Implementar `POST /admin/citas/<int:cita_id>/reprogramar` y escribir los 4 tests de rutas de esta tarea (TC-018-006, 008, 012 y 019).**
  RF-4, RF-5, RF-6, RF-8, RF-9
  - Alcance web: cargar la cita vieja (404 si no existe); **si `status ==
    cancelled`, responder `ADMIN_MSG_ALREADY_CANCELLED` sin validar, sin
    comprobar hueco y sin cancelar**; construir `data` copiando los 5 campos
    reales del `Appointment` (`document_type`, `document_number`,
    `patient_name`, `email`, `phone`) y tomando `service/date/time` del
    formulario; `validate_booking(data)` con errores → re-render de
    `appointment_detail.html` con errores, **sin cancelar** (la fecha nueva es
    un `input type="date"` y se valida en servidor con las reglas de la Spec
    004; el HTML5 no la sustituye); `repository.is_slot_taken()` del horario
    nuevo → `ADMIN_SLOT_TAKEN`, **sin cancelar**; `cancel_appointment()` de la
    vieja (si devuelve sentinela, parar); `create_booking()` de la nueva **con**
    `cancellation_url_builder=lambda id: url_for("cancellation.verify",
    cita_id=id, _external=True)` (Spec 017 RF-13 / enmienda Spec 008); si
    devuelve `SLOT_TAKEN` por carrera → `ADMIN_SLOT_TAKEN` y la cancelación
    **permanece**; éxito → `ADMIN_RESCHEDULE_SUCCESS_TEMPLATE.format(id=nueva.id)`
    con 200. No se implementa la restricción de 3 horas de la Spec 017 (RF-9).
    Sin lógica de persistencia propia.
  - Tests (4 funciones, se escriben y ejecutan en esta tarea): TC-018-006 cubre
    cancelar cita inexistente (404 + literal), ya cancelada (200 +
    `ADMIN_MSG_ALREADY_CANCELLED`, sin cambios ni eventos nuevos) y
    **reprogramar una cita ya cancelada** (mismo literal, sin validar/cancelar,
    sin cambios ni eventos). TC-018-008 comprueba que el éxito de reprogramación
    contiene el **id real** (`Nueva cita #N`) y los estados vieja `cancelled` /
    nueva `confirmed`. TC-018-012 envía dos POST a cancelar y dos a reprogramar
    y verifica que el segundo no crea otra cita ni emite eventos nuevos
    (filtrado por `event_type`). TC-018-019 hace un segundo POST idéntico
    (refresh/re-POST) y comprueba que **no duplica cita ni eventos** y que el
    comportamiento es seguro (puede mostrar un mensaje distinto del original).
  - Hecho cuando: `python -m pytest -q tests/test_admin_routes.py -v` →
    **9 passed / 0 failed** (los 5 de T3 + los 4 de T4);
    `python -m pytest -q` → **313 passed / 0 failed**. No se cierra por
    inspección estática: los 4 TC de esta tarea deben estar en verde.

- [ ] **T5. Escribir `tests/test_hu_018.py` (TC-018-005, TC-018-007, TC-018-009, TC-018-010, TC-018-011, TC-018-017 y TC-018-018; 7 funciones) y ejecutar la suite completa (TC-018-016).**
  RF-3, RF-4, RF-5, RF-6, RF-9
  - Alcance: receptor de webhook parcheado (`automation_service._post_webhook`) y
    **filtro por `event_type`** en todos los recuentos. TC-018-005: cancelar →
    exactamente 1 POST/evento `appointment.cancellation_email` en `sent` y
    presencia del evento `appointment.cancelled`, sin contarlo a ciegas.
    TC-018-007: reprogramar a horario libre → vieja `cancelled` + nueva
    `confirmed` y exactamente 1 evento `sent` de cada tipo:
    `appointment.cancelled`, `appointment.cancellation_email`,
    `appointment.confirmed`, `appointment.confirmation_email`; además, el
    payload de `appointment.confirmation_email` de la nueva cita contiene el
    enlace `cancellation.verify`. TC-018-009: horario ocupado → `ADMIN_SLOT_TAKEN`
    y vieja **intacta** (`confirmed`), sin cancelar. TC-018-010: fecha pasada y
    fin de semana → errores de validación y vieja **intacta**. TC-018-011:
    cancelar una cita del mismo día y una pasada (RF-9 completo) y reprogramar a
    hoy; aclarar que la **fecha nueva** sigue las reglas de la Spec 004 (una
    fecha nueva pasada/fin de semana se rechaza). TC-018-017: forzar
    `create_booking` a devolver `SLOT_TAKEN` tras cancelar → mensaje de horario
    ocupado, la cita original queda `cancelled`, no se crea otra y no se
    revierte. TC-018-018: verificar con spy/monkeypatch que se llama primero a
    `cancel_appointment` y después a `create_booking`. Para no depender del día
    real, fijar con `monkeypatch` el reloj de `appointment_service.date` a un día
    laborable cuando el caso lo requiera, sin tocar código de producción.
  - Hecho cuando: `python -m pytest -q tests/test_hu_018.py -v` →
    **7 passed / 0 failed**; `python -m pytest -q` → **320 passed / 0 failed**
    (TC-018-016).

- [ ] **T6. Ejecutar la demo manual §6.2 del plan con receptor stdlib local y redactar `docs/evidencias/hu-018/qa-hu-018.md` con PASS/FAIL por TC.**
  RF-1..RF-9, RNF, criterios de finalización
  - Alcance: servidor local con `CONSULTORIO_ADMIN_TOKEN` definido **solo en el
    entorno** (valor local no versionado) y receptor HTTP stdlib (patrón
    HU-010). Demo: reservar desde `/citas` → cancelar desde
    `/admin/citas/<id>` → verificar `appointment.cancelled` +
    `appointment.cancellation_email`; comprobar el borrado del evento de Google
    Calendar por n8n (Spec 007 RF-8); reservar otra → reprogramar con una fecha
    del control `input type="date"` y una hora de `BOOKING_HOURS` → verificar
    vieja `cancelled`, nueva `confirmed` y los cuatro eventos
    (`appointment.cancelled`, `appointment.cancellation_email`,
    `appointment.confirmed`, `appointment.confirmation_email`), con el enlace de
    cancelación en la confirmación; token inválido; horario ocupado; doble clic;
    misma fecha (RF-9); comportamiento del refresh/re-POST. Revisar paleta y
    contraste en la pantalla admin. Informe con **PASS/FAIL por
    TC-018-001..019**, comandos y resultados reales, sin PII ni token real, y
    **checkbox de aceptación sin marcar** (solo la usuaria puede marcarlo). No
    se inventan capturas: D8 decide no generar 1280/375; si se añadieran, usar
    CDP y no `--window-size`.
  - Hecho cuando: existe `docs/evidencias/hu-018/qa-hu-018.md` con los 19 TC y
    su PASS/FAIL, la demo §6.2 registrada (incluidos Calendar/n8n y refresh) y
    el checkbox de aceptación vacío; `python app.py` queda en marcha y la URL de
    revisión se comunica.

- [ ] **T7. Cierre: commits por fase, push de la rama, actualización de `MEMORY.md` y verificación del servidor.**
  RF-1..RF-9, RNF, trazabilidad
  - Alcance: commits por fase citando HU-018 / Spec 018 (spec enmendada +
    plan + task → contenido+espejo+config → plantillas+guard+rutas → tests →
    evidencia);
    push de **`feature/hu-018`** (sin merge a `main`; un push a `main`
    desplegaría en Render y vaciaría la BD); `MEMORY.md` con estado de HU-018,
    baseline **302 → 320**, decisiones D1–D12/Q1/Q2, la enmienda 2026-11-05
    aplicada y el literal opcional de error de persistencia pendiente; sin secretos, token real ni PII.
    Verificar que `python app.py` sigue en marcha.
  - Hecho cuando: `git log --oneline main..feature/hu-018` muestra los commits
    de fase; `git status` **sin cambios tracked pendientes** (los untracked
    `.opencode/` y `.agents/skills/sdd/` quedan fuera); `git rev-parse HEAD` =
    `git rev-parse origin/feature/hu-018`; `MEMORY.md` refleja HU-018, la cifra
    320 y los pendientes; el servidor responde en la URL comunicada.

---

## Pendientes de enmienda de spec (NO ejecutar)

Las enmiendas 1–4 fueron **aplicadas en `spec.md` el 2026-11-05** (ver
«Enmienda 2026-11-05» de la spec). Solo queda la siguiente, que es **opcional**
y hoy **no se implementa**:

1. **[NECESITA APROBACIÓN DE LA USUARIA] Literal de error de persistencia (si
   se adopta).** Propuesta: «No se pudo completar la operación. Inténtalo de
   nuevo.» **No se implementa por defecto**: no hay TC ni constante asociados y
   la cifra objetivo **sigue siendo 320**. Si se aprobara, se añadiría un TC
   condicionado y la cifra se recalcularía.

## Decisiones que la usuaria debe aprobar

- Aprobación del `plan.md` revisado el 2026-11-05 (D1–D12, cifras 302/320,
  horas/fecha del formulario y correcciones de la revisión técnica).
- Aprobación de este `task.md`.
- Opcional: si se adopta el literal de error de persistencia, aprobación del
  texto y del TC adicional (la cifra 320 dejaría de ser la definitiva).
