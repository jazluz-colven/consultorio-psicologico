# Informe QA — HU-017 / Spec 017: Cancelar una cita por parte del paciente

**Tarea:** T10 — Evidencia QA y demo manual de los criterios de finalización
(`specs/017_cancelar-cita-paciente/tasks.md`).
**Fecha (pasada 1 — CDP):** 2026-10-26 (19:35–19:50, hora local).
**Fecha (pasada 2 — cierre de T10, canal real n8n):** 2026-10-30.
**Rama:** `feature/hu-017` · **HEAD:** `83babda7f7151fa69a5a53db4167f0bc7ef5c35c`
(`test(cancellation): cobertura TC-017-001..013 y regresion completa`). Sin cambios
versionados de código entre ambas pasadas (`consultorio/`, `templates/`, `static/`,
`tests/` y `specs/017_*` sin modificaciones; `tests/demo_reprocess.py` sigue sin
seguimiento y es ajeno a esta revisión).
**Especificación:** `specs/017_cancelar-cita-paciente/spec.md` (aprobada 2026-10-13).
**Plan:** `specs/017_cancelar-cita-paciente/plan.md` (§5 rutas, §6 matriz de pruebas,
§7 trazabilidad).
**Entorno de ejecución (pasada 1):** Windows, Python 3.14 del sistema
(`C:\Python314\python.exe`), Flask en **http://127.0.0.1:5000** (pid **8700**,
`python app.py`, sin reiniciar durante la validación), SQLite `data/consultorio.db`.
El estado del servidor al **cierre de T10** se registra en *Estado del entorno al
cierre*.
**Automatización:** en la **pasada 1 (CDP, entorno de QA)** `AUTOMATION_WEBHOOK_URL`
estaba **vacía**: los eventos de `automation_events` se registraron como `skipped`
(«Automatización no configurada.» / «Envío de correo no configurado.»). En la
**pasada 2 (cierre)**, la usuaria ejecutó la prueba E2E en **su** entorno con el webhook
de n8n configurado. Esa evidencia se registra en *n8n — prueba E2E en canal real* y fue
**corroborada por QA con una consulta de solo lectura** a `data/consultorio.db`; QA no
configuró el webhook, no repitió la prueba y no modificó datos.
**Rol:** QA independiente (revisor). No se modificó código, plantillas, CSS, JS,
servicios, pruebas ni `specs/**`. Los únicos archivos escritos por esta revisión son
los de `docs/evidencias/hu-017/`.

**Método de validación de interfaz:** el MCP de Chrome DevTools **no estaba disponible
en la sesión** (limitación L-1). Con autorización expresa de la usuaria se usó la ruta
alternativa **CDP directo**: Chrome 156.0.8078.48 headless, puerto 9222, perfil aislado
en `%TEMP%\opencode\hu017-t10\profile`, cliente WebSocket propio que registra
`consoleAPICalled`, `exceptionThrown`, `Log.entryAdded`, red (`Network.*`, incluidos
`redirectResponse`), viewport con `Emulation.setDeviceMetricsOverride` (1280×900 y
375×812) y capturas `Page.captureScreenshot` de página completa. Los formularios se
enviaron con clicks reales (`Input.dispatchMouseEvent`), no con `fetch()` inyectado.
La instancia de Chrome de QA (pid 10388) se cerró al finalizar.

---

## Veredicto

**VEREDICTO: APROBADO.**

Alcance obligatorio revisado y con evidencia suficiente: RF-1..RF-13 (ver *Matriz de
validación RF por RF*), TC-017-001..014 y los criterios de finalización de la spec.
La pasada 1 cubrió el flujo funcional en navegador (CDP) y la suite automatizada; la
pasada 2 cerró el único criterio que quedaba pendiente: el **envío real por el canal
n8n** (RF-8; cita `#29` con **4/4** eventos `sent`) y la **apertura del enlace desde el
correo real** (RF-13 E2E; cancelación completada desde la página abierta desde el
cliente de correo). **No se detectaron defectos bloqueantes de HU-017** en el alcance
revisado.

Queda **fuera de este veredicto** el defecto `D-010-01` (un 4xx/5xx real se registra
como «Servicio de automatización no disponible.»), registrado por separado y gestionado
como defecto de la **Spec 010**. Se documenta aquí solo como **riesgo conocido** (ver
*Riesgo conocido fuera de alcance: D-010-01*) y **no bloquea** la aceptación de HU-017.

La **aceptación funcional** de la HU corresponde a la usuaria y no se presume por este
informe técnico.

---

## Criterios de aceptación (checkboxes)

- [x] **RF-1/RF-2** — Verificación de referencia + documento antes de cualquier cambio;
      mensaje uniforme y sin datos de la cita (referencia inexistente, documento
      incorrecto, documento vacío o con formato inválido; id no numérico → 404).
- [x] **RF-3** — Pantalla de resumen con servicio, fecha legible, hora y estado antes
      de cancelar; la cita sigue `confirmed` en BD.
