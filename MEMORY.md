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
  **T6 parcial y cierre (2026-11-06)**: demo local §6.2 ejecutada con app en
  `127.0.0.1:5000` y receptor stdlib en `127.0.0.1:8765` (BD y artefactos en
  `%TEMP%\opencode\hu018-demo`, fuera del repo); **33/34** comprobaciones OK.
  Única pendiente: **Calendar/n8n real (Spec 007 RF-8) = NO VERIFICADO**;
  requiere la URL de producción, el Header Auth y el workflow v5 configurado en
  Render. Se creó `docs/evidencias/hu-018/qa-hu-018.md` con los 19 TC PASS, la
  demo y una sección específica de NO VERIFICADO; checkbox de aceptación
  marcado el **2026-11-07**. T6 queda **PARCIAL** (`[ ]`). **T7 cerrada**
  (commits por fase, `MEMORY.md` y servidor de revisión).
  **HU-018 cerrada técnicamente con la E2E n8n/Calendar pendiente y
  documentada**; **aceptada funcionalmente el 2026-11-07 con esa limitación**
  (sin declarar PASS la E2E). Pendiente opcional: literal de error de
  persistencia (no incluido; 320 no cambia).
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
- **Secuencia acordada con la usuaria (2026-11-06)**: la **primera sesión nueva
  es la evaluación PostgreSQL**; después se redacta la **spec de acceso/agenda**
  (roles administrador/psicólogo, sesión, CSRF y auditoría por usuario) y luego
  las Specs 011/012. La migración a PostgreSQL se evalúa con un spike
  (inventario de SQLite, dialecto, tests, límites del plan de Render, migración
  de datos y rollback). Recomendación del coordinador: si es viable, migrar
  **antes** de implementar acceso/011/012; no mezclar la migración con la spec
  de acceso. **HU-018 no se migra**: se cierra en SQLite.
- **HU-018 MERGEADA A `main` (local, 2026-11-07)**: fast-forward
  `9846613 → 8ce511f` (15 commits), **sin push**; `main` queda 15 commits por
  delante de `origin/main` y Render **no** se ha redesplegado. Verificado antes y
  después del merge: **320 PASS** (`python -m pytest -q`). **La aceptación
  funcional fue otorgada por la usuaria el 2026-11-07**, con la limitación
  documentada de que la **E2E n8n/Calendar sigue NO VERIFICADA** (no se declara
  PASS); registrada en `qa-hu-018.md`. T6 permanece **PARCIAL** y HU-018 se
  cierra como aceptada con limitación.
- **Evaluación PostgreSQL (spike 2026-11-07) — COMPLETADA TÉCNICAMENTE**:
  modalidad B; rama aislada `spike/postgres-evaluacion` en worktree
  `%TEMP%\opencode\spike-postgres`, sin commit ni merge. PostgreSQL 16.15 en
  Docker + `psycopg` 3.3.8; suite **307 PASS** con backend PG y **302 PASS /
  5 skip** en SQLite; pruebas críticas 5/5 (índice parcial, concurrencia,
  atomicidad Spec 010, dedup) con **no-vacuidad verificada** por `@revisor`
  → **APROBADO**. Informe: `docs/spikes/postgresql-evaluacion-2026-11.md`.
  Esfuerzo real: ~140–200 líneas netas en 9 archivos de producción + ~180–250 en
  6–8 tests; sin migración de datos. Render Free Postgres descartado (caduca a
  30 días); Render pago ~$6.30/mes; Neon Free $0; SQLite + disco ~$7.25/mes.
- **Spec 019 (migración a PostgreSQL/Neon) APROBADA por la usuaria (2026-11-07)**
  con estas decisiones: (1) **UTC** en `created_at`/`sent_at` y
  `America/Bogota` para futuras visualizaciones; (2) suite **siempre contra
  PostgreSQL**; (3) desarrollo/pruebas con **Postgres en Docker**, Neon solo
  para E2E; (4) **misma región** que Render, sin umbral numérico de latencia en
  el MVP; (5) SQLite queda como **rollback temporal** y se retira tras la
  aceptación; (6) **pérdida de filas en rollback aceptada** (snapshot antes de
  un rollback con datos reales); (7) nuevo literal de BD no disponible
  («No pudimos completar tu solicitud en este momento. Inténtalo de nuevo en
  unos minutos.») aprobado para el MVP, pero exige **enmienda coordinada** de
  las Specs 004/005 y su espejo `tests/expected_content.py`. Rama
  `feature/hu-019-migracion-postgres` (creada desde `main`, ya ff a `8ce511f`);
  `plan.md`/`tasks.md` **aprobados el 2026-11-08**; T1/T2 completadas
  (2026-11-09). Pendiente: reconciliar los literales de la
  **Spec 011** (están en MEMORY, no en su `spec.md`).
