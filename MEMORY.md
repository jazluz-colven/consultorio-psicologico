# MEMORY.md — Página web para el Consultorio de Psicología Carolina Gómez

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no
aporte.

## Estado actual
- Versión 1.0 - En desarrollo
- **HU-001 (Spec 001) ACEPTADA** (2026-10-07): portada completa, rama `feature/hu-001`,
  cerrada en `ba23658`.
- **HU-002 (Spec 002) ACEPTADA y CERRADA** (2026-10-07, rama `feature/hu-002`;
  `c71c78c` spec+plan, `f782797` feat, `a686a58` plan, `6ed88eb` evidencia,
  `8103b91` justificación generalizada, `5038f6b` evidencia regenerada,
  cierre de aceptación en `qa-hu-002.md`).
- **HU-003 (Spec 003) ACEPTADA y CERRADA** (2026-10-08, rama `feature/hu-003`):
  página `/servicios` con los 2 servicios (catálogo + servicio + blueprint +
  plantilla + CSS `.services-page-*`), fallback por campo, 404 de subrutas y
  **banner de imagen por servicio** (Q6/D14: WebP 1200×600 y 1200×800,
  `aspect-ratio: 2/1` + `object-fit: cover` + `border-radius`; el PNG original de
  1 MB se convirtió a WebP 55 KB). Veredicto QA **PASS** en
  `docs/evidencias/hu-003/qa-hu-003.md` (aceptación 2026-10-08); capturas
  `escritorio-1280.png` (1280×1965) y `movil-375.png` (375×2286). Commits:
  `6440e74` spec, `84169a4` catálogo, `c16a098` servicio, `66d980a` web+plantilla,
  `5be6b48` CSS, tests en `18f5a85`/`5b5dbdb`/`249dae6`/`6d4a5f4`, `6f2a9c4`
  regresión, `6992364`+`d659139` evidencia/imágenes; cierre de aceptación en
   `qa-hu-003.md`. Mergeado a `main` (`bf2533d`) antes de crear la rama actual.
- **HU-016 (Spec 016) + enmienda de identidad ACEPTADAS y CERRADAS**
  (2026-10-08, rama `feature/identidad-buscador`): nombre
  **«Carolina Gómez»** en todo el sitio, cabecera con logotipo
  `hero-contenidas.png` + nombre, hero con `hero-presentacion.png` (380×511,
  marco elíptico 50 %), tipografía **Open Sans** (Google Fonts por `@import`),
  y **buscador** `GET /buscar` (etiqueta oculta, D9; cabecera responsive
  768-1199, D10). Commits: `d0e2d4c` docs, `ed36013` feat, `f53282d` tests,
  `2c1c146` evidencia+memoria; veredicto **PASS** en
  `docs/evidencias/hu-016/qa-hu-016.md` (aceptación 2026-10-08, sin PNG por Q6).
  Specs/plans 001-003 enmendados; `docs/design-identity.md` nuevo. Mergeada a
  `main` (`fac427d`).
- **HU-004 (Spec 004) ACEPTADA Y CERRADA** (2026-10-09, rama `feature/hu-004`
  desde `main`): flujo de reserva en
  `/citas` — formulario de 8 campos, disponibilidad en vivo
  (`GET /citas/horarios` + `availability.js`), alta con PRG (303 →
  `/citas/confirmada/<id>`), estado inicial **«Pendiente»** (`pending`).
  **Modificación visual D19 (2026-10-09)**: layout en **2 columnas** (datos del
  paciente ‖ fecha y hora), **datepicker vanilla propio** (días agendables
  lun–vie ≥ hoy diferenciados, navegación de meses) y horas en **bloques
  Mañana/Tarde** con radios; textos nuevos (`MSG_SELECT_DATE_HINT`,
  `BOOKING_BLOCK_*`, títulos de sección) en content + espejo.
  **Primera persistencia del proyecto**: `consultorio/persistence/` con SQLite
  stdlib, tabla `appointments` (11 columnas) e índice **`UNIQUE (service,
  date, time)`**; `data/consultorio.db` en `.gitignore`; tests con BD temporal
  por fixture. 14 slots 30 min (08:00–11:30 y 14:00–16:30), solo lun–vie,
  documento y celular **solo dígitos** (enmienda de la usuaria 2026-10-09).
  Spec 004 enmendada (dudas Q1/Q2 cerradas + literales fijados). Commits:
  `f68b765` docs, `392227f` contenido, `e8274cf` persistencia, `ef62651`
  servicio, `7a25fd2` web+JS+CSS, `eb10fc3` tests, `cee1528` evidencia+memoria,
  y los commits de D19 en el mismo orden de fases. Veredicto **PASS** en
   `docs/evidencias/hu-004/qa-hu-004.md`; capturas `escritorio-1280.png`
   (1280×1433) y `movil-375.png` (375×2569), sin desborde verificado por
   `scrollWidth`. Ajuste posterior (2026-10-09): **Servicio, helper y botón
   «Agendar cita» pasan a la columna izquierda** (Servicio sobre «Datos del
   paciente»; helper + botón debajo de los campos), solo reposición en la
   plantilla. **Mergeada a `main` (ff → `b793686`).**
- Tests: **163 PASS / 0 FAIL** (`python -m pytest -q`), Python 3.14.8 + Flask
  3.1.3 + pytest 9.1.1 (147 previos de HU-001/002/003/016/004/005/006/007 +
  16 nuevos TC-008-001..016; **TC-008-017 es la corrida de la suite, no una
  función**). TC-001-004 acotado al `<figure>` del hero y TC-001-008 a
  formularios que no sean el buscador.
- **HU-005 (Spec 005) ACEPTADA Y CERRADA** (2026-10-09, rama `feature/hu-005`):
  validar
  disponibilidad de horarios. Spec+plan+task enmendados/aprobados (`e92112b`,
  `56cff54`), repositorio `list_booked_times_by_date` (`40a71ac`), servicio
  `get_hours_with_status`/`get_available_days`/`is_valid_month` (`9d92e0c`,
  `ef8a5ca`), capa web con `occupied` + **`GET /citas/disponibilidad`** y
  plantilla con horas «Ocupado» + leyenda (`faf967c`, `c37fd53`; enmienda
  TC-004-021 a dos claves, D9), JS con estados de día (`is-full`/`is-bookable`),
  guard `seq` y estado de carga (`f9b62f1`), CSS (`6dedebd`) y tests de HU
  (`accb304`). Veredicto **PASS** en `docs/evidencias/hu-005/qa-hu-005.md`
  (16/16 TC, demo manual 16/16, capturas `escritorio-1280.png` 1280×1539,
  `movil-375.png` 375×2726 y `dia-lleno-1280.png` 1280×1486).
  **Aceptada por la usuaria el 2026-10-09 (T18) y mergeada a `main` (`8463087`).**