- [x] **RF-4** — Restricción de 3 h (cita próxima, hora ya iniciada/pasada y borde
      < 3 h) sin cambios en BD; borde ≥ 3 h permite continuar.
- [x] **RF-5** — La confirmación cancela mediante el servicio de la Spec 010
      (delegación verificada por `pytest`), sin lógica propia.
- [x] **RF-6** — El horario vuelve a ofrecerse en `/citas/horarios` y puede reservarse
      de nuevo.
- [x] **RF-7** — Pantalla de éxito con «Cita cancelada», mensaje literal, estado
      «Cancelada», datos y referencia.
- [x] **RF-8** — Notificación de cancelación sin duplicar al reintentar. En **canal
      real** (cita `#29`): exactamente **1** `appointment.cancelled` (`sent`,
      00:29:57) y **1** `appointment.cancellation_email` (`sent`, 00:29:58), **0**
      duplicados; la usuaria recibió el correo de cancelación. Deduplicación al
      reintentar: 1 sola fila por cita y `test_tc_017_005_*`.
- [x] **RF-9** — Reintento/recarga: «Esta cita ya fue cancelada.», sin segunda
      cancelación ni segunda notificación.
- [x] **RF-10** — Guard de doble envío (botón `disabled` + `aria-busy`, un solo POST)
      ante doble clic real.
- [x] **RF-11** — `/citas/confirmada/<id>` de una cita cancelada muestra «Cancelada» y
      **sin** botón de cancelar.
- [x] **RF-12** — `/citas/confirmada/<id>` de una cita confirmada muestra el botón
      «Cancelar cita» que inicia el flujo.
- [x] **RF-13** — El payload de `appointment.confirmation_email` contiene el enlace
      absoluto `…/citas/cancelar/<id>` en texto y HTML (prueba automatizada) y la
      usuaria **abrió el enlace desde el correo real recibido** en su cliente de correo,
      completando la cancelación desde esa página (**E2E**).
- [x] **TC-017-005** — Notificación de la cancelación en **canal real**: **4/4** eventos
      `sent` en la cita `#29`, 1 fila por `event_id`, 0 duplicados y correo de
      cancelación recibido (ver *n8n — prueba E2E en canal real*).
- [x] **TC-017-013** — Regresión: `python -m pytest -q` → **283 passed**, 0 FAIL
      (re-ejecutada al cierre: 36.22 s).
- [x] **TC-017-014** — Demo E2E completa, **incluida la parte n8n**: reserva → correo
      real → apertura del enlace desde el cliente de correo → verificación con
      documento → resumen → «Cancelada» → hueco libre → re-reserva → correo de
      notificación.
- [ ] **Aceptación funcional de la usuaria** (fuera del alcance del QA técnico).

---

## Resumen de pruebas

| Prueba | Comando / método | Resultado |
|---|---|---|
| Suite completa (regresión, pasada 1) | `python -m pytest -q` | **283 passed in 23.09s**, 0 FAIL |
| Suite completa (re-ejecución de cierre, pasada 2) | `python -m pytest -q` (HEAD `83babda`, 2026-10-30) | **283 passed in 36.22s**, 0 FAIL |
| E2E n8n en canal real | Prueba manual de la usuaria; estado verificado por QA con consulta de solo lectura | **4/4 eventos `sent`** en `#29`; correos de confirmación y cancelación recibidos; enlace abierto desde el cliente de correo |
| Reproceso de evento `failed` (Spec 010, 2B/T27) | Reproceso real sobre `appointment.cancelled:28:v1` | **`sent`** (2026-10-30 00:38:58), misma fila, `detail` limpiado |
| Escenarios funcionales en navegador | Harness CDP (`log-book`, `log-flow`, `log-restrict`, `log-dbl`) | **19/19 PASS** |
| Consola JS | `Runtime.consoleAPICalled` + `Runtime.exceptionThrown` | 0 mensajes, 0 excepciones |
| Log del navegador | `Log.entryAdded` | 1 error, **intencional**: 404 de `/citas/cancelar/abc` |
| Red | `Network.responseReceived` / `redirectResponse` | 303 y 200 esperados; **ningún 5xx**; 0 peticiones fallidas |
| Imágenes | `naturalWidth === 0` en la página | 0 imágenes rotas |
| Desbordamiento horizontal | `document.scrollWidth` vs `innerWidth` por contenedor | 0 desbordes en 1280 y 375 |
| Literales contractuales | `pytest` (espejo `tests/expected_content.py`) | En verde |

---

## Matriz de validación RF por RF