- **Enmiendas coordinadas 004/005/006/010 — APROBADAS por la usuaria
  (2026-11-08)**: 004 fija el literal `MSG_PERSISTENCE_UNAVAILABLE` («No
  pudimos completar tu solicitud en este momento. Inténtalo de nuevo en unos
  minutos.»); 005 lo reutiliza; 006 describe la unicidad como **índice único
  parcial** `ux_appointments_slot_open … WHERE status <> 'cancelled'`
  (coherente con 010) y acota el diagnóstico a citas no canceladas; 010
  sustituye «transacción de persistencia de SQLite» por «… del motor de base de
  datos». Sin cambios en código, tests ni `tests/expected_content.py`: la clave
  y su espejo entran con la implementación de la Spec 019.
- **Plan y tareas de la Spec 019 — APROBADOS (2026-11-08)**:
  `plan.md` con D1–D16 (psycopg 3.3.8 sin ORM, config
  `DATABASE_URL`/`PERSISTENCE_BACKEND`, conexión por petición + semáforo, DDL
  idempotente con advisory lock, atomicidad 010, errores 503 ≠ 409, UTC en
  `TEXT`, suite siempre PostgreSQL, rollback SQLite, Render/Neon, trazabilidad
  RF-1..30/RNF-1..8/CL-1..11); `tasks.md` con T1–T18 en fases A/B/C. T13 (E2E
  Neon desde entorno controlado) y T14 (Render: redespliegue/spin-down)
  separadas; `TC-010-014` se conserva, reubicado a la verificación de rollback
  (T15). Baseline 320 PASS en SQLite; el conteo final en PostgreSQL se
  reportará ejecutado, sin cifras inventadas.
  **Implementación: T1 y T2 completadas (2026-11-09)**; T3–T18 y T18 (retirada
  del rollback) requieren autorización expresa y revisión tras cada tarea.
  Sin commit ni push.
- **Spec 019 — T1 y T2 COMPLETADAS (2026-11-09)**:
  **T1:** PostgreSQL **16.15** en Docker (`consultorio-pg-019`,
  `127.0.0.1:55432`, volumen `consultorio-pgdata-019`, en marcha),
  `docs/operaciones/postgresql.md` y `docs/evidencias/hu-019/setup-local.md`;
  320 PASS. **T2:** `psycopg[binary]==3.3.8`; config por entorno
  (`DATABASE_URL`, `PERSISTENCE_BACKEND`, límites/timeouts y TLS);
  `tests/test_pg_resilience.py` (TC-019-001, 18 casos); evidencia
  `docs/evidencias/hu-019/t2-driver-config.md`; **338 PASS**. La usuaria
  aprobó **A1 (2026-11-09)**: binarios oficiales de EDB sin firma Authenticode,
  verificados por SHA-256 oficial; cliente local **16.15-5** (SHA-256
  `43BB45F1…CCAA8281`, 373.254.386 bytes) con `PSYCOPG_IMPL=python` y
  `libpq.dll` `NotSigned` aceptado; servidor 16.15. El `@revisor` emitió
  **APROBADO** para T2. **Riesgos no bloqueantes**: (a) `sslmode` duplicado en
  el DSN puede eludir la validación TLS (endurecer antes de T14);
  (b) `DATABASE_PATH` se lee con cualquier backend (condicionar en T3/T4/T15);
  (c) RF-17 y la indisponibilidad de rutas son parciales en T2 y se completan en
  T3/T4/T9; (d) restaurar el entorno del fixture de TC-019-001 y corregir el
  docstring de `tests/test_admin_content.py`. **T3 COMPLETADA y APROBADA
  (2026-11-09)**: capa `DatabaseTarget`/`Database` con conexión por petición,
  semáforo, transacciones y traducción de errores; 14 casos iniciales + 12 de
  la corrección F-01/F-02; **364 PASS**. El revisor aprobó tras corregir la
  traducción en operación/commit/rollback y el uso de `isinstance` sobre
  subclases reales de psycopg. **RF-23 sigue base/parcial** (T4/T5/T9).
  Observaciones no bloqueantes: falta un test automatizado de error de driver
  dentro de contexto Flask (verificado manualmente) y persiste el riesgo de
  `sslmode` duplicado de T2 (endurecer antes de T14). **T4 no autorizada**.
  Sin commit ni push.