- **HU-006 (Spec 006) IMPLEMENTADA — QA PASS, PENDIENTE DE ACEPTACIÓN** (2026-10-09,
  rama `feature/hu-006` creada desde `main`): evitar doble reserva. Spec+plan+task
  (`e6a8f4f`), literal `MSG_SUBMITTING` «Registrando tu cita…»,
  `create_booking()` endurecido (`sqlite3.IntegrityError`/`OperationalError` →
  `SLOT_TAKEN`; sin `except Exception`), guard JS de envío + CSS `:disabled` /
  `[aria-busy]`, `data-submitting` en la plantilla y 16 tests nuevos (`6233f9d`,
  `afa4423`). **Enmienda 2 (Q6/D13, 2026-10-09)** tras la observación de la
  usuaria («El mensaje de «Registrando tu cita…» es muy rápido»): el estado se ve
  al menos **700 ms** (`SUBMITTING_MIN_MS = 700`) — el primer envío hace
  `preventDefault()` (sin eso el navegador navega ya y el retardo no sirve) y
  `form.submit()` a los 700 ms; TC-006-017. Veredicto **PASS** en
  `docs/evidencias/hu-006/qa-hu-006.md` (17/17 TC, suite 134/134; clic→POST
  medido en el reloj de la página: **728 ms**; capturas CDP 1280/375 medidas por
  IHDR). BD de desarrollo: filas 25–28 = pruebas manuales de la usuaria; fila 34 =
  demo de la evidencia; se limpiaron las filas 29–33 de ejecuciones intermedias.
  **Aceptada por la usuaria el 2026-10-09 (T17, incluida la enmienda 2) y
  mergeada a `main` (fast-forward).**
- **Tipografía vigente**: **Open Sans** (18 px base), h1 con `text-wrap: balance` y
  **justificación generalizada** (`text-align: justify` + `hyphens: none`).
  Decisiones en `docs/design-typography.md` (sección «Decisión vigente — Open Sans»);
  reglas permanentes en `AGENTS.md`.
- **Evidencia visual HU-001/002** (2026-10-07): `hu-001/escritorio-1280.png` 1280×1268,
  `hu-001/movil-375.png` 375×2215, `hu-002/*.png` 1280×1394 y 375×1903; los
  `*-devtools.png` se conservan (verificados por píxeles). **Quedan históricas**
  tras la enmienda de identidad (Q6: no se regeneran).
- Servidor de revisión en marcha: `python app.py` → http://127.0.0.1:5000/
  (`/buscar?q=psicología` responde 200).
- **HU-007 (Spec 007, automatización n8n) ACEPTADA Y CERRADA** (2026-10-10, rama
  `feature/hu-007`): plan aprobado y spec enmendada (Q1 webhook genérico
  `appointment.confirmed`, Q2 payload **sin PII**, `automation_events` con
  `UNIQUE(event_id)`, POST síncrono stdlib timeout 3 s, sin reintentos). Config
  por env (`AUTOMATION_WEBHOOK_URL` vacío = deshabilitado, parse defensivo de
  timeout), repositorio de eventos (dedup → 0 POST en reproceso), aislamiento
  total (la automatización nunca invalida la reserva; demo: webhook caído →
  303 intacto + evento `failed`). 12 tests nuevos (TC-007-001…012); suite
  **146 PASS / 0 FAIL**. Veredicto **PASS** en
  `docs/evidencias/hu-007/qa-hu-007.md`. BD dev: citas 36–40 de la demo.
  Commits: `4735576` docs, `d1a1bd5` config+persistencia+contenido, `31367d0`
  servicio+disparo+web, `138b547` tests, `9d039a9` evidencia+memoria; aceptación
  y merge a `main` 2026-10-10. **Enmienda 2 (Q7/D14)** tras el 403 del n8n cloud:
  cabecera opcional **`AUTOMATION_WEBHOOK_AUTH_HEADER`** (`Nombre: valor`,
  default vacío; **el token es secreto de entorno, nunca en el repo**);
   TC-007-014, suite **147 PASS**, live n8n `webhook-test` → **HTTP 200** y **E2E
   app→n8n OK** (cita 42 → evento `sent`; usuaria: «La prueba de conexión fue
   satisfactoria», 2026-10-10; commits `ae854cb`/`5c817cf`/`7dff948`).
- **HU-008 (Spec 008, correo de confirmación vía n8n) ACEPTADA Y CERRADA**
  (2026-10-11, rama `feature/hu-008`):
  spec 008 **enmendada** («Contratos fijados») y plan revisado/reaprobado con
  Q1–Q7; nuevo evento **`appointment.confirmation_email` (v1)** al **mismo
  webhook de HU-007**, con `recipient` (`to`+`patient_name`, PII documentada) y
  `message` (subject/text/html **compuestos por la app**); n8n solo transporta.
  `email_content.py` (paleta Serenidad Natural inline, fecha legible en español)
  + espejo en `expected_content.py`; `email_service.py` reutiliza
  `automation_service._post_webhook` **por referencia de módulo (D14)** y
  `automation_events` con `event_id` determinista (Q4); **D15**: TC-007-002/007
  filtran POSTs por `event_type` (2 eventos por reserva). Sin SMTP, sin env vars
  nuevas, firma de `create_booking()` intacta. 16 tests nuevos (TC-008-001…016);
  suite **163 PASS / 0 FAIL**. Veredicto **PASS** en
  `docs/evidencias/hu-008/qa-hu-008.md` (demo §6.2: 2 POST → `sent`, receptor
  caído → `failed` con motivo + 303 intacto, reproceso → 0 POST). Commits:
  `7a3d9df`   docs, `e2040fa` contenido, `da18850` servicio+disparo, `62f06cd`
  tests. **Live E2E 2026-10-11**: workflow de la usuaria (correo + **Google
  Calendar**) activo en producción → cita 46, ambos eventos `sent` y correo
   recibido («Sí, llegó»). La cita queda `pending` por diseño (spec 004; sin
   transiciones de estado aún — cancelación = Spec 010).