| RF | Criterio comprobado | Evidencia | Veredicto |
|---|---|---|---|
| RF-1 | Verifica referencia + documento antes de cambiar nada | Escenarios 1–6: `#17` permanece `confirmed` hasta la confirmación; POST fallidos con `0` cambios (`log-flow.json`); `tests/test_hu_017.py::test_tc_017_001_*` | CUMPLE |
| RF-2 | Mensaje uniforme en español y sin datos de la cita | Referencia `999999` y documento `11111111` → mismo literal «No pudimos verificar tu cita. Revisa los datos e inténtalo de nuevo.»; `leaks = []` (sin nombre/correo/celular/documento/servicio/fecha); vacío → literal de servidor; formato `12` → literal de formato; `abc` → 404 | CUMPLE |
| RF-3 | Resumen (servicio, fecha legible, hora, estado) antes de cancelar | Escenario 6: filas `Servicio / Fecha / Hora / Estado` = `Psicología Integral / viernes, 30 de octubre de 2026 / 15:30 / Confirmada`; documento solo en `input[type=hidden]` (`bodyContainsDocument = false`); BD sin cambios | CUMPLE |
| RF-4 | Sin cancelación a < 3 h (próxima, iniciada, pasada) y borde ≥ 3 h permitido | R1 (`#19`, 1 h 51 min) y R2 (`#20`, hora pasada) → literal de restricción, `cancelled_rows = 0`; R3 (`#24`, +3 h 05 min) → resumen sin cambios; R4 (`#22`, < 3 h) → rechazo; unidad: borde exacto 3 h permitido, 2 h 59 min / iniciada / pasada → `TOO_SOON` (`test_cancellation_flow_service.py`) | CUMPLE |
| RF-5 | Cancela delegando en el servicio de la Spec 010, sin segunda lógica | POST `/confirmar` → **303** a `/citas/cancelar/17/exito`; BD `cancelled`; `test_tc_017_011_*` (sin UPDATE/transiciones propias en `cancellation_flow_service`) | CUMPLE |
| RF-6 | Hueco liberado y re-reservable | `/citas/horarios?service=psychology_integral&date=2026-10-30` ofrece de nuevo `15:30` (`occupied = []`); re-reserva por UI → 303 a `/citas/confirmada/18` | CUMPLE |
| RF-7 | Éxito con «Cita cancelada», estado «Cancelada», datos y referencia | Escenario 8 + captura `qa-hu-017-exito-1280.png` / `-375.png`: título «Cita cancelada», mensaje literal, filas Servicio/Fecha/Hora/Estado/Referencia (`#17`) | CUMPLE |
| RF-8 | Notificación de cancelación sin duplicar al reintentar | **Canal real** (cita `#29`): 1 `appointment.cancelled` (`sent`, 00:29:57) + 1 `appointment.cancellation_email` (`sent`, 00:29:58), 0 duplicados; correo de cancelación recibido por la usuaria. Deduplicación: 1 sola fila por cita (`#17`, `#26`, pasada 1) y `test_tc_017_005_*` (1 POST; webhook caído → `failed` con cancelación intacta) | CUMPLE |
| RF-9 | Reintento indica «ya cancelada» sin segunda cancelación/notificación | Escenario 12: POST `/confirmar` y POST de verificación → 200 «Esta cita ya fue cancelada.», sin 303, `cancelled_rows = 0` adicionales, 1 sola fila de notificación | CUMPLE |
| RF-10 | Evita doble envío | Doble clic real con `Fetch.enable`: 1 solo POST a `/confirmar`, `observedDom = {disabled:true, buttonAriaBusy:"true", formAriaBusy:"true"}`, `navToSuccess = 1`, 1 cancelación y 1 evento de correo | CUMPLE |
| RF-11 | Página de cita cancelada muestra «Cancelada» | Escenario 9 + `qa-hu-017-confirmacion-cancelada-1280.png` / `-375.png`: estado «Cancelada», `cancelLink = false`, sin botón | CUMPLE |
| RF-12 | Página de cita confirmada muestra botón «Cancelar cita» | Escenario 7 (vuelta a `/citas/confirmada/17` con enlace de cancelación) y `qa-hu-017-re-reserva-confirmada-1280.png` (`#18`, «Confirmada» + botón «Cancelar cita») | CUMPLE |
| RF-13 | Enlace de cancelación en el correo de confirmación | `test_tc_017_009_*`: texto y HTML contienen `…/citas/cancelar/<id>` con etiqueta «Cancelar cita»; `test_hu_008.py` sin modificar y en verde; **E2E**: la usuaria abrió el enlace desde el correo real recibido y completó la cancelación desde esa página | CUMPLE |

---

## Matriz PASS/FAIL por TC (plan §6)

