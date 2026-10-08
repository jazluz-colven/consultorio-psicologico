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
- **HU-016 (Spec 016) + enmienda de identidad IMPLEMENTADAS, en espera de
  aceptación** (2026-10-08, rama `feature/identidad-buscador`): nombre
  **«Carolina Gómez»** en todo el sitio, cabecera con logotipo
  `hero-contenidas.png` + nombre, hero con `hero-presentacion.png` (380×511,
  marco elíptico 50 %), tipografía **Open Sans** (Google Fonts por `@import`),
  y **buscador** `GET /buscar` (etiqueta oculta, D9; cabecera responsive
  768-1199, D10). Commits: `d0e2d4c` docs, `ed36013` feat, `f53282d` tests;
  evidencia en `docs/evidencias/hu-016/qa-hu-016.md` (veredicto PASS, sin PNG
  por Q6). Specs/plans 001-003 enmendados; `docs/design-identity.md` nuevo.
- Tests: **74 PASS / 0 FAIL** (`python -m pytest -q`), Python 3.14.8 + Flask 3.1.3 +
  pytest 9.1.1 (63 previos de HU-001/002/003 + 11 nuevos TC-016-001..011).
  TC-001-004 acotado al `<figure>` del hero y TC-001-008 a formularios que no
  sean el buscador.
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
- **Sin SQLite hasta que una HU lo pida**: contenido en `consultorio/content/`
  (constitución #1); `persistence/` se crea con la primera HU con BD.
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
- **Jinja + claves de dict con nombre de método**: `{{ d.values }}` resuelve a
  `dict.values`; usar `{{ d["values"] }}` (bug HU-002).
- El lector de imágenes del asistente puede adjuntar ficheros equivocados/caché:
  verificar siempre por medidas programáticas (DOM + muestreo de píxeles), no a ojo.
- **Servidor para revisión**: tras toda tarea visible, dejar `python app.py` en marcha
  y comunicar la URL (regla en `AGENTS.md`).

## Próximos pasos
- HU-016 implementada y en verde (74 PASS); **falta aceptación de la usuaria**
  (checkbox de `qa-hu-016.md`) y, al comenzar la siguiente HU, **merge
  `feature/identidad-buscador` → `main`** y crear su rama desde `main` (Q4/T1).
- Preguntas abiertas de HU-016: ninguna (Q1-Q6 cerradas en el plan 016).