- **HU-015 (Spec 015, consultar contacto) ACEPTADA Y CERRADA** (2026-10-12, rama
  `feature/hu-015`, mergeada a `main`): página
  **`/contacto`** con bloques por canal (Dirección, WhatsApp, Correo electrónico,
  Horarios de atención, Redes sociales) — **sin bloque Teléfono** (opcional, no
  disponible; D16; RF-3 condicional). Spec 015 **enmendada** («Contenido de
  contacto»: dirección Calle 34 #29-18 / Mejoras Públicas / Bucaramanga;
  WhatsApp `+573168756020` → `wa.me/573168756020`; `caritogomez26@gmail.com`;
  horarios D13 lun–vie; solo Instagram `psi.carolinagomez`). Sin SQLite:
  `content/contact_content.py` + `services/contact_service.py` (resolución
  vivo→default→omisión, `fallback_active`; horarios con
  `DEFAULT_OFFICE_HOURS`), blueprint `contact`, `PLACEHOLDER_SECTIONS` =
   `["/articulos"]`, CSS `.contact-*`. 16 tests nuevos (TC-015-001…016); suite
   **179 PASS / 0 FAIL**. Veredicto **PASS** en
   `docs/evidencias/hu-015/qa-hu-015.md` (capturas CDP 1280×1335 y 375×1552, sin
   desbordes). Commits: `04640c7` docs, `942cf77` contenido+espejo, `7c14cfc`
   servicio, `1f60bda` web+plantilla, `6eb32eb` CSS, `9670a9c` tests,
   evidencia+MEMORY en el commit de cierre.
- **HU-015 ampliación (cajón + iconos + mapa) ACEPTADA Y CERRADA Y MERGEADA**
  (2026-10-12, rama `feature/hu-015-diseno` → `main`): spec 015 enmendada con **RF-7**
  (mapa condicionado a dirección) + literales `MAP_QUERY`/`MAP_EMBED_URL`/
  `MAP_LINK_URL`/`MAP_LINK_LABEL`/`MAP_FRAME_TITLE` (iframe de Google Maps sin
  API key + enlace «Abrir en Google Maps»). Plantilla refactorizada: un **cajón
  `.contact__panel`** con 5 `<li class="contact__row">` (SVG inline `aria-hidden`
  + etiqueta + valor; marcado de enlaces idéntico a v1) y bloque
  `.contact__map`; CSS con **grid 2 columnas ≥900 px** (cajón ‖ mapa) y
  apilado <900 px. Servicio con `ContactMap` + `ContactView.map` (vivo→
  default→omisión, CL-1/CL-5). 3 TC adaptados (009/012/015) + 3 nuevos
  (017/018/019); suite **182 PASS / 0 FAIL**; capturas regeneradas
  (1280×1156 / 375×1574). **Lección**: a 375 px `.contact__label` (10,5 rem)
  desbordaba el valor con tokens largos (email) → `flex-wrap: wrap` en
  `.contact__row` + `min-width: 0`. Commits: `2bd6f53` docs, `923f9b6`
  contenido+servicio, `33bee8f` plantilla+CSS+tests, evidencia+fix en el
  cierre. **Aceptada por la usuaria 2026-10-12 (T17)**.
- **Pulido contraste AA + back-links + foco (2026-10-12, rama
  `feature/contraste-aa` **ACEPTADA POR LA USUARIA Y MERGEADA A `main`**
  (ff → `5c3847d`))**: revisión frontend
  encontró contraste <WCAG AA (botones/enlaces 2.77, hover 2.14, hero 1.55,
  errores 2.14) y `outline: none` en el calendario. Solución: **2 tonos
  funcionales derivados** `--color-primary-dark: #3D5A4E` y
  `--color-accent-dark: #7F4527` (≥4.5:1 sobre marfil Y verde agua; decisión
  en `docs/design-contrast.md`, tabla de paleta actualizada en `AGENTS.md`).
  A3: `.search-page__back` + `.placeholder__back` (margen/negrita). A2:
  foco `2px solid #30454B` en calendario/inputs/enlaces/botones. Nuevos
  `tests/test_contraste.py` (5 TC) y `expected_content.PALETTE` con 8 hex.
  **Suite 187 PASS / 0 FAIL**; 12 capturas CDP sin desbordes en
  `docs/evidencias/pulido-contraste-aa/` (+ qa PASS). Specs no tocados
  (los textos «6 hex» de planes 001-006/015/016 quedan superados por la
   decisión). **Lección**: `:focus-visible` no matchea con `element.focus()`
   de script; verificar con `Input.dispatchKeyEvent` (Tab) por CDP.
- **HU-010 (Spec 010 enmendada, notificar cancelación) ACEPTADA Y CERRADA**
  (2026-10-13, rama `feature/hu-010`): transición `confirmed → cancelled` vía `cancel_appointment()` (servicio
  interno **sin UI**, Q1); notificación por correo vía webhook n8n (evento
  **`appointment.cancellation_email` v1**, `event_id` determinista +
  `UNIQUE(event_id)` + UPDATE condicional — dedup D6; PII mínima
  `recipient`+`message` D9; best-effort nunca revierte D7; **sin env vars
  nuevas** D8). **Q4: el horario cancelado se libera** — el `UNIQUE (service,
  date, time)` inline migró a **índice único parcial**
  `ux_appointments_slot_open … WHERE status <> 'cancelled'` (backup
  `.bak-<timestamp>`, aborto ante duplicados activos, idempotente — D4/D5);
  disponibilidad excluye `cancelled`. Literales contractuales («Cita cancelada
  —», «Cancelada», pie de reagendado) + espejo. 17 TC nuevos (TC-010-001…017;
  018 = corrida de suite); suite **204 PASS / 0 FAIL**. QA PASS en
  `docs/evidencias/hu-010/qa-hu-010.md` (demo pasos a–e con receptor stdlib
  local). Commits: `9b6a850` docs, `6eac5c6` contenido, `8926931` persistencia,
  `d419d1e` servicio, `b2b31ee` tests, `9010825` evidencia. **TC-004-004 y
  TC-006-013 adaptados** al índice parcial (spec-backed, sin relajar garantías).
  WhatsApp pendiente de Spec 009. **Aceptada por la usuaria 2026-10-13 (T15)**;
  merge a `main` autorizado.