| TC | RF | Resultado | Evidencia |
|---|---|---|---|
| TC-017-001 | RF-1, RF-2 | **PASS** | Escenarios 1–5 (CDP) + `test_tc_017_001_*` |
| TC-017-002 | RF-3 | **PASS** | Escenario 6 + `test_tc_017_002_*` |
| TC-017-003 | RF-4 | **PASS** | R1–R4 (CDP) + `test_tc_017_003_*` (unidad con `now` fijo) |
| TC-017-004 | RF-5, RF-6, RF-7 | **PASS** | Escenarios 8, 10, 11 + `test_tc_017_004_*` |
| TC-017-005 | RF-8 | **PASS** | **Canal real** (cita `#29`): 4/4 eventos `sent`, 1 fila por `event_id`, 0 duplicados; `test_tc_017_005_*` con `_post_webhook` simulado (`sent`, 1 POST; caído → `failed` y cancelación intacta) |
| TC-017-006 | RF-9 | **PASS** | Escenario 12 + `test_tc_017_006_*` |
| TC-017-007 | RF-10 | **PASS** | Escenario doble envío (CDP) + `test_tc_017_007_*` |
| TC-017-008 | RF-11, RF-12 | **PASS** | Escenarios 7 y 9 + `test_tc_017_008_*` (incluye id desconocido → 404) |
| TC-017-009 | RF-13 | **PASS** | `test_tc_017_009_*` (texto + HTML, enlace absoluto) y **E2E**: apertura del enlace desde el correo real y cancelación completada desde esa página |
| TC-017-010 | RNF claridad | **PASS** | `tests/test_cancellation_content.py` en verde (11 literales + etiquetas) |
| TC-017-011 | Constitución #1/#3 | **PASS** | `test_tc_017_011_*`; sin dependencias nuevas |
| TC-017-012 | RNF estados UX | **PASS** | Estados del botón observados en vivo + literales de mensajes comprobados uno a uno |
| TC-017-013 | Regresión | **PASS** | `python -m pytest -q` → 283 passed, 0 FAIL |
| TC-017-014 | Criterios de finalización | **PASS** | Demo completa, incluida la parte n8n (ver *n8n — prueba E2E en canal real*) |

---

## Escenarios ejecutados (CDP, 1280×900 y 375×812)

Datos **ficticios**; ninguna persona real. La cita guía del flujo es `#17`
(documento `00000010`, Psicología Integral, 2026-10-30 15:30, paciente «Paciente QA
Final», `qa.final@example.test`).

| # | Escenario | Resultado | Evidencia / captura |
|---|---|---|---|
| 1 | Reserva real por UI (servicio + calendario + hora + datos) | PASS — formulario completo antes de enviar; **303** a `/citas/confirmada/13`/`15`/`17` | `qa-hu-017-formulario-reserva-1280.png`, `qa-hu-017-confirmacion-inicial-1280.png` / `-375.png` |
| 2 | `GET /citas/cancelar/17` (formulario de verificación) | PASS — 200; título «Cancelar cita», aviso previo, «Referencia de la cita: #17», «Número de documento», botón «Cancelar cita» | `qa-hu-017-verificacion-1280.png` / `-375.png` |
| 3 | Referencia inexistente (`999999`) | PASS — 200, literal uniforme, sin fugas | `qa-hu-017-error-referencia-inexistente-1280.png` |
| 4 | Documento incorrecto (`11111111`) | PASS — mismo literal, `sameAsNonexistent = true`, sin datos | `qa-hu-017-error-documento-incorrecto-1280.png` |
| 5 | Documento vacío | PASS — validación nativa (`checkValidity() = false`, «Completa este campo»); forzando `form.submit()` → «Ingresa el número de documento.» | `qa-hu-017-error-documento-vacio-1280.png` |
| 6 | Documento con formato inválido (`12`) | PASS — «El número de documento debe tener entre 4 y 20 dígitos.» | `qa-hu-017-error-documento-formato-1280.png` |
| 7 | Referencia no numérica (`/citas/cancelar/abc`) | PASS — **404** «Página no encontrada» | `qa-hu-017-referencia-no-numerica-404-1280.png` |
| 8 | Verificación correcta → resumen | PASS — 4 filas correctas; documento solo oculto; botones «Sí, cancelar mi cita» / «No, volver» | `qa-hu-017-resumen-1280.png` / `-375.png` |
| 9 | «No, volver» | PASS — vuelve a `/citas/confirmada/17` con estado «Confirmada» y enlace de cancelación; sin cancelar | `qa-hu-017-no-volver-confirmada-1280.png` |
| 10 | Confirmación (POST) | PASS — **303** a `/citas/cancelar/17/exito`; título «Cita cancelada», mensaje literal, estado «Cancelada», referencia `#17` | `qa-hu-017-exito-1280.png` / `-375.png` |
| 11 | `/citas/confirmada/17` tras cancelar | PASS — «Cancelada», sin botón de cancelación | `qa-hu-017-confirmacion-cancelada-1280.png` / `-375.png` |
| 12 | Hueco liberado en `/citas/horarios` (2026-10-30) | PASS — `15:30` vuelve a ofrecerse; `occupied = []` | `log-flow.json` (escenario RF-6) |
| 13 | Re-reserva del hueco | PASS — reserva por UI → **303** a `/citas/confirmada/18` («Confirmada» + botón «Cancelar cita») | `qa-hu-017-re-reserva-confirmada-1280.png` |
| 14 | Reintento de la cancelación de `#17` | PASS — POST `/confirmar` y POST de verificación → 200 «Esta cita ya fue cancelada.», sin 303 ni segunda cancelación | `qa-hu-017-reintento-ya-cancelada-1280.png` |
| 15 | Restricción 3 h — cita próxima (`#19`, 21:41; ahora 19:50) | PASS — literal de restricción, `confirmed`, `cancelled_rows = 0` | `qa-hu-017-restriccion-3h-1280.png` / `-375.png` |
| 16 | Restricción 3 h — hora ya iniciada/pasada (`#20`, 18:41) | PASS — mismo literal, sin cambios | `qa-hu-017-restriccion-3h-iniciada-1280.png` |
| 17 | Borde ≥ 3 h (`#24`, 22:51; +3 h 05 min) | PASS — resumen alcanzado, `confirmed`, sin cambios | `qa-hu-017-borde-3h-resumen-1280.png` |
| 18 | Borde < 3 h (`#22`, 22:39) | PASS — rechazo con literal, sin resumen ni cambios | `qa-hu-017-borde-3h-rechazado-1280.png` |
| 19 | Doble envío real sobre `#26` (2026-10-29 14:00) | PASS — 1 solo POST, botón `disabled` + `aria-busy`, 1 cancelación, 1 evento de correo | `qa-hu-017-doble-envio-exito-1280.png` |