- **Spec 019 — T4 COMPLETADA y APROBADA (2026-11-09)**: DDL PostgreSQL
  idempotente sin ORM (`appointments`, `automation_events` con
  `UNIQUE(event_id)`, índice parcial `ux_appointments_slot_open`,
  `schema_migrations`), `pg_advisory_xact_lock(719019)`, pasos versionados con
  `ON CONFLICT DO NOTHING` y `ensure_schema()` perezoso con reintento;
  `create_app()` tolera BD no disponible sin abortar y mantiene SQLite mientras
  dure la convivencia con T5/T6. Tests: TC-019-003/004/005/018/016; **369
  PASS** (364 + 5). El `@revisor` emitió **APROBADO** (RF-22..RF-27,
  CL-4/CL-5/CL-7); RF-23 queda base hasta T5/T6/T9. Observaciones no
  bloqueantes: sin `TEST_DATABASE_URL` son 364 PASS + 5 errores de setup (no
  skip); el intento eager de `ensure_schema()` puede esperar `connect_timeout`;
  un DSN malformado podría abortar el arranque; falta test automatizado de
  rollback mid-DDL; limpieza de esquemas best-effort; SQLite UTC pendiente en
  T5/T6; `CREATE TABLE IF NOT EXISTS` no altera tablas preexistentes. **T5
  autorizada después**. Sin commit ni push.
- **Spec 019 — T5 COMPLETADA y APROBADA (2026-11-09)**: repositorios de citas y
  eventos en dialecto PostgreSQL (`%s`, `RETURNING id`, `rowcount`, acceso por
  nombre) con adaptador mínimo SQLite `%s`→`?`; índice parcial y dedup
  `UNIQUE(event_id)` verificados en PostgreSQL real; `mark_sent()`/`created_at`
  UTC; `claim_failed_event()` atómico; sin reglas de negocio ni mensajes de
  usuario. Se corrigió antes de revisar una fuga de conexión/semáforo al usar
  `DatabaseTarget` dentro de contexto Flask (`_scope` cierra la instancia
  temporal; `Database` del llamador no se cierra); regresión
  `test_t5_target_scope_closes_connection_in_app_context`. Tests T5: **9
  PASS**; suite completa: **378 PASS / 0 FAIL**, sin `skip`. El `@revisor`
  emitió **APROBADO** para T5 (RF-4, RF-5, RF-6, RF-7, RF-10..RF-12, RF-14,
  RF-30; CL-8), con dependencias de T6/T7/T11/T12/T15 pendientes. Evidencia:
  `docs/evidencias/hu-019/persistence.md`. Observaciones no bloqueantes:
  limpiar `import sqlite3` sin uso en `appointments_repository.py`; ajustar el
  docstring de `insert_event()`; validar SQLite ≥ 3.35 y bases preexistentes en
  T14/T15; completar `mark_skipped` y atomicidad real en T11/T7; la nota
  histórica de `schema.md` sobre `localtime` se aclara en la evidencia T5.
  **T6+ no autorizadas.** Sin commit ni push.
- **Spec 019 — T6 COMPLETADA y APROBADA (2026-11-10)**: servicios de reserva,
  disponibilidad y cancelación reciben `DatabaseResource`; las rutas de citas,
  cancelación y admin resuelven el `Database` registrado en
  `app.extensions["consultorio.database"]` mediante `web/persistence.py`.
  `create_booking()` conserva el contrato y mapea **solo** la violación del
  índice único del slot a `SLOT_TAKEN`; `PersistenceUnavailable` y errores
  operativos (`OperationalError`/`InterfaceError` de SQLite y psycopg) se
  traducen a indisponibilidad, nunca a horario ocupado. Sin imports de
  `sqlite3` en servicios. TC-019-008 cubre el mapeo y la concurrencia de 8
  hilos (1 cita, 7 `SLOT_TAKEN`) contra PostgreSQL real; `TestConfig` mantiene
  la suite general en SQLite hasta T10/T11. Suite: **382 PASS / 0 FAIL**, sin
  `skip`; tests T6 **12 PASS**. El `@revisor` emitió **APROBADO** (RF-4, RF-5,
  RF-6, RF-14, RF-20, RF-21 en alcance T6; CL-8), sin defectos bloqueantes.
  Evidencia: `docs/evidencias/hu-019/t6-services.md`. Observaciones no
  bloqueantes: `create_app()` aún crea un SQLite no usado con backend
  PostgreSQL (retirar en T15/T18); anotaciones `database_path` en
  automation/email por alinear en T10/T11; `_is_unique_violation()` de eventos
  en SQLite acepta cualquier `IntegrityError` (acotar en T7); el 503/UX de
  indisponibilidad y el saneamiento de trazas quedan en T9; la paridad de
  disponibilidad en PostgreSQL queda en T10/T11. **T7+ no autorizadas.** Sin
  commit ni push.