- **Spec 011 APROBADA** (2026-10-23, `specs/011_visualizar-agenda/spec.md`, enmienda
  `sdd-clarify` + cierre de dudas en working tree, sin commitear): **agenda diaria
  del psicólogo**. Dudas cerradas — A: «el día» = fecha actual según servidor (fechas
  arbitrarias → Spec 012); B: roles autorizados **psicólogo + administrador del
  sistema**, RF-4 con **literal único compartido** «Consulta de agenda restringida:
  inicia sesión con una cuenta autorizada.»; C: canceladas se muestran y diferencian,
  día solo con canceladas = agenda vacía; D: literales «No hay citas para hoy.»,
  «No disponible», «No pudimos cargar la agenda. Intenta de nuevo.». RF-1..RF-7
  (RF-5 datos incompletos, RF-6 orden cronológico, RF-7 fallo de persistencia).
  **Sin plan ni tareas todavía: la planificación NO está autorizada.**
- **Spec 010 — enmienda 2 (evento `appointment.cancelled`) APROBADA** (2026-10-23, texto
  por la usuaria): RF-8 ajustado, RF-10 reescrito (garantía acotada a fallos POST-commit),
  **RF-11..RF-15 nuevos** — (1) `reprocess_automation_event()` solo sobre `failed`, misma
  fila/`event_id`, no-op sobre `sent`/`skipped`/`pending`, exclusión de concurrencia
  (transición atómica), 4 estados fijos; (2) **atomicidad**: transición a `cancelled` +
  registro `pending` en la misma transacción SQLite («sin traza local, sin cancelación
  confirmada»; rollback si falla el registro); (3) `cancellation_email` sin cambios
  (ventana post-commit = limitación conocida). **Tres confirmaciones**: `pending` huérfano
  = no-op con **limitación operativa explícita** (sin vía de recuperación esta fase);
  desalineación T19/T20 (registro post-commit) aceptada y a corregir en planificación (no
  es defecto; hasta entonces NO afirmar que la atomicidad está en el código);
  `tests/expected_content.py` sin cambios. **Plan §9 y tareas T21-T27 REAPROBADOS**
  (2026-10-23, «Apruebo») con **división 2A (T21-T25) / 2B (T26-T27)** («Divide la
  fase»; 2B inicia al cerrar 2A). Tests: 18 TC-010-101..118, **222 PASS esperados**.
  **FASE 2A (T21-T25) CERRADA 2026-10-25**: motor transaccional (T22:
  `update_appointment_status_with_pending_event()` + `publish_cancelled_event()`),
  tests de atomicidad oficiales (T23: TC-010-110/112), reproceso sobre `failed`
  (T24/T25). Verificado en el cierre: **2 PASS** de T23 y suite completa
  **278 PASS / 0 FAIL**; se eliminó el temporal `tests/test_t22_quickcheck.py`.
  **2B**: T26 (concurrencia TC-010-117/119) ya cumple; **T27 pendiente** (falta
  `docs/evidencias/hu-010/qa-hu-010-rf8-10.md`, cierre y push).
  T16-T20 commiteadas (hasta `223a43c`).

## Decisiones (y por qué)
- **Despliegue en Render (2026-10-12)**: `render.yaml` (Blueprint, Python 3.12,
  `gunicorn app:app`, `healthCheckPath: /`) + `requirements.txt` (Flask, gunicorn) +
  **`DATABASE_PATH` configurable por env** en `consultorio/config.py` (default
  intacto: `data/consultorio.db`; rutas relativas se resuelven contra `cwd`).
  **En vivo 2026-10-12**: Blueprint `exs-db6f05gn74is73aq3070` → servicio
  **https://consultorio-psicologico-c6g6.onrender.com** (verificado: 6 páginas
  200, `/citas/horarios` y `/citas/disponibilidad` 200, reserva E2E → 303
  `/citas/confirmada/3` → horario pasa a `occupied`). La BD es efímera (se
  pierde en cada redeploy **y** en cada spin-down de 15 min sin tráfico). El
  push a `main` despliega solo; la clave de sync
  (`GET api.render.com/sync/<blueprint>?key=...`) es solo un respaldo manual y
  es **secreta: nunca publicarla**.
- **Flujo de despliegue acordado con la usuaria (2026-10-12)**: `push` a `main`
  ⇒ GitHub actualizado **y** Render despliega solo (~42 s); `push` a rama
  `feature/*` ⇒ solo GitHub, Render espera al merge en `main`. Cada deploy
  vacía la BD (plan Free sin disco).
- **Enmienda 2026-10-11 — estado inicial de la cita `confirmed` («Confirmada»)**
  (specs 004 y 008): la usuaria pidió que, registrada la cita, el estado sea
  Confirmada («una vez se registra la cita pasa a la confirmación»). Renombrado
  `STATUS_PENDING→STATUS_CONFIRMED` (+ label «Confirmada»), INSERT y
  `DEFAULT` de `appointments.status` = `'confirmed'`; payload de HU-007/008
  `appointment.status='confirmed'` (misma forma, `event_version` 1); correo
  con «Estado: Confirmada». El ciclo `pending→sent/skipped/failed` de
  `automation_events` no se toca. BD de desarrollo **limpiada** (en pruebas, sin
  migración). Rama `feature/estado-confirmada` **mergeada a `main`**
  (2026-10-11, junto con `feature/hu-008`; suite 163/163 en `main`).
  **Validada en vivo 2026-10-11**: cita 2 → 2 eventos `sent` + correo recibido
  con «Estado: Confirmada».
- **Sin SQLite hasta que una HU lo pida** → **resuelto en HU-004**: SQLite
  stdlib en `consultorio/persistence/` (sin ORM, sin dependencias); BD en
  `data/consultorio.db` (fuera de git); unicidad en el punto de persistencia.
- **Spec 001/002 con textos literales contractuales** (Q8): cambiar un copy obliga a PR
  de spec primero; `tests/expected_content.py` es su espejo. La spec 004 también
  fija literales (Q9 aprobado y enmendado 2026-10-09: documento y celular solo
  dígitos).
