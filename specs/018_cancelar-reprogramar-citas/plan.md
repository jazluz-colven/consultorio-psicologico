# Plan 018 — Cancelar y reprogramar citas por el consultorio

> Trazabilidad: **HU-018 → Spec 018 (`specs/018_cancelar-reprogramar-citas/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs`.
> Etapa actual: **plan APROBADO (2026-10-13)**. Decisiones de la usuaria:
> modelo **A** (cancelar + reservar nueva, sin reversión), rutas internas propias
> (011/012 intactas), token solo por variable de entorno `CONSULTORIO_ADMIN_TOKEN`
> (Q1 de la spec, 2026-10-13), paciente recibe cancelación + confirmación, sin
> límite de 3 h para el consultorio. Dudas de este plan resueltas en la misma
> aprobación: **Q1 esquema híbrido de entrega del token** y **Q2 literal
> «La cita ya estaba cancelada.»**.
> Baseline esperado en `main`: **204 PASS / 0 FAIL** (HU-010 mergeada 2026-10-13).

---

## 0. Alcance y cobertura

Implementa únicamente la interfaz interna de Spec 018: que el consultorio pueda
**cancelar** una cita (RF-3) o **reprogramarla** (RF-4) desde una superficie web
mínima protegida por token (RF-1), mostrando siempre un **resumen previo**
(RF-2), informando del **nuevo id** y generando las **notificaciones ya
aprobadas** (cancelación de la anterior + confirmación de la nueva) sin
reversión de cancelaciones confirmadas (RF-6), con errores claros, sin doble
envío (RF-7) y sin restricción de antelación (RF-9).

**Lo que NO cambia** (constitución #2, «no reescribir lo que funciona»):

- Firmas y lógica de `cancel_appointment()` y `create_booking()`
  (`consultorio/services/appointment_service.py`) — la interfaz **delega** en
  ellas (constitución #3).
- Specs 011/012 (agenda, solo lectura), 004/005/006 (reserva/disponibilidad),
  007/008/010 (eventos y correos) y 017 (cancelación por el paciente) — sin
  modificaciones.
- Sin dependencias nuevas (constitución #1): solo stdlib
  (`hmac.compare_digest` para el token) + Flask ya usado.

## 1. Requisitos → diseño (matriz RF)

| RF | Diseño | Prueba clave |
|---|---|---|
| RF-1 token | Helper `_check_token()` en el blueprint `admin`; sin token o con token incorrecto → 403 | token ausente, incorrecto, correcto, vacío en config |
| RF-2 resumen | `GET /admin/citas/<id>` con paciente/servicio/fecha/hora/estado + formularios | contiene datos y estados |
| RF-3 cancelar | `POST /admin/citas/<id>/cancelar` → `cancel_appointment()` | estado cancelled + evento `cancellation_email` |
| RF-4 reprogramar | `POST /admin/citas/<id>/reprogramar` → cancel + `create_booking()` | vieja cancelled + nueva confirmed |
| RF-5 nuevo id + correos | literal «Cita reprogramada. Nueva cita #{id}.» | id correcto + eventos `confirmed`, `confirmation_email`, `cancellation_email` |
| RF-6 sin reversión | validación e `is_slot_taken` **antes** de cancelar; carrera → mensaje, cancelación permanece | horario ocupado y carrera simulada |
| RF-7 doble envío | mismo patrón de guard de HU-006 en ambos formularios | patrón presente; segundo envío → sentinela, sin doble correo |
| RF-8 errores | literales propios: no encontrada, ya cancelada, acceso denegado | 404/403 + textos |
| RF-9 sin 3 h | sin código extra: solo la **fecha nueva** se valida con las reglas existentes | misma fecha (hoy) permitida al consultorio |

## 2. Decisiones técnicas

- **D1 — Superficie**: blueprint nuevo `admin` en `consultorio/web/admin.py`
  (`url_prefix="/admin"`), 3 rutas; registro con una línea en `create_app()`:

| Método | Ruta | Comportamiento | Éxito |
|---|---|---|---|
| GET | `/admin/citas/<int:cita_id>` | resumen + formularios cancelar/reprogramar (RF-2) | 200; 404 si no existe; 403 si token inválido |
| POST | `/admin/citas/<int:cita_id>/cancelar` | `cancel_appointment()` | 200 con «Cita cancelada.» |
| POST | `/admin/citas/<int:cita_id>/reprogramar` | cancel + `create_booking()` | 200 con «Cita reprogramada. Nueva cita #{id}.» |

  Los POST renderizan el resultado directamente (200). Un refresh repite el
  POST: el servicio es idempotente (`ALREADY_CANCELLED` → mensaje, sin segundo
  correo) y el guard RF-7 minimiza el caso.

- **D2 — Entrega del token** (Q1 aprobada): sin sesiones/cookies en el sitio →
  **cada request porta el token**:
  - GET: cabecera `X-Admin-Token` **y**, como alternativa para navegador sin JS,
    query `?token=...`;
  - POST: campo oculto `admin_token` en el formulario **y** acepta también la
    cabecera (tests/scripts);
  - comparación con `hmac.compare_digest` (constante en tiempo);
  - `CONSULTORIO_ADMIN_TOKEN` vacío en config → **todas** las rutas responden
    403 (funcionalidad desactivada por defecto, seguro en Render sin
    configurar);
  - el token nunca se loguea ni aparece en plantillas salvo el campo oculto.

- **D3 — Flujo cancelar**: token OK → cargar cita (`None` → «No encontramos
  esa cita. Revisa la referencia.», 404) →
  `cancel_appointment(id, db, AUTOMATION_*)` con la config de la app → éxito:
  «Cita cancelada.»; `ALREADY_CANCELLED`: «La cita ya estaba cancelada.»
  (literal Q2); `APPOINTMENT_NOT_FOUND`: literal de no encontrada.

- **D4 — Flujo reprogramar** (orden para minimizar daño, RF-6):
  1. cargar cita vieja (guard);
  2. construir `data` nuevo = datos del paciente copiados de la cita +
     `service/date/time` del formulario (D5);
  3. `validate_booking(data)` → errores → re-render del formulario con
     errores, **sin cancelar nada**;
  4. `is_slot_taken()` → ocupado → «Ese horario ya está ocupado. Elige otro.»
     (reutiliza `MSG_SLOT_TAKEN`), **sin cancelar nada**;
  5. `cancel_appointment(vieja)` → si falla, se para (nada nuevo creado);
  6. `create_booking(data)` → `SLOT_TAKEN` por carrera → mismo mensaje (la
     **cancelación permanece**, nunca se revierte); éxito → «Cita
     reprogramada. Nueva cita #{id}.» + eventos heredados (`confirmed`,
     `confirmation_email`, `cancellation_email`).

- **D5 — Datos del paciente**: la nueva cita copia `patient_full_name`,
  `patient_document_number`, `patient_email`, `patient_phone` de la vieja; el
  formulario interno **solo** pide servicio/fecha/hora nuevos. Ningún dato
  personal en URLs, mensajes ni logs.

- **D6 — Contenido**: módulo nuevo `consultorio/content/admin_content.py` con
  los literales contractuales de la spec 018 (tabla de textos) **más** estos
  literales funcionales (Q2 aprobado):
  - `MSG_ALREADY_CANCELLED = "La cita ya estaba cancelada."`
  - etiquetas de formulario: «Servicio», «Nueva fecha», «Hora», «Resumen de la
    cita», «Paciente», «Estado»;
  - «Acceso denegado» reutiliza el literal de la tabla; `MSG_SLOT_TAKEN` se
    **importa** de `appointment_content` (texto idéntico, cero duplicación);
  - espejo obligatorio en `tests/expected_content.py`.

- **D7 — Guard de doble envío** (RF-7): mismo patrón de HU-006 (atributo de
  estado + listener de `submit` en JS) aplicado a los dos formularios del
  resumen; JS mínimo en el propio template o archivo pequeño en `static/js/`.

- **D8 — Templates**: `templates/admin/appointment_detail.html` (resumen +
  formularios) y `templates/admin/result.html` (resultado con «Volver» →
  `/citas`); heredan `base.html`, paleta Serenidad Natural, texto justificado,
  foco visible. Sin capturas 1280/375 (fuera de alcance, no es visible).

- **D9 — Config**: `Config.CONSULTORIO_ADMIN_TOKEN =
  os.environ.get("CONSULTORIO_ADMIN_TOKEN", "")` (mismo patrón de secreto que
  `AUTOMATION_WEBHOOK_AUTH_HEADER`). Tests: valor fijo de prueba
  (`"test-admin-token"`) en un `TempConfig` local — nunca el token real.

- **D10 — Blueprints intactos**: registro único del `admin_bp` en
  `consultorio/__init__.py`; rutas de 011/012 no existen y no se tocan.

- **D11 — Rama y baseline**: `feature/hu-018` desde `main` (con HU-010
  mergeada); baseline **204 PASS / 0 FAIL**.

- **D12 — Sin PII en logs**: los handlers no loguean datos de pacientes ni el
  token (constitución #6).

## 3. Algoritmo (pseudocódigo de los handlers)

```text
_check_token(app_config, request):
    expected = config["CONSULTORIO_ADMIN_TOKEN"]; if not expected → False
    given = header "X-Admin-Token" o form "admin_token" o args "token"
    return hmac.compare_digest(given, expected)

GET /admin/citas/<id>:
    token inválido → plantilla acceso denegado (403)
    cita = get_appointment_by_id(); None → plantilla no encontrada (404)
    → resumen + formularios (cancelar siempre visible; reprogramar con
      select de servicios, date y time)

POST /admin/citas/<id>/cancelar:
    guards token + cita → cancel_appointment(id, db, AUTOMATION_*)
    éxito | APPOINTMENT_NOT_FOUND | ALREADY_CANCELLED → result.html (200)

POST /admin/citas/<id>/reprogramar:
    guards token + cita vieja
    data = copia paciente + form (service, date, time)
    validate_booking(data) con errores → detail.html con errores (200)
    is_slot_taken → MSG_SLOT_TAKEN (200)
    r = cancel_appointment(vieja); si sentinela → error (200)
    n = create_booking(data); SLOT_TAKEN → MSG_SLOT_TAKEN (200, la
        cancelación de la cita anterior se mantiene); éxito → «Cita
        reprogramada. Nueva cita #{n.id}.» (200)
```

Config de automación heredada: `AUTOMATION_WEBHOOK_URL`,
`AUTOMATION_TIMEOUT_SECONDS`, `AUTOMATION_WEBHOOK_AUTH_HEADER` — pasadas igual
que en `consultorio/web/appointments.py:129-131`.

## 4. Comandos

```powershell
git status                         # rama y estado
git checkout -b feature/hu-018     # desde main (204 PASS)
python -m pytest -q                # suite completa por fase
python app.py                      # servidor de revisión (http://127.0.0.1:5000)
```

## 5. Fuera de alcance (spec + D13)

Login/sesiones/roles; agenda diaria (011/012); cancelación/reprogramación por
el paciente (017); `initiated_by` en BD; WhatsApp (009); historial de
reprogramaciones pasadas; reintentos; panel de envíos; cambios en servicios
existentes.

## 6. Estrategia de tests

**6.1 Matriz** (números fijos en `task.md`; archivos nuevos:
`tests/test_admin_routes.py`, `tests/test_hu_018.py`, `tests/test_admin_content.py`):

| TC | Qué | Resultado esperado |
|---|---|---|
| TC-018-001 | GET detalle sin token / token incorrecto / vacío en config | 403 + «No tienes acceso…» |
| TC-018-002 | GET detalle con token correcto (cabecera y query) | 200 con resumen y estados |
| TC-018-003 | GET detalle de cita inexistente | 404 + literal |
| TC-018-004 | POST cancelar con token en cabecera y en campo oculto | 200 «Cita cancelada.», estado cancelled |
| TC-018-005 | Cancelar genera evento `appointment.cancellation_email` | 1 evento `sent` |
| TC-018-006 | Cancelar cita inexistente / ya cancelada | literales correspondientes |
| TC-018-007 | Reprogramar a horario libre | vieja cancelled + nueva confirmed; eventos `confirmed` + `confirmation_email` + `cancellation_email` |
| TC-018-008 | Literal de éxito con el id correcto | «Nueva cita #N» con N real |
| TC-018-009 | Reprogramar a horario ocupado | `MSG_SLOT_TAKEN`; **vieja intacta** (RF-6) |
| TC-018-010 | Reprogramar con datos nuevos inválidos (fecha pasada/fin de semana) | errores; **vieja intacta** |
| TC-018-011 | Misma fecha hoy sin antelación (RF-9) | permitido al consultorio |
| TC-018-012 | Doble envío: segundo POST cancelar/reprogramar | sentinela, sin segundo correo |
| TC-018-013 | Guard RF-7 presente en el HTML | patrón verificable |
| TC-018-014 | Espejo: literales admin en `expected_content.py` | iguales a `admin_content` |
| TC-018-015 | Constitución #1: sin dependencias nuevas | import check |
| TC-018-016 | Regresión completa | ≥204 previos intactos |

**6.2 Demo manual** (receptor stdlib local, patrón HU-010): reservar cita
pública → cancelar desde `/admin/citas/<id>` → verificar `cancellation_email`
→ reservar otra → reprogramar → verificar `cancellation_email` + `confirmed` +
`confirmation_email` → token inválido → horario ocupado → doble clic.

**6.3 QA**: `docs/evidencias/hu-018/qa-hu-018.md` con PASS/FAIL por TC,
captura del flujo si aplica y checkbox de aceptación.

## 7. Aprobación y dudas

### 7.1 Dudas

- **[RESUELTA — Q1]** Entrega del token (D2): esquema híbrido aprobado —
  cabecera `X-Admin-Token` para scripts/tests + campo oculto `admin_token` para
  los formularios + `?token=` como alternativa de navegador (2026-10-13).
- **[RESUELTA — Q2]** Literal nuevo (D6): «La cita ya estaba cancelada.» para
  el caso de doble cancelación — **aprobado** (2026-10-13).

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Aprobación de este `plan.md` (alcance, matriz RF, D1–D13, Q1/Q2) por la
      usuaria — **aprobado 2026-10-13 («Apruebo el plan»)**.
- [ ] Creación de `feature/hu-018` desde `main` (D11) y verificación del
      baseline **204 PASS / 0 FAIL**.
- [ ] Espejo + `admin_content` + `Config.CONSULTORIO_ADMIN_TOKEN`.
- [ ] Blueprint `admin` + templates + guard de doble envío + registro en
      `create_app()`.
- [ ] Tests §6 en verde: objetivo **~220 PASS / 0 FAIL** con los 204 previos
      intactos (cifra exacta fijada en `task.md`).
- [ ] Demo manual §6.2 + evidencia en `docs/evidencias/hu-018/`.
- [ ] Informe QA `qa-hu-018.md` con PASS/FAIL por TC y checkbox de aceptación.
- [ ] Commit/Push por fases, `MEMORY.md` y aceptación de la HU.
- [ ] Servidor de revisión en marcha (AGENTS.md) y URL comunicada.

---

## 8. Secuencia de implementación

0. **Aprobación de este plan** (incl. Q1 y Q2) — **cumplida 2026-10-13**.
1. **Rama**: `feature/hu-018` desde `main`, verificar baseline **204 PASS**.
2. **Espejo**: `tests/expected_content.py` con los literales de §2.2/D6.
3. **Contenido**: `admin_content.py`.
4. **Config**: `Config.CONSULTORIO_ADMIN_TOKEN`.
5. **Web**: blueprint `admin` + `appointment_detail`/`result` + guard +
   registro en `create_app()`.
6. **Tests**: TC-018-001…015 → suite completa (TC-018-016, ~220 PASS).
7. **Demo manual** §6.2 + evidencia.
8. **QA** `qa-hu-018.md` + aceptación de la usuaria.
9. **Commits por fase** + push + `MEMORY.md`.
10. **Servidor de revisión** en marcha y URL comunicada.