- **Spec 019 — T7 COMPLETADA y APROBADA (2026-11-10)**: no fue necesario cambiar
  producción; T5/T6 ya garantizaban D5. `update_appointment_status_with_pending_event()`
  ejecuta `UPDATE` + `INSERT` del evento `pending` en un único
  `_scope(write=True)`/`Database.transaction()` sobre la misma conexión, con un
  solo commit o rollback completo; la publicación del evento de negocio y el
  correo ocurren después del commit. TC-019-009 se añadió a
  `tests/test_pg_persistence.py` con 3 pruebas contra PostgreSQL real:
  (1) misma conexión y commit único, (2) fallo real del `INSERT` por
  `UNIQUE(event_id)` con rollback y cita `confirmed`, (3) publicación solo
  después del commit, verificada desde conexión independiente. Regresión
  017/018 sin lógica de persistencia propia ni imports de `sqlite3` en
  servicios. Resultados: T7 **61 PASS**, regresión ampliada **90 PASS**, suite
  **385 PASS / 0 FAIL**, sin `skip`. El `@revisor` emitió inicialmente
  **CAMBIOS NECESARIOS** solo por sobreafirmar la paridad total de la suite y
  por volcados no reproducibles; corregida la evidencia, emitió **APROBADO**
  para el alcance T7. Evidencia: `docs/evidencias/hu-019/t7-atomicity.md`.
  La paridad total de la suite en PostgreSQL sigue pendiente de T10/T11/T12;
  las rutas 017/018 se prueban en SQLite hasta T11. Observación residual de T6:
  acotar `_is_unique_violation()` de eventos en SQLite. **T8+ no autorizadas.**
  Sin commit ni push.
- **Spec 019 — T8 COMPLETADA y APROBADA (2026-11-10)**: literal contractual
  `MSG_PERSISTENCE_UNAVAILABLE` añadido en
  `consultorio/content/appointment_content.py` con el texto exacto «No pudimos
  completar tu solicitud en este momento. Inténtalo de nuevo en unos minutos.»
  y espejo idéntico en `tests/expected_content.py`, con trazabilidad a RF-20 /
  RNF-5, D12, T8 y la enmienda coordinada de las Specs 004/005 (2026-11-08).
  TC-019-011 en `tests/test_hu_019.py` fija valor, espejo y permanencia de
  literales 004/005; no se consume aún en handlers/templates/JS (T9). Resultados:
  TC-019-011 **1 PASS**, content+HU-019 **8 PASS**, suite **386 PASS / 0 FAIL**,
  sin `skip`. `@revisor`: **APROBADO**, sin defectos; solo adiciones en los dos
  archivos de contenido. Evidencia: `docs/evidencias/hu-019/t8-literal.md`.
  **T9+ no autorizadas.** Sin commit ni push.
- **Spec 019 — T9 COMPLETADA Y APROBADA (2026-11-10)**: handler
  central `PersistenceUnavailable` → **503** (`consultorio/errors.py`), por
  endpoint: `appointments.horarios`/`appointments.disponibilidad` JSON
  `{"error": MSG_PERSISTENCE_UNAVAILABLE}`; resto plantilla
  `templates/errors/persistence_unavailable.html` con el literal y enlace a
  `/citas` etiquetado con `ADMIN_BACK_BUTTON` («Volver», sin copy nuevo).
  `availability.js` limpia horas y muestra el literal ante 503/no-2xx/red, sin
  badges «Ocupado» ni estados de día engañosos (mantiene `daySeq`/`hoursSeq`);
  la plantilla sirve el literal por `data-unavailable-message`. Rutas 004/017/
  018 cubiertas por el mismo handler, sin degradar a 404/409/cancelada/ocupada.
  Log constante sin DSN/PII. TC-019-010: **10 PASS** en
  `tests/test_pg_resilience.py` con fallo real del driver (DSN `127.0.0.1:1`);
  suite completa PostgreSQL **396 PASS / 0 FAIL**, sin `skip` (T8: 386).
  Evidencia: `docs/evidencias/hu-019/t9-unavailable.md`; capturas CDP
  `persistence-unavailable.png` (1280×900, sin desborde) y
  `persistence-unavailable-movil.png` (375×800, sin desborde).
  `docs/operaciones/postgresql.md` documenta el 503 y su reproducción. Servidor
  normal de revisión: http://127.0.0.1:5000/. **`@revisor` emitió APROBADO**
  (RF-20/RF-21/RNF-6 y CL-1/2/3/11 CUMPLE; suite reproducida 396 PASS; 503
  reproducido sin mocks; JS verificado estática y dinámicamente sin badges
  «Ocupado»); **T9 marcada `[x]` en `tasks.md`**. Observaciones no bloqueantes:
  el JS trata cualquier `!response.ok` como indisponibilidad (incluido 400);
  la prueba JS del repo es estática; el reporte CDP completo no está
  versionado; el test de logs no exige la presencia del warning; el
  reprogramado admin sigue sin atomicidad entre cancelar y crear (preexistente,
  plan D4/RF-6, para T12/T13). **Aceptación funcional de la usuaria:
  2026-11-10**, con esas observaciones no bloqueantes. **Commit de T9
   autorizado el 2026-11-10.** **T10 autorizada el 2026-11-10.** Sin push.