- **Rama de HU-004**: `feature/hu-004` nacida de `main` tras merge de
  `feature/identidad-buscador` (Q6).
- **Doble comprobación de horario (D9)**: `SELECT` previo + `UNIQUE` → mismo
  literal `MSG_SLOT_TAKEN` y 0 filas nuevas; la concurrencia avanzada queda para
  HU-006.
- **Disponibilidad por `(service, date)`** (D18): coherente con Spec 006 RF-2;
  HU-005 la usó con `/citas/horarios` (`available` + `occupied`) y añadió
  **`GET /citas/disponibilidad?service=&month=YYYY-MM`** (días del mes con ≥ 1
  hueco; 400 con servicio/mes inválidos, 405 en otros métodos).
- **HU-005 — decisiones clave**: disponibilidad = `servicio + fecha + hora` (duda
  cerrada en la enmienda); día con huecos → `is-bookable`, día sin huecos →
  `is-full` + `disabled` + «, sin horarios disponibles» en el aria-label; hora
  ocupada → radio `disabled` **sin** `name` + badge «Ocupado» (imposible
  postear); literales de estado servidos por `data-*` del calendario (nunca en
  el JS); guards `daySeq`/`hoursSeq` descartan respuestas obsoletas al
  cambiar de servicio/mes rápido.
- **Spec 001/002 con textos literales contractuales** (Q8): cambiar un copy obliga a PR
  de spec primero; `tests/expected_content.py` es su espejo.
- **Rutas placeholder** (Q1): ahora solo `/articulos`, `/contacto`, `/citas` responden
  «Sección en construcción»; `/nosotros` (HU-002) y `/servicios` (HU-003) las
  sustituyeron.
- **Sin botón CTA en el hero**; «Agendar cita» vive solo en el menú.
- **Todos los párrafos justificados y sin guiones** (regla permanente del usuario,
  2026-10-07): `justify` + `hyphens: none`, ajustados al cajón.
- Colores de la ilustración NO se usan como UI: paleta Serenidad Natural intacta
  (solo los 6 hex aprobados).

## Aprendizajes y errores a evitar
- **Incidente 2026-10-25 — spec borrada por glob mal construido**: al retomar la Spec
  017 se buscó `specs/spec-017*` (la carpeta real es `specs/017_cancelar-cita-paciente/`),
  se concluyó erróneamente que la spec no existía y el `@planificador` la
  **sobrescribió** con una versión regenerada inferior; la aprobación de la usuaria, la
  revisión del `@revisor` y el plan/tareas recayeron sobre ese texto equivocado.
  **Regla**: antes de «crear» un artefacto, comprobar su existencia con
  `glob specs/*017*/` o `git ls-files specs/`; si git lo tiene trazado, no regenerarlo.
  Recuperación: `git checkout HEAD -- <archivo>` + reaplicar solo la edición pedida.
  El plan/tareas generados sobre el texto equivocado deben **regenerarse y volver a
  aprobarse**.
- **`instance/` (BD de la versión plana antigua, esquema `citas`) eliminada del
  workspace** el 2026-10-12, con respaldo en
  `C:\Users\Jaz\AppData\Local\Temp\opencode\instance-backup\`; la app vigente usa
  `data/consultorio.db` (esquema `appointments`) y ni siquiera la lee.
- **Local desfasado del remoto (incidente 2026-10-12)**: la copia local de `main`
  (`abc70e2`) no era ancestro de `origin/main` (el remoto se reescribió con ~130
  commits). Antes de cualquier trabajo comparar `git status` con `git log
  main..origin/main`; la sincronización fue `git branch backup/local-main-20261012`
  + `git reset --hard origin/main` (acordado con la usuaria). **Nunca `push
  --force`** sobre el remoto.
- `pip` está **bloqueado por AppLocker**: usar `python -m pip install ...` (así se
  instaló Pillow 12.3.0 para convertir imágenes; es herramienta del entorno, no
  dependencia del proyecto).
- **n8n cloud**: los webhooks exigen autenticación (403 «Authorization data is
  wrong!» sin cabecera) y la URL `webhook-test/...` solo responde a **1 llamada**
  tras pulsar «Execute workflow» (si no, 404). La URL de producción es
  `webhook/...` con el workflow **activado**. El token vive solo en
  `AUTOMATION_WEBHOOK_AUTH_HEADER` (entorno), nunca en el repo. **Con 2 eventos
  por reserva (HU-007+HU-008) el Listen de `webhook-test` solo captura el
  primero** (incidente live 2026-10-11: `confirmed` sent + `confirmation_email`
  failed); para pruebas E2E con ambos eventos hacer el workflow **Active** y
  usar la URL de producción.
- Imágenes de portada: `hero-presentacion.png` es el hero (380×511);
  `hero-contenidas.png` (720×713) ahora es el logotipo de cabecera; llegó
  `hero-contenidas.png.png` (nombres dobles) y su fondo blanco se ve como caja
  sobre `#F7F3EA` (por eso la marca y el hero llevan fondo/borde propios).
