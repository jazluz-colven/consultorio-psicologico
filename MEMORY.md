# MEMORY.md — Página web para el Consultorio de Psicología Carolina Gómez

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no
aporte.

## Estado actual
- Versión 1.0 - En desarrollo
- **HU-001 (Spec 001) implementada y ACEPTADA** (2026-10-07): portada con identidad,
  imagen representativa, resumen de servicios, frase de valores, marca secundaria
  «Contenidas» y menú de 6 accesos. Rama `feature/hu-001`.
- **HU-002 (Spec 002) implementada con evidencia PASS** (2026-10-07, `feature/hu-002`):
  `/nosotros` con Misión/Visión/Experiencia/Valores según literales de la spec;
  **PENDIENTE de aceptación**.
- Tests: **45 PASS / 0 FAIL** (`python -m pytest -q`), Python 3.14.8 + Flask 3.1.3 +
  pytest 9.1.1 (29 de HU-001 + 16 de HU-002).
- Specs y plan en `specs/001_visualizar-pinicio/`.
- Commits: remoto `origin` (github.com/jazluz-colven/consultorio-psicologico);
  HU-001 cerrada en `ba23658`; HU-002: `c71c78c` (spec+plan), `f782797` (feat),
  `a686a58` (plan) y cierre de evidencia en el commit correspondiente.
- **Tipografía vigente y commitada**: portada en Palatino, párrafo del hero justificado
  (solo `.hero__intro`), **cuerpo base 18 px** (`html { font-size: 112.5% }`, escala
  1.125× en todos los `rem`; cortes `px` intactos) y h1 del hero equilibrado con
  `text-wrap: balance`. Decisiones en `docs/design-typography.md`, D10 del plan.
- **Evidencia DevTools regenerada y commiteada** (2026-10-07, `434ef1e`):
  `escritorio-1280-devtools.png` y `movil-375-devtools.png` (1028×563) muestran la
  tipografía actual, toolbar real «Responsive 1280 × 650» / «375 × 512» y menú desplegado.

## Decisiones (y por qué)
- **Sin SQLite en HU-001**: la portada no escribe datos; el contenido vive en
  `consultorio/content/` (constitución #1, nada por conveniencia). La capa
  `persistence/` se crea con la primera HU que use BD.
- **Spec 001 con textos literales contractuales** (Q8): cambiar un copy obliga a PR de
  spec primero; `tests/expected_content.py` es su espejo.
- **Rutas placeholder** (Q1) ahora solo `/servicios`, `/articulos`, `/contacto`,
  `/citas` responden «Sección en construcción»; `/nosotros` fue sustituida por HU-002
  (`PLACEHOLDER_SECTIONS` ajustado, D11).
- **Sin botón CTA en el hero**; «Agendar cita» vive solo en el menú.
- **Todos los párrafos justificados** (regla permanente del usuario, 2026-10-07;
  en `docs/design-typography.md` y `AGENTS.md`): `text-align: justify` + `hyphens: none`
  (sin guiones ni cortes de palabras), ajustados al cajón. Aplicado en `/nosotros` y
  en la portada (`.hero__intro`, tarjetas, frase de valores, pie).
- Colores de la ilustración NO se usan como colores de UI: paleta Serenidad Natural
  intacta (solo los 6 hex aprobados).

## Aprendizajes y errores a evitar
- `pip` está **bloqueado por AppLocker**: usar `python -m pip install ...`.
- El archivo de imagen llegó como `hero-contenidas.png.png`; comprobar nombres dobles.
- El PNG de la portada mide 720×713 (usado en `width`/`height` del `<img>`).
- Si se sube una imagen con fondo blanco, se verá una caja sobre `#F7F3EA`: pedir fondo
  transparente.
- **Chrome 154 headless no renderiza a menos de 500 px**: `--window-size=375` recorta la
  imagen de 500 px y la maqueta parece desbordada (no lo está). Para capturas exactas
  usar DevTools Protocol (`Emulation.setDeviceMetricsOverride`); script de apoyo en
  `C:\Users\Jaz\AppData\Local\Temp\opencode\capture_cdp.ps1` (miden `scrollHeight` con
  `Runtime.evaluate` antes de capturar).
- **Jinja + claves de dict con nombre de método**: `{{ d.values }}` resuelve al método
  `dict.values`, no a la clave; usar `{{ d["values"] }}` (bug visto en HU-002).
- **Servidor para revisión**: tras toda tarea/modificación visible, dejar
  `python app.py` en marcha y comunicar la URL (regla añadida a `AGENTS.md`).

## Próximos pasos
- **PENDIENTE**: aceptación de HU-002 (checkbox en `docs/evidencias/hu-002/qa-hu-002.md`);
  evidencia y push ya hechos. Tras aceptar, valorar HU-003 (Servicios).