- **Spec 019 — T10 COMPLETADA Y APROBADA (2026-11-10)**:
  `tests/conftest.py` valida `TEST_DATABASE_URL` en `pytest_configure` (conexión
  real `SELECT 1`; sin `skip`; `pytest.exit` código 1 con instrucciones si falta
  o no conecta). Fixture `app`: `create_app(TempConfig)` con SQLite temporal
  (bootstrap sin tocar `public`), luego `Database(pg_target)` +
  `ensure_schema()`, sustitución en `app.extensions`, `PERSISTENCE_BACKEND=
  "postgres"` y cierre `close_request()` antes del `DROP SCHEMA`; esquema aislado
  `test_hu019_<uuid>` por test; nueva fixture `database`; `database_path` se
  conserva para T11. Migrados a PG: `test_appointment_persistence.py`,
  `test_hu_006.py`, `test_hu_007.py` y `test_hu_010.py` (catálogos
  `information_schema`/`pg_*`, `psycopg.errors.UniqueViolation`; sin
  `sqlite3.connect` directo). `TC-010-014` se reubicó sin cambios a
  `tests/test_rollback_sqlite.py` (verificación de rollback para T15, no
  paridad); la idempotencia PG sigue en TC-019-004/018. Resultados reales:
  T10+rollback **18 PASS**; PG existente+T10+rollback **32 PASS**; suite
  completa **372 PASS / 24 FAIL** (base 396), 24 fallos solo en archivos T11
  (`test_appointment_routes.py`, `test_availability_routes.py`,
  `test_double_booking_routes.py`, `test_hu_008.py`, `test_hu_017.py`) porque
  aún leen `app.config["DATABASE_PATH"]` (SQLite) mientras las rutas usan
  PostgreSQL. Sin esquemas `test_hu019_*` residuales; `public` con 0 filas de
  test. Evidencia: `docs/evidencias/hu-019/t10-fixtures.md` y
  `suite-postgres.txt`. Pendiente: T11 debe migrar esos 5 archivos y los que aún
  usan `database_path`; T15 registra el rollback aparte. **`@revisor` emitió
  APROBADO** (aislamiento y `public` intactos verificados; `TC-010-014`
  reubicado con cuerpo idéntico; lista de 24 fallos coincide con la evidencia;
  sin aserciones relajadas). Observaciones no bloqueantes: la suite sigue roja
  hasta T11; `docs/operaciones/postgresql.md` y un comentario de
  `config.py` aún describen la etapa SQLite (T16/cierre); `pytest_configure`
  bloquea también `--collect-only` sin BD (coherente con D9/CL-10);
  `pg_schema` silencia fallos de `DROP`; la fixture copia el DSN local a
  `config` (no imprimirlo). **T10 marcada `[x]` en `tasks.md` y commiteada en
  `673d799` (2026-11-10, autorizada por la usuaria); sin push.**
- **Spec 019 — T11 COMPLETADA Y APROBADA (2026-11-11)**: migrada a PostgreSQL
  la persistencia de los tests de servicios, rutas y HU de las Specs 004–018
  (`conftest.py` retira la fixture `database_path`; `Database.connection()`/
  `transaction()`, placeholders `%s`, catálogos PG e
  `is_slot_uniqueness_violation`). Sin cambios de producción
  (`git diff -- consultorio templates static app.py` vacío). **Suite completa:
  396 PASS / 0 FAIL / 0 skipped** (coordinador 406,69 s; revisor 181,51 s y
  180,17 s), 18 casos TC-018 (7 `test_hu_018.py`, 9 `test_admin_routes.py`,
  2 `test_admin_content.py`). Aislamiento verificado: 0 esquemas
  `test_hu019_*`, `public` con 0 filas y `schema_migrations` en 4. Revisor:
  **APROBADO**, con recuento mecánico de `assert` (sin relajaciones) y CL-10
  reprobado con DSN ausente/inalcanzable (exit 1, sin `skip`). Evidencia:
  `docs/evidencias/hu-019/t11-suite.md` y `suite-postgres.txt` (corrida real).
  Imprecisones documentales detectadas por el revisor (inventario de archivos,
  reparto de TC-018 y mención de la ruta SQLite) corregidas después en
  `t11-suite.md` y `docs/operaciones/postgresql.md`; solo documentación, sin
  efecto en código ni pruebas. **T11 marcada `[x]` en `tasks.md` y commiteada en
  `5419d4a` (2026-11-11, autorizada por la usuaria); sin push.**
