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
- Tests: **118 PASS / 0 FAIL** (`python -m pytest -q`), Python 3.14.8 + Flask
  3.1.3 + pytest 9.1.1 (102 previos + 16 nuevos TC-005-001..016).
  TC-001-004 acotado al `<figure>` del hero y TC-001-008 a formularios que no
  sean el buscador.
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
  **Aceptada por la usuaria el 2026-10-09 (T18) y mergeada a `main`.**
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

## Decisiones (y por qué)
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
- `pip` está **bloqueado por AppLocker**: usar `python -m pip install ...` (así se
  instaló Pillow 12.3.0 para convertir imágenes; es herramienta del entorno, no
  dependencia del proyecto).
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
- **HU-006 (Spec 006, evitar doble reserva) EN EJECUCIÓN**: `plan.md` aprobado
  (Q1–Q5, 2026-10-09) y `task.md` con T1–T17; flujo: cierre HU-005 → rama
  `feature/hu-006` → enmienda de la spec → código/tests → evidencia.
- Servidor de revisión en marcha: http://127.0.0.1:5000/citas
- HU-006 se apoya en el `UNIQUE` de HU-004 (concurrencia).