**Total: 19/19 PASS.** Capturas: **25 PNG** en esta carpeta
(`qa-hu-017-<escenario>-<viewport>.png`).

---

## n8n — prueba E2E en canal real

**Procedencia de la evidencia.** La prueba la ejecutó la **usuaria** en su entorno, con
el workflow `HU-007 - Integración de citas con n8n` y el webhook configurado. QA **no**
configuró el webhook, no repitió la prueba y no modificó datos: verificó el estado
persistido con una **consulta de solo lectura** a `data/consultorio.db` (2026-10-30) y
contrastó los valores con los aportados por la usuaria. Las horas son las registradas en
`automation_events.sent_at`.

### Causa raíz del rechazo inicial (cita `#28`)

- El nodo `Validar evento` **aceptaba** el payload: contrato de RF-9 conforme —
  **10/10** campos obligatorios presentes, **0** prohibidos, **0** extra.
- El nodo Switch `Enrutar por tipo de evento` **no tenía la rama `appointment.cancelled`**:
  el evento caía en el fallback `extra` → `Responder evento invalido` (**HTTP 400**).
- La usuaria **corrigió el workflow** y repitió la prueba.

> **Trazabilidad:** el workflow de n8n vive **fuera** de este repositorio y no hay
> artefacto versionado de la corrección. La evidencia disponible es el estado real de
> `automation_events` (corroborado por QA) y la prueba funcional descrita.

### Cita `#29` — 4/4 eventos `sent`

Cita `#29` (`nutrition`, 2026-10-30 14:30, estado `cancelled`).

| # | `event_id` | `status` | `sent_at` |
|---|---|---|---|
| 1 | `appointment.confirmed:29:v1` | `sent` | 2026-10-30 00:28:15 |
| 2 | `appointment.confirmation_email:29:v1` | `sent` | 2026-10-30 00:28:16 |
| 3 | `appointment.cancelled:29:v1` | `sent` | 2026-10-30 00:29:57 |
| 4 | `appointment.cancellation_email:29:v1` | `sent` | 2026-10-30 00:29:58 |

- **Correos reales recibidos por la usuaria:** confirmación y cancelación.
- **Enlace del correo abierto desde el cliente de correo** y **cancelación completada
  desde esa página** → **RF-13 validado E2E**.
- `detail` vacío en las cuatro filas; una fila por `event_id`, sin duplicados.

### Reproceso del evento fallido de `#28` (Spec 010, 2B/T27)

| Momento | `appointment.cancelled:28:v1` | `detail` |
|---|---|---|
| Antes (prueba previa al arreglo) | `failed` | «Servicio de automatización no disponible.» |
| Tras el reproceso (2026-10-30 00:38:58) | `sent` | vacío (limpiado) |

Se conservó la **misma fila** y el **mismo `event_id`**; no se creó una segunda fila. Es
la evidencia real del reproceso exigido por la Spec 010 (2B/T27). La cita `#28`
permanece `cancelled`.

### Verificación de QA (solo lectura)

| Comprobación | Resultado |
|---|---|
| `PRAGMA integrity_check` | `ok` |
| `appointments` con id 13..26 | **0 filas** (limpieza P-3) |
| `automation_events` huérfanos | **0** |
| `automation_events` de `#28` y `#29` | **8 filas**, todas `sent`, `detail` vacío |

---

## Consola y red

- **Consola JS:** `consoleAPICalled` = **0** y `exceptionThrown` = **0** en los 19
  escenarios (book, flow, restrict, dbl).
- **Log del navegador:** 1 única entrada de nivel `error`:
  `Failed to load resource: the server responded with a status of 404 (NOT FOUND)` en
  `http://127.0.0.1:5000/citas/cancelar/abc`, **provocada deliberadamente** para
  comprobar el 404 de referencia no numérica (escenario 7). No hay errores no
  intencionales.