- **Spec 019 — T12 COMPLETADA Y APROBADA (2026-11-11)**: añadido
  **TC-019-014** (`tests/test_hu_019.py`): 8 hilos reales con
  `threading.Barrier` sobre el mismo slot PostgreSQL → 1 cita, 7 `SLOT_TAKEN`,
  0 excepciones no controladas, 2 eventos `skipped` del ganador y limpieza
  efectiva del esquema aislado. Auditoría de no vacuidad TC-019-003..018:
  TC-019-003/005 refuerzan la igualdad exacta de tablas e índices; TC-019-018
  añade un paso aditivo real (versión 5, `ADD COLUMN IF NOT EXISTS`) sobre
  datos; TC-019-008 elimina el mock de `is_slot_taken` y provoca la violación
  real con una transacción bloqueante (poll de `pg_stat_activity`); TC-019-016
  añade el tramo de cold start. Mutación de no vacuidad reproducida por el
  revisor: sin el índice parcial, 8/8 reservas ganan; con él, 1 cita y 7
  `SLOT_TAKEN`. Suite: **397 PASS / 0 FAIL / 0 skipped** (coordinador 180,04 s;
  revisor 170,99 s). 0 esquemas residuales, `public` 0 filas y
  `schema_migrations` en 4. Revisor: **APROBADO**, sin aserciones relajadas.
  Evidencia: `suite-postgres.txt`, `schema.md`, `persistence.md`,
  `resilience.md` (nuevo, untracked hasta el commit). **T12 marcada `[x]` en
  `tasks.md`. Commit de T12 pendiente de autorización; T13+ no autorizadas.**
  Observaciones no bloqueantes: `tasks.md` T12 declara «CL-1..CL-11» pero CL-6
  (rollback) pertenece a T15/TC-019-021 según el plan → requiere decisión
  documental; CL-1/CL-3 se cubren de forma indirecta vía TC-019-010; el helper
  `_wait_for_blocked_booking_insert` usa un `sleep` de 0,02 s con timeout (sin
  flakiness observada); TC-019-014 hace `DROP SCHEMA` manual además del
  fixture. Sin cambios de producción ni dependencias. **T12 commiteada en
  `d1e7909` (2026-11-11); corrección autorizada de la línea «Cubre» de T12
  (CL-6 pasa a T15) incluida en ese commit; sin push.**
- **Spec 019 — T13 COMPLETADA Y APROBADA (2026-11-12)**: E2E real contra Neon
  desde entorno controlado con `create_app` (sin Render). TLS verificado en
  pooler y endpoint directo (`ssl_in_use=True`, `sslmode=require`); región
  `us-east-2`. **Plan Free verificado por el coordinador vía API Neon**
  (`subscription_type=free_v3`, proyecto `fragrant-silence-79082611`,
  PostgreSQL 18). Esquema creado desde `public` vacío por `ensure_schema()` y
  verificado contra el DDL aprobado (tablas, índice parcial,
  `UNIQUE(event_id)`, migraciones 1..4, defaults UTC). Reserva HTTP 303 +
  confirmación; cita y dos eventos `skipped` visibles desde conexión
  independiente. Cold start real de 360 s (`pg_postmaster_start_time()` cambió;
  disponibilidad 1,491 s y reserva 2,381 s). Limpieza: 0 filas y esquema
  conservado. Revisor: **APROBADO** (RF-1, RF-16, RNF-2/4/6; reprodujo el 503
  con pooler y el 200 con directo). Suite local: **397 PASS / 0 FAIL**
  (coordinador 179,41 s; revisor 181,01 s). Evidencia:
  `docs/evidencias/hu-019/e2e-neon.md`; operación:
  `docs/operaciones/postgresql.md`.
  **Bloqueo para T14 (riesgo alto, no defecto de T13):** la app envía
  `statement_timeout` como parámetro de arranque (`options` en
  `consultorio/persistence/database.py:728-742`) y el **pooler de Neon lo
  rechaza** (`unsupported startup parameter`); el DSN entregado es pooler y no
  sirve tal cual. **Decisión de la usuaria 2026-11-12: opción A**, usar el
  **endpoint directo** en la app y en Render (sin `-pooler`), sin cambio de
  código y sin tocar TLS; queda registrada en `plan.md` D11 y en `tasks.md`
  T14. Si Render no alcanzara el endpoint directo, se detendrá T14 y se pedirá
  decisión para fijar el timeout con `SET` tras conectar.
  **Incidente local resuelto:** el implementador rotó la contraseña del
  PostgreSQL Docker a un valor no registrado; el coordinador la restauró a
  `devlocal_password` y verificó TCP + suite. Observaciones documentales del
  revisor corregidas el 2026-11-12: plan Free/región verificados por API,
  derivación explícita del endpoint directo (`$env:T13_DIRECT_DSN`), aclaración
  de que `/citas/disponibilidad` no prueba la exclusión del slot (la prueba
  fuerte es `/citas/horarios`), alcance de `docs/operaciones` hasta T13 y nota
  de que el harness E2E no está versionado. **T13 marcada `[x]` en
  `tasks.md`. Commit de T13 pendiente de autorización; T14 no autorizada.**
  Sin push.