- **Chrome 154 headless no renderiza a menos de 500 px**: para capturas exactas usar
  DevTools Protocol (`Emulation.setDeviceMetricsOverride`), midiendo `scrollHeight`
  antes; scripts en `C:\Users\Jaz\AppData\Local\Temp\opencode\` (`capture_cdp.ps1`,
  `measure_cdp.ps1`, `eval_cdp.ps1`, `probe_lines.ps1`, `imgtool.ps1`).
- **La emulación CDP es por sesión**: al cerrar el WebSocket se limpia; todo script
  (capture, measure, eval) debe fijar su propio viewport, y conviene perfil de Chrome
  nuevo para no servir CSS de caché (incidente visto en `/nosotros`).
- **Nunca lanzar dos capturas CDP en paralelo**: compiten sobre el mismo
  target/puerto 9444 (incidente HU-005: mes y medidas cruzados); ejecutarlas
  secuencialmente y re-medir `scrollHeight` hasta que se estabilice.
- **Chrome headless: `Network.emulateNetworkConditions` no retrasa el `POST`**
  (incidente HU-006): para capturar el estado «en curso» usar
  **`Fetch.requestPaused`** (`requestStage: "Request"`), comparar el frame
  antes/después y liberar con `Fetch.continueRequest`; mientras la petición está
  pausada el renderer queda en estado provisional y **`Runtime.evaluate` se
  bloquea** (no evaluar; capturar el screenshot directamente). Además, el clic
  debe enviarse **sin aguardar** la respuesta de `Runtime.evaluate`.
- **Retener el envío de un formulario exige `preventDefault()` en el primer
  `submit`** (HU-006/D13): sin él el navegador navega ya y un `setTimeout(…
  form.submit())` posterior no garantiza nada; con él, el estado en curso se ve
  el tiempo que se decida y `form.submit()` (que no re-dispara el evento) envía
  después. Medir el intervalo clic→POST **en el reloj de la página**
  (instrumentar `HTMLFormElement.prototype.submit` y leer el `console.log` por
  CDP): correlacionar el reloj mono de CDP con `Date.now()` de Node es impreciso.
- **En `/citas` la fecha la gobierna el clic del calendario** (`selectDate`), no
  un `change` del input `#booking-date`: fijar `input.value` desde un script no
  dispara `refreshHours()` y la vista de horas queda de otra fecha. Y en esperas
  de DOM contra el backend, exigir **igualdad exacta** con el JSON de
  `/citas/horarios` (p. ej. lista de ocupadas), no «algún elemento taken»: las
  vistas previas/retrasadas de otra fecha también lo cumplen (incidente de
  evidencia HU-006).
- **Reservas de demostración en `data/consultorio.db`**: las demos HU-004/005/006
  dejan filas reales (ids 1–4 y 24); si un script de evidencia falla a medias,
  eliminar sus filas antes de reintentar (incidente HU-006: ids 21–23).
- **`/citas` arranca con servicio `""`** (placeholder): `loadDayStates()` y
  `refreshHours()` no hacen fetch hasta elegir servicio; en la demo manual
  primero `select.value = … + dispatchEvent(change)` y después clic en el día.
- **Jinja + claves de dict con nombre de método**: `{{ d.values }}` resuelve a
  `dict.values`; usar `{{ d["values"] }}` (bug HU-002).
- El lector de imágenes del asistente puede adjuntar ficheros equivocados/caché:
  verificar siempre por medidas programáticas (DOM + muestreo de píxeles), no a ojo.
- **Servidor para revisión**: tras toda tarea visible, dejar `python app.py` en marcha
  y comunicar la URL (regla en `AGENTS.md`).