- **Red (códigos observados):**
  - `POST /citas` → **303** (reserva y re-reserva), `POST /citas/cancelar/<id>` → **200**
    (verificación/validaciones y restricciones), `POST /citas/cancelar/<id>/confirmar`
    → **303** → `GET …/exito` → **200**, `GET /citas/cancelar/abc` → **404**.
  - Sin respuestas 5xx, sin `requestWillBeSent` fallidos, sin recursos rotos
    (`brokenImages = []`), sin errores de CORS.
  - `redirectResponse`: un único salto 303 por cada POST de confirmación y por cada
    reserva; el reintento no produce 303 (se queda en 200 con el literal de conflicto).
- **Webhook n8n (pasada 2, entorno de la usuaria):** antes del arreglo del workflow,
  `appointment.cancelled` recibió **HTTP 400** (rama ausente en el Switch) mientras
  `appointment.cancellation_email` de la misma cita recibía **200**; tras el arreglo, los
  **4/4** eventos de `#29` quedaron `sent`. Este tráfico **no** fue observado por el
  arnés de QA: se documenta a partir del estado persistido y del relato de la usuaria.
- **Estados de operación:** validación nativa → mensaje de servidor; resumen →
  confirmación con botón deshabilitado y `aria-busy` mientras envía; éxito → pantalla
  propia; conflicto/reintento → literal «Esta cita ya fue cancelada.»; error →
  literales de verificación/formato/restricción. Todos corresponden a la respuesta real
  del backend.

---

## Escritorio y móvil

- Viewport de escritorio: `1280×900` (`deviceScaleFactor 1`, `mobile false`).
- Viewport móvil: `375×812` (`deviceScaleFactor 1`, `mobile true`) aplicado con
  `Emulation.setDeviceMetricsOverride`.
- En ambos: `document.scrollWidth === innerWidth` (1280 / 375) y sin desbordamiento en
  `.cancellation`, `.cancellation__form`, `.appointment__summary`, `main`,
  `.site-header` ni `.site-footer`.
- Contenido íntegro y legible en 375: el resumen pasa a dos columnas (etiqueta/valor),
  los botones quedan accesibles y el texto justificado no presenta cortes de palabra
  (`hyphens: none`), conforme a `docs/design-typography.md`.
- Paleta Serenidad Natural verificada visualmente (fondo marfil, contenedores verde
  agua, acción salvia oscura, aviso arena/terracota); `tests/test_contraste.py` sigue en
  verde dentro de la suite.

---

## Datos de prueba utilizados

Filas `#13`–`#26`: datos **ficticios** de QA. Filas `#28` y `#29`: **no se transcriben**
datos del paciente porque no son necesarios para la evidencia (ver *n8n — prueba E2E en
canal real*).

| Cita | Documento | Nombre / correo | Fecha-hora | Uso |
|---|---|---|---|---|
| #13 (cancelada) / #14 (confirmada) | `00000000` / `00000009` | Paciente QA Demo / Paciente QA Reserva | 2026-10-27 16:30 | Reserva por UI → cancelación → re-reserva |
| #15 (cancelada) / #16 (confirmada) | `00000007` / `00000009` | Paciente QA Flujo / Paciente QA Reserva | 2026-10-28 16:00 | Reserva por UI → cancelación → re-reserva |
| **#17 (cancelada) / #18 (confirmada)** | `00000010` / `00000009` | Paciente QA Final / Paciente QA Reserva | 2026-10-30 15:30 | **Flujo completo definitivo** |
| #19 | `00000001` | Paciente QA Cerca | 2026-10-26 21:41 | Restricción 3 h (insertada por SQL) |
| #20 | `00000002` | Paciente QA Pasada | 2026-10-26 18:41 | Hora iniciada/pasada (SQL) |
| #21 / #22 | `00000003` / `00000004` | Paciente QA Borde Ok / Borde No | 2026-10-26 22:43 / 22:39 | Borde de ventana (SQL) |
| #24 | `00000013` | Paciente QA Borde Ok 2 | 2026-10-26 22:51 | Borde ≥ 3 h (SQL) |
| #23 / #25 (canceladas) | `00000008` / `00000011` | Paciente QA Doble / Doble 2 | 2026-10-29 15:00 / 14:00 | Intentos previos del doble envío |
| #26 (cancelada) | `00000011` | Paciente QA Doble 2 | 2026-10-29 14:00 | Doble envío definitivo (RF-10) |
| #28 (cancelada) | no transcrito | no transcrito | 2026-10-27 14:00 | Prueba previa al arreglo del workflow y **reproceso real** (Spec 010, 2B/T27) |
| #29 (cancelada) | no transcrito | no transcrito | 2026-10-30 14:30 | **Prueba E2E de cierre**: 4/4 eventos `sent`, correos y enlace reales (RF-8, RF-13) |