- **Spec 019 — T14 PREPARADA (2026-11-12, parte local)**: `render.yaml` con
  `region: ohio`, `PERSISTENCE_BACKEND=postgres`, `DATABASE_URL` con
  `sync: false` y sin valor, sin `DATABASE_PATH`, y se conservan `plan: free`,
  `PYTHON_VERSION=3.12.7`, `buildCommand`, `startCommand`, `healthCheckPath: /`
  y `SECRET_KEY` con `generateValue`. Nuevo `tests/test_render_manifest.py`
  (solo stdlib, sin PyYAML) que fija el contrato del manifiesto y la ausencia de
  DSN/credenciales. Documentado el despliegue en
  `docs/operaciones/postgresql.md` («Despliegue en Render», pasos 1–9:
  borrar/recrear en Ohio, secreto con endpoint directo, esquema, reserva,
  redespliegue y spin-down). Evidencia preliminar
  `docs/evidencias/hu-019/render-deploy.md` con despliegue, reserva, redespliegue
  y spin-down marcados **PENDIENTE**. Suite local PostgreSQL Docker:
  **398 PASS / 0 FAIL** (397 + 1). Sin cambios en producción (`consultorio/`,
  `templates/`, `static/`, `app.py`). **T14 NO completada**: requiere panel de
  Render (sin acceso desde el implementador) y que el `render.yaml` llegue a la
  rama del Blueprint. **Riesgo operativo:** borrar el servicio pierde las
  variables configuradas solo en el panel (webhook n8n, token admin);
  anotarlas antes y reintroducirlas sin registrarlas. Sin commit ni push.

- **Spec 019 — T14 EJECUTADA (2026-11-12, verificación real Render/Neon)**:
  `main` publicado en `dde4461` (`9846613..dde4461` con la API key de la
  usuaria). Servicio antiguo `srv-db6f4v0473hc73e9ovg0` (oregón, suspendido)
  eliminado por API; su URL `c6g6` da 404. Blueprint
  `exs-db6f05gn74is73aq3070` recreó `consultorio-psicologico`
  (`srv-dbr08jk9v7es73agc110`) en **ohio**, plan free, URL
  `https://consultorio-psicologico-z1o5.onrender.com`; estado `in_sync`.
  `DATABASE_URL` (endpoint directo) configurada por API sin registrarla; sin
  `DATABASE_PATH`; `PYTHON_VERSION=3.12.7`, `PERSISTENCE_BACKEND=postgres`.
  Build real: Python 3.12.7 + `psycopg 3.3.8`. Esquema Neon 1..4, índice
  parcial y `UNIQUE(event_id)`. Reserva ficticia `POST /citas` → 303 a
  `/citas/confirmada/3`, slot 10:00 ocupado y 2 eventos `skipped` en Neon.
  Redespliegue 18:29:14→18:30:07Z con cita y eventos intactos. Spin-down: 17 min
  sin tráfico (18:31→18:48Z), primera petición 200 en 32,7 s y datos intactos.
  Limpieza: 0 citas, 0 eventos, 4 migraciones. Evidencia completa en
  `docs/evidencias/hu-019/render-deploy.md`.
  **Incidente:** la usuaria borró el servicio de n8n en Render; asume su
  restauración. `AUTOMATION_WEBHOOK_URL`, `AUTOMATION_WEBHOOK_AUTH_HEADER` y
  `CONSULTORIO_ADMIN_TOKEN` no se reintrodujeron; los eventos quedan `skipped`.
  Fuera del alcance de Spec 019.
  **Revisión 2026-11-12:** `@revisor` emitió **APROBADO** (RF-1/2/3/15 y
  RNF-1/3/6/7 PASS; sin defectos bloqueantes). Correcciones documentales
  aplicadas: referencia a los 8 criterios de T14, nota de que el esquema se creó
  en T13, limitación de facturación y artefacto bruto de spin-down pendiente
  para T17. **T14 marcada `[x]` en `tasks.md`.**
  **Cierre:** commit `309a442` publicado en `main` (`dde4461..309a442`).
  `RENDER_API_KEY` retirada del entorno local el 2026-11-16 y revocada en el
  Dashboard de Render el 2026-11-17; no queda pendiente de seguridad. Observaciones
  abiertas para T17: n8n/variables de automatización y
  `CONSULTORIO_ADMIN_TOKEN` (RNF-5 y paridad funcional), repetir la suite
  completa y adjuntar extracto del primer GET tras el spin-down.