## Próximos pasos
- **Despliegue Render COMPLETADO** (2026-10-12): https://consultorio-psicologico-c6g6.onrender.com
  — **auto-deploy verificado 2026-10-12**: el push a `main` (`17a1416`)
  redeployó el servicio en **42 s** y vació la BD (cita de prueba desapareció);
  el sync manual solo hace falta si el push no despliega. **Disco persistente
  IMPOSIBLE en plan Free** (docs de Render: "Free web services don't support…
  Persistent disks"); además el sistema de archivos es efímero **también al
  apagarse por 15 min sin tráfico**, así que `data/consultorio.db` se pierde en
  cada redeploy *y* en cada spin-down. Opciones: plan de pago ($7/mes), Render
  Postgres Free (caduca a los 30 días, exige migrar SQLite → Postgres con spec y
  plan), o aceptar la BD efímera (válida para demo).
- **HU-008 + enmienda de estado CERRADAS** (2026-10-11); ambas mergeadas a
  `main` (fast-forward). Sin pendientes abiertos.
- **HU-015 ACEPTADA Y CERRADA** (2026-10-12, aceptación en `qa-hu-015.md`);
  v1 y **ampliación** (cajón+iconos+mapa RF-7, `feature/hu-015-diseno`)
  **mergeadas a `main`** (`e034c34`, fast-forward).
- Servidor de revisión: http://127.0.0.1:5000/contacto (ampliación HU-015).
- **Pulido contraste AA CERRADO** (2026-10-12): aceptado por la usuaria
  («Me gusta. Acepto.») y mergeado a `main` (ff → `5c3847d`); QA PASS en
  `qa-pulido-contraste-aa.md`. Sin pendientes abiertos de esta tarea.
- **HU-010 ACEPTADA Y CERRADA** (2026-10-13): rama `feature/hu-010` mergeada a
  `main` (autorización de la usuaria); suite 204/204.
- **Spec 017 APROBADA por la usuaria** (2026-10-13, `specs/017_cancelar-cita-paciente/`):
  el **paciente cancela su propia cita**; dudas cerradas — Q1 identificación
  `#id` + número de documento; Q2 mínimo **3 horas** de antelación; Q3 pantalla
  de confirmación con resumen previa; Q4 pantalla de éxito propia; Q5 botón
  «Cancelar cita» en `/citas/confirmada/<id>`; Q6 la cita cancelada muestra
  estado «Cancelada»; Q7 el correo de confirmación llevará **enlace directo** a
  la cancelación (**enmienda coordinada de la Spec 008** registrada).
- **Spec 017 — plan y tareas APROBADOS, implementación INICIADA** (2026-10-25, rama
  `feature/hu-017` desde `223a43c`): **incidente corregido** — el coordinador concluyó
  por error que la spec no existía (glob mal construido) y el `@planificador`
  sobrescribió la spec aprobada por una versión regenerada de 56 líneas; se restauró
  la original desde git y se reaplicó **solo** la edición de la usuaria en «Fuera de
  alcance» (la notificación la coordina el servicio centralizado de la Spec 010).
  `plan.md` (419 líneas, D1..D13) + `tasks.md` (**10 tareas** T1..T10) regenerados
  **contra la spec real (RF-1..RF-13)** y **aprobados por la usuaria** con las
  decisiones **Q-A…Q-F** (rutas `/citas/cancelar/<id>|/confirmar|/exito`, enlace del
  correo con `url_for(_external=True)` y etiqueta «Cancelar cita», aviso previo en la
  verificación, «No, volver» → `/citas/confirmada/<id>`, id no numérico → 404, **T8 se
  pospone si T22 sigue sin commitear**). Trazabilidad RF↔T↔TC-017-001..014 en plan §6-§7.
  Errata P-2 («documento de documento» en RF-1) **pendiente de decisión de enmienda**.
  Cambios sin commitear de la **Spec 010/T22** intactos y fuera de alcance.
  Estado: **T1–T4 commiteadas** (`38d6609` contenido, `d79c1af` verificación+ventana, `ab3c6b3`
  ejecución delegada, T4 plantillas+guard+CSS); suite **261 PASS**. Sigue T5 (blueprint).
  **Prueba E2E con n8n acordada para el cierre de la 017** (la cancelación dispara
  `appointment.cancelled` + `appointment.cancellation_email` de la Spec 010): usar la URL
  de **producción** del webhook (la de `webhook-test` solo captura la primera llamada) y las
  variables `AUTOMATION_WEBHOOK_URL`/`AUTOMATION_WEBHOOK_AUTH_HEADER` en el entorno.
- **Enmienda de la Spec 010 APROBADA** (2026-10-23): título ampliado a
  **«Servicio centralizado de cancelación y notificación de citas»**
  (identificador y ruta intactos). RF-1..RF-4 conservados (trazabilidad con
  HU-010); **RF-5..RF-7 consolidados** (transición única, liberación de
  horario, fallo de canal sin revertir — ya implementados); **RF-8..RF-10
  [PENDIENTE DE IMPLEMENTACIÓN]**: evento de negocio **`appointment.cancelled`
  v1** (`event_id` determinista + UNIQUE, payload sin PII, emitido tras el
  commit **independiente del correo**, fallo trazado y reintentable sin
  duplicados, sin reintentos automáticos). n8n guardará el `calendar_event_id`
  en su data table (sin tocar backend). Commit `1b63e5a` en `main`.
- **Revisión de referencias 017/018 (2026-10-23, @revisor)**: ambas **SIN
  CAMBIOS** — ya delegaban correctamente en el servicio de la 010, sin cita
  del título antiguo ni brechas. Plan 018 sin cambios por ahora; al
  implementar RF-8..10 de la 010, TC-018-005 deberá filtrar por `event_type`
  (apuntar en ese plan). Opcionales dejados para planificar cada HU:
  P-1 (contexto 018 atribuye a 010 también la reprogramación) y P-2 (errata
  «documento de documento» en RF-1 de 017).
- **Enmienda de la Spec 007 APROBADA** (2026-10-23): **RF-8..RF-13
  [PENDIENTE DE IMPLEMENTACIÓN]** + sección «Contratos fijados — borrado de
  Google Calendar». Contrato de consumo de `appointment.cancelled` por n8n:
  fila de creación con `appointment_id`+`calendar_event_id`, búsqueda por
  `appointment_id` (**nunca** por el `event_id` de cancelación/correo),
  reintentos idempotentes, ausencia controlada de `calendar_event_id`,
  tres estados separados (creación/cancelación/correo) y distinción evento de
  negocio vs. acción técnica de correo. **Solo contrato documental**: la
  implementación (data table, workflow, emisión) exigirá plan, tareas y
  aprobaciones posteriores. Secuencia del ciclo completada: 010 ✓ → 017/018 ✓
  → 007 ✓. **Pendiente**: commit de la enmienda 007 y decisión de push (un
  push a `main` despliega en Render y vacía la BD).

- **D-010-01 (Spec 010, enmienda 3 / RF-16) `CORREGIDO — VALIDADO TÉCNICAMENTE (QA APROBADO)`**
  (2026-10-30, rama `feature/hu-017`, commits `f32030b`, `4706862`, `97c40b9`, `cb8abe9`,
  `52a3557`, `2f65207`, `acd2a91`, `acb17fe`): causa raíz = `HTTPError` es subclase de
  `URLError` y se capturaba antes, así que 4xx/5xx reales se registraban como «Servicio de
  automatización no disponible.». Corrección: captura ordenada
  `TimeoutError → HTTPError → URLError → Exception` con helper único
  `_register_publication_failure()` en los **cinco** flujos (`publish_cancelled_event`,
  `reprocess_automation_event`, `on_appointment_confirmed`, `send_confirmation`,
  `send_cancellation`) + exclusión atómica de 4xx permanentes en `claim_failed_event()`
  (`detail IS NULL OR detail NOT LIKE <4xx> OR detail LIKE <429>`, sin `SELECT` previo ni
  migraciones). Literal vigente intacto (DP-01); sin cambios en `_post_webhook`,
  `tests/expected_content.py` ni specs 007/008. Suite **300 passed / 0 FAIL**; revisor
  independiente **APROBADO** (RF-8…RF-16 y CA-D010-01…14 CUMPLE; no vacuidad comprobada en
  worktree temporal). Evidencia: `docs/evidencias/hu-010/qa-hu-010-rf8-10.md`.
  Recomendaciones opcionales del revisor **aplicadas** (`a74269f`):
  `DETAIL_INVALID_RESPONSE_PREFIX` documentado como ancla de prueba; TC-D010-17
  (readmisión de `DETAIL_UNEXPECTED`) y TC-D010-18 (`claim_failed_event` sin
  patrones); suite **302 passed**. **Aceptación funcional de la usuaria: 2026-10-30**
  (estado `CORREGIDO — ACEPTADO FUNCIONALMENTE`). Árbol limpio; merge a `main`
  realizado el 2026-11-01 (sin push). `MEMORY.md` sigue siendo demasiado largo: compactar.

- **HU-017 ACEPTADA Y MERGEADA a `main` sin push** (2026-11-01): la usuaria aceptó la
  funcionalidad tras el veredicto `APROBADO` (registrado en `qa-hu-017.md`). Merge
  fast-forward de `feature/hu-017` → `main` (Spec 010 fase 2 RF-8…RF-16 + HU-017 +
  D-010-01); **sin push** en ese momento por decisión de la usuaria; subida finalmente
  el 2026-11-04 en `9bfdbef` (Render redesplegado). Pendiente de aprobación posterior: merge de
  `chore/proyecto-docs` (AGENTS.md, `.opencode/`, skill `sdd`, enmiendas 011/018).
  Siguiente: **HU-018** (primero las specs de cancelación); P4/P5 (011/012) después.

- **Enmienda 2026-11-01 de la Spec 007 IMPLEMENTADA Y VALIDADA (2026-11-04)**:
  workflow de n8n `HU-007 - Integración de citas con n8n` con 48 nodos
  (`docs/workflows/hu-007/n8n-hu-007-integracion-citas-2026-11-02-v5.json`,
  sha256 `89183067…`). Cinco escenarios E2E con PASS: A borrado real
  (`completed`/detalle vacío), B evento ya borrado (`not_found` + id limpio),
  C guard de reintento sin llamar a Calendar, D sin fila de creación y E sin
  `calendar_event_id` (ambos `skipped` con motivo). RF-8..RF-13 cubiertos.
  Aprendizajes de plataforma que costaron 4 ciclos: (1) n8n Cloud prohíbe
  credenciales OAuth2 de Google en nodos HTTP Request; (2) el nodo
  `googleCalendar` oculta el código HTTP; (3) `events.get` devuelve eventos
  borrados con `status: "cancelled"` → el discriminador correcto es el estado,
  no la existencia. Defecto `D-007-01` en `CORREGIDO — ACEPTADO
  FUNCIONALMENTE (2026-11-04)`.
  Evidencia y QA en `docs/evidencias/hu-007/enmienda-2026-11-01/`. Revisor:
  `CAMBIOS NECESARIOS` solo por documentación; huecos cerrados. Aceptación
  funcional de la usuaria y push: **2026-11-04**. Las cinco
  versiones del JSON (v1–v5) están conservadas en `docs/workflows/hu-007/`.

- **Estado de Git (2026-11-05)**: `main` = `origin/main` = `9846613`;
  `feature/hu-018` creada desde `main`. `D-007-01` en `CORREGIDO — ACEPTADO
  FUNCIONALMENTE (2026-11-04)`. `chore/proyecto-docs` (.opencode,
  `.agents/skills/sdd`, enmiendas 011/018) sigue sin merge y **no debe
  mergearse en bloque**: está muy desfasada (~28.700 líneas de borrado) y su
  enmienda 018 «reservar primero» (`8c0b3a5`) es contradictoria y fue
  **descartada** el 2026-11-05. `.opencode/` y `.agents/skills/sdd/` sin
  versionar.
- **HU-018 (Spec 018) — PLAN Y TAREAS APROBADOS (2026-11-05), T1 COMMITEADA**:
  rama `feature/hu-018` desde `main` (`9846613`); baseline **302 PASS**;
  commit `c1d53b5` (spec enmendada + plan revisado + `task.md`).
  Decisiones: **modelo A confirmado** (cancelar primero y después registrar la
  nueva; sin reversión; sin aceptación del paciente), actor psicólogo/
  administrador, token `CONSULTORIO_ADMIN_TOKEN`. Enmienda 2026-11-05 de la
  spec: contexto, literal Q2 «La cita ya estaba cancelada.», RF-9 (la fecha
  nueva sigue la Spec 004) y RF-1 (solo mensaje de acceso denegado).
  Plan/task corregidos tras la revisión (`CAMBIOS NECESARIOS`): campos reales +
  `document_type`, literal contractual de horario ocupado,
  `cancellation_url_builder`, cita ya cancelada, `?token=` solo GET +
  `no-store`/`no-referrer`, TC-018-017/018/019, 20 constantes (14+6),
  **18 tests → 320 PASS**, **7 tareas autocontenidas** (T1–T7).
  **T2 completada** (`b099104`: 20 constantes `ADMIN_`, espejo, config y 2
  tests; **304 PASS**). **T3 completada** (`e08c8fe`: blueprint `admin`,
  guard `hmac` (`?token=` solo GET, config vacía → 403), `GET` detalle y `POST`
  cancelar delegado en el servicio 010, plantillas admin + `admin.js` (patrón
  HU-006), 5 tests de rutas; **309 PASS**). D8: sin capturas en T3; validación
  visual en T6. **T4 completada** (`f3314d6`: `POST` reprogramar con orden D4
  —ya cancelada → validar → hueco → cancelar → crear—, 5 campos copiados,
  `cancellation_url_builder`, `SLOT_TAKEN` sin revertir la cancelación, 4 tests;
  **313 PASS**). **T5 completada** (`832149e`: `tests/test_hu_018.py` con
  TC-018-005/007/009/010/011/017/018, eventos filtrados por `event_type`,
  reloj congelado para RF-9 y orden cancelar→crear; suite **320 PASS**).
  **T6 en curso (2026-11-06)**: demo local §6.2 ejecutada con app en
  `127.0.0.1:5000` y receptor stdlib en `127.0.0.1:8765` (BD y artefactos en
  `%TEMP%\opencode\hu018-demo`, fuera del repo); **33/34** comprobaciones OK.
  Única pendiente: **Calendar/n8n real (Spec 007 RF-8) = NO VERIFICADO**;
  requiere la URL de producción y el Header Auth del workflow v5. Decisión de
  la usuaria (2026-11-06): dejar esa prueba **pendiente**; T6 queda **PARCIAL**
  (`[ ]`) y falta `docs/evidencias/hu-018/qa-hu-018.md`. Pendiente opcional:
  literal de error de persistencia (no incluido; 320 no cambia).
- **Decisiones confirmadas por la usuaria (2026-11-06) para la próxima spec de
  acceso/agenda**: administrador y psicóloga son **personas distintas**; MVP con
  roles **administrador** y **psicólogo**; agenda con **fechas pasadas y
  futuras**; **auditoría por usuario** obligatoria; el acceso debe integrarse
  con las Specs 011/012 y el detalle de la 018. La revisión visual local de la
  pantalla admin fue **OK**. Recomendación del coordinador (**pendiente de
  aprobación**): implementar primero el acceso y después 011/012, para no
  exponer PII con el token compartido ni rehacer el guard; alternativa solo si
  hay urgencia: 011/012 con token como piloto interno temporal y migración
  planificada. Las specs 011/012 existen pero **no tienen plan ni tareas**.
- **Solicitud de evaluación (2026-11-06): migración a PostgreSQL** y posibilidad
  de aprovecharla para el futuro módulo de acceso/agenda. Pendiente: spike de
  evaluación (inventario de SQLite, dialecto, tests, límites del plan de Render,
  migración de datos y rollback). Recomendación del coordinador: evaluar primero
  y, si es viable, migrar **antes** de implementar acceso/011/012; no mezclar la
  migración con la spec de acceso. **HU-018 no se migra**: se cierra en SQLite.