Filas `#19`–`#22` y `#24` se insertaron por SQL directo (solo para forzar fechas/horas
que la UI no permite reservar en el pasado o a menos de 3 h) y no se canceló ninguna.
`automation_events` de `#17` y `#26` contenía exactamente 1 `appointment.cancelled` y 1
`appointment.cancellation_email` por cita (`skipped`, sin duplicados).

**Nota actualizada (2026-10-30):** las 14 filas `#13`–`#26` **ya no están** en
`data/consultorio.db`; se eliminaron con respaldo previo y auditoría (ver **P-3**,
resuelto). Esta tabla se conserva como registro histórico de la pasada 1: su evidencia
son las capturas y los registros del arnés, no las filas.

---

## Incumplimientos bloqueantes

**Ninguno demostrado.** No se encontraron desviaciones de HU-017 respecto de la
especificación aprobada, del plan, de los criterios de aceptación ni de
`docs/constitution.md` en el alcance revisado (RF-1..RF-13, RNF aplicables, AGENTS.md).
El único defecto conocido del flujo es **ajeno a HU-017** y se registra a continuación.

---

## Riesgo conocido fuera de alcance: D-010-01

**Referencia:** `docs/defectos/D-010-01.md` (estado `PROPUESTO`; **no** autoriza
implementación). **No es un defecto de HU-017.**

**Descripción.** En `consultorio/services/automation_service.py`, `urllib.error.HTTPError`
es subclase de `urllib.error.URLError` y se captura **antes**: una respuesta 4xx/5xx real
se registra como `failed` con el detalle «Servicio de automatización no disponible.» en
lugar del detalle de respuesta no válida. Afecta a los **cuatro** tipos de evento del
flujo de automatización y también al **reproceso**.

**Impacto.** Traza engañosa: el `detail` no permite distinguir un rechazo del receptor
(contrato) de una caída del servicio, y un evento `failed` por 4xx/5xx puede readmitirse
en el reproceso y repetir un POST ya rechazado. La cancelación confirmada y la
integridad de los datos **no** se ven afectadas (Spec 010, RF-7/RF-11/RF-12).

**Por qué no bloquea HU-017.** Es un defecto de **clasificación de errores de la Spec
010**, no del comportamiento funcional de la cancelación por el paciente: en la prueba
real los eventos quedaron `sent` y la cancelación, la liberación del hueco y los correos
funcionaron. La corrección se gestiona como **defecto de la Spec 010** (decisiones
DP-01..DP-06 pendientes de la usuaria), **no** como cambio de HU-017; este informe no
modifica código ni el registro del defecto.

**Huella en esta evidencia.** El evento `appointment.cancelled:28:v1` conservó el detalle
erróneo hasta su reproceso exitoso (2026-10-30 00:38:58), que lo limpió. La fila
histórica y la no reintentabilidad de los no-2xx siguen pendientes de DP-03/DP-02.

---

## Verificaciones pendientes y limitaciones

| ID | Estado | Aspecto | Requisito afectado | Evidencia / motivo | Efecto en el veredicto |
|---|---|---|---|---|---|
| **P-1** | **RESUELTA** | Envío real del correo de cancelación por el canal configurado | RF-8, TC-017-005, criterio de finalización | Prueba E2E de la usuaria con el webhook de n8n configurado: **4/4** eventos `sent` en `#29` y correo de cancelación recibido (ver *n8n — prueba E2E en canal real*) | Sin efecto: TC-017-005 y TC-017-014 cerrados |
| **P-2** | **RESUELTA** | Apertura del enlace de cancelación desde un correo real | RF-13 | La usuaria abrió el enlace desde el **correo real recibido** y completó la cancelación desde esa página (E2E) | Sin efecto: RF-13 CUMPLE E2E |
| **P-3** | **RESUELTO** | Datos de prueba en la BD local | — | Filas QA `#13`–`#26` (14 citas + 30 eventos) eliminadas con respaldo `data/consultorio.db.bak-20261026201134` y auditoría posterior (ver más abajo) | Sin efecto; limpieza auditada |
| **L-1** | Vigente | MCP `chrome-devtools` no disponible en la sesión | Validación visual (AGENTS.md) | No había servidor MCP ni endpoint CDP del navegador del usuario; se usó **CDP directo con Chrome aislado** (ruta 2 autorizada por la usuaria) | Método equivalente en capacidades (consola, red, viewport, capturas); se documenta para trazabilidad |
| **L-2** | Vigente | Render de Chrome headless por debajo de 500 px | Reglas de pruebas visuales | Se aplicó `Emulation.setDeviceMetricsOverride` (375×812) y se midió `scrollWidth`; no se usó `--window-size=375` | Sin efecto: la comprobación de desbordamiento es por métricas del DOM |
| **L-3** | Vigente | Incidencia puntual del arnés | — | En la primera pasada, una captura devolvió `net::ERR_NO_BUFFER_SPACE`; no se reprodujo tras añadir espera explícita de imágenes y la captura afectada se regeneró | No es un defecto de la aplicación; las capturas finales se tomaron con la página completamente cargada |