- **Spec 019 — T15 EJECUTADA (2026-11-13)**: rollback temporal a SQLite
  documentado y probado en local. `tests/test_rollback_sqlite.py` añade
  `TC-019-021`: cita en PostgreSQL aislado → cambio a `PERSISTENCE_BACKEND=sqlite`
  + `DATABASE_PATH` → cita PostgreSQL no visible → cita SQLite → vuelta a
  PostgreSQL con la cita original intacta y la fila SQLite **no** trasladada;
  además `create_app` con configuración SQLite y `DATABASE_URL=""` persiste en
  disco. `TC-010-014` se conserva íntegro. Suite completa: **399 PASS / 0 FAIL**
  (total de `tests/`, no solo paridad). Archivo de rollback: **2 PASS**. Nuevo
  procedimiento en `docs/operaciones/postgresql.md` (snapshot manual en Neon,
  hora de corte UTC, pérdida aceptada, disco efímero de Render, vuelta a
  PostgreSQL) y evidencia en `docs/evidencias/hu-019/rollback.md`.
  **Revisión 2026-11-13:** `@revisor` emitió **APROBADO** (RF-18, RF-19, RNF-7,
  CL-6 y RF-28 PASS; sin defectos bloqueantes). Observaciones no bloqueantes
  corregidas en la evidencia: precisión de datos ficticios, encuadre de los 399
  como total de suite y diferencia entre DSN conservado y `DATABASE_URL=""` en
  el test. **T15 marcada `[x]`; commit `87ab012` publicado en `main`.**
  **No se ejecutó rollback real sobre Render/Neon** ni snapshot real.

- **Spec 019 — T16 COMPLETADA Y APROBADA (2026-11-16)**: actualización
  documental de `specs/004_agendar-cita/plan.md`,
  `005_validar-dis-horarios`, `006_evitar-doble-reserva`,
  `007_automatizacion-reservas` y `010_notificar-cancelacion`, con evidencia
  `docs/evidencias/hu-019/plan-updates.md`. Menciones operativas a SQLite,
  `sqlite3`, `DATABASE_PATH`, `sqlite_master`, `PRAGMA` y `busy_timeout`
  sustituidas por `Database`/`ensure_schema()`/PostgreSQL; DDL históricos
  marcados; `TC-010-014` ubicado en `tests/test_rollback_sqlite.py`.
  Decisiones D2 (004), D1/D2/D3 (006), D11 (007) y D5 (010) conservadas con
  marca histórica; sin cambios de RF/CA/CL/literales. `@revisor`: **APROBADO**
  tras dos ciclos de corrección. 201+/142− en 5 planes; P1 30 y P2 9
  coincidencias, todas históricas o de rollback T15. **Commit `861e3f4`
  publicado en `main` (2026-11-16).**

- **Spec 019 — T17 QA EJECUTADO (2026-11-16)**: informe
  `docs/evidencias/hu-019/qa-hu-019.md` con matriz TC-019-001..023, comandos y
  resultados reales. Suite completa PostgreSQL Docker: **399 PASS / 0 FAIL /
  0 skipped**; `test_hu_019.py` + `test_rollback_sqlite.py`: **8 PASS**. Render
  `GET /`: **200** con cold start (~22,5 s). PostgreSQL 16.15, Python 3.14.6,
  psycopg 3.3.8. `@revisor`: **APROBADO** (sin defectos bloqueantes; 3
  observaciones menores corregidas). n8n real sigue **NO VERIFICADO** por el
  incidente, limitación externa divulgada. **Aceptación funcional emitida por la
  usuaria el 2026-11-16** con esa limitación; T17 marcada `[x]`. **Commit y push
  autorizados; T18 autorizada e iniciada el 2026-11-16.**

- **Spec 019 — T18 RETIRADA SQLITE COMPLETADA (2026-11-17)**: retirados
  `PERSISTENCE_BACKEND`, `DATABASE_PATH`, el DDL SQLite, `init_db`,
  `get_connection`, el adaptador `%s`→`?` y las ramas de backend; `render.yaml`
  sin variables SQLite; documentación operativa centrada en PostgreSQL. Suite
  completa PostgreSQL Docker: **392 PASS / 0 FAIL / 0 skip** (implementador
  `188.84s`; corrida independiente del coordinador `192.92s`). `@revisor`:
  **APROBADO** sin defectos bloqueantes; no pudo repetir la suite por no tener
  Docker activo y se apoyó en la corrida independiente. Observaciones menores
  corregidas: test `init_db` renombrado, `DATA_DIR` retirado, cifras de la
  evidencia y referencia obsoleta a T14. Evidencia:
  `docs/evidencias/hu-019/t18-removal.md`; T18 marcada `[x]`. **Commit
  `61f358a` publicado en `origin/feature/hu-019-migracion-postgres`
  (2026-11-17).** La `RENDER_API_KEY` local fue retirada y la usuaria confirmó
  su revocación en el panel de Render (2026-11-17); no queda pendiente de
  seguridad. Quedan `data/consultorio.db*` locales ignorados por Git y sin
  referencias en código.