**Cierre de P-3 (2026-10-30).** Las 14 filas QA `#13`–`#26` y sus 30 eventos se
eliminaron de `data/consultorio.db` con **respaldo previo**
`data/consultorio.db.bak-20261026201134`, cuyo sha256 verificado por QA es
`531b3043bea8c799ca61de56ea91d498035be2456b247d4b9ab2b4d3217f8e39`. Auditoría posterior
(solo lectura): `PRAGMA integrity_check` → `ok`; `appointments` con id 13..26 → **0
filas**; `automation_events` huérfanos → **0**. La limpieza la ejecutó la
usuaria/coordinación fuera de QA; este informe solo registra el resultado verificado. Las
capturas y los registros del arnés conservan la evidencia del flujo aunque las filas ya
no existan.

---

## Recomendaciones opcionales (no bloqueantes)

- **O-1.** En `templates/cancellation/verify.html` y `summary.html` el `action` del
  formulario está escrito como ruta literal (`/citas/cancelar/{{ cita_id }}`). Usar
  `url_for` evitaría desajustes si cambia la regla de ruta. No incumple el plan (las
  rutas están fijadas en §5).
- **O-2.** `GET /citas/cancelar/<id>/exito` es accesible sin sesión y expone
  servicio/fecha/hora de cualquier cita cancelada cuyo id se conozca (sin datos
  personales). Es el comportamiento previsto por RF-7; si en el futuro se quiere
  endurecer, habría que decidirlo en la spec.
- **O-3.** La página `/citas/confirmada/<id>` muestra la fecha en formato ISO
  (`2026-10-30`), mientras el resumen de cancelación usa fecha legible
  (`viernes, 30 de octubre de 2026`). Es comportamiento previo de la Spec 004 y queda
  fuera del alcance de HU-017.
- **O-4 (observación editorial, no bloqueante).** En
  `specs/017_cancelar-cita-paciente/spec.md`, RF-1 (línea 28) contiene la errata «el
  número de documento de documento». Ya estaba señalada en la revisión de 2026-10-23
  (plan §8.8, ítem P-2). **No se corrigió**: la enmienda de la spec requiere decisión de
  la usuaria y este informe no modifica `specs/**`. No afecta al comportamiento
  implementado ni a los criterios verificados.

---

## Estado del entorno al cierre

Cierre de T10: **2026-10-30**.

- **Servidor de revisión en marcha:** `python app.py` (pid **15088**) →
  **http://127.0.0.1:5000** (comprobado por QA al cierre: `/` → **200**,
  `/citas/cancelar/999999` → **200**). URL del flujo:
  **http://127.0.0.1:5000/citas/cancelar/<id>**.
- **Chrome de QA (pasada 1):** instancia aislada (pid 10388, puerto 9222) **cerrada** al
  finalizar la pasada 1.
- **Base de datos:** `data/consultorio.db` con `PRAGMA integrity_check` → `ok`; sin filas
  QA `#13`–`#26`; 0 eventos huérfanos. Respaldo de la limpieza:
  `data/consultorio.db.bak-20261026201134` (sha256 verificado).
- **Git:** rama `feature/hu-017`, HEAD `83babda`, sin cambios versionados de código
  atribuibles a esta revisión. Cambios previos ajenos a la HU presentes en el árbol y
  **no evaluados aquí**: `AGENTS.md`, `specs/011_visualizar-agenda/spec.md`,
  `specs/018_cancelar-reprogramar-citas/spec.md` (modificados) y
  `.agents/skills/sdd/`, `.opencode/`, `docs/defectos/`, `tests/demo_reprocess.py` (sin
  seguimiento). `docs/evidencias/hu-017/` es nuevo y contiene este informe y las 25
  capturas.
- **Suite:** 283 passed, 0 FAIL (re-ejecutada al cierre: 36.22 s).

---

## Artefactos de esta validación

- `docs/evidencias/hu-017/qa-hu-017.md` (este informe).
- 25 capturas `qa-hu-017-*.png` en esta misma carpeta (pasada 1).
- Registros técnicos del arnés (fuera del repositorio, en
  `%TEMP%\opencode\hu017-t10\`): `log-book.json`, `log-flow.json`,
  `log-restrict.json`, `log-dbl.json`, `state.json`, `cdp.mjs`, `qa.mjs`.
- Evidencia de la pasada 2 (canal real n8n): filas de `automation_events` de `#28` y
  `#29` en `data/consultorio.db`, corroboradas por consulta de solo lectura; correos
  reales y apertura del enlace verificados por la usuaria. **No hay capturas de la
  pasada 2**: no se tomaron y no se simulan.
- Salida de `python -m pytest -q`: 283 pruebas, 0 fallos (23.09 s en la pasada 1;
  36.22 s en la re-ejecución de cierre).
