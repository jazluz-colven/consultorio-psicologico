# MEMORY.md — Página web para el Consultorio de Psicología Carolina Gómez

Memoria del proyecto entre sesiones. Máximo ~50 líneas: resume o elimina lo que ya no
aporte.

## Estado actual
- Versión 1.0 - En desarrollo
- **HU-001 (Spec 001) implementada**: portada con identidad, imagen representativa,
  resumen de servicios, frase de valores, marca secundaria «Contenidas» y menú de 6
  accesos. Rama `feature/hu-001`.
- Tests: **29 PASS / 0 FAIL** (`python -m pytest -q`), Python 3.14.8 + Flask 3.1.3 +
  pytest 9.1.1.
- Specs y plan en `specs/001_visualizar-pinicio/`.
- Commits en `feature/hu-001`: `2ebaa46` (docs), `85a0e9d` (feat), `3203047` y
  `aa5379c`. **Sin remoto configurado**: no se puede hacer push.
- **Cambio tipográfico aplicado y sin commitar**: portada en Palatino, párrafo del
  hero justificado (solo `.hero__intro`), **cuerpo base 18 px** (`html { font-size:
  112.5% }`, escala 1.125× en todos los `rem`; cortes `px` intactos) y h1 del hero
  equilibrado con `text-wrap: balance`. Decisiones en `docs/design-typography.md`,
  D10 del plan actualizada.

## Decisiones (y por qué)
- **Sin SQLite en HU-001**: la portada no escribe datos; el contenido vive en
  `consultorio/content/` (constitución #1, nada por conveniencia). La capa
  `persistence/` se crea con la primera HU que use BD.
- **Spec 001 con textos literales contractuales** (Q8): cambiar un copy obliga a PR de
  spec primero; `tests/expected_content.py` es su espejo.
- **Rutas placeholder** `/nosotros`, `/servicios`, `/articulos`, `/contacto`, `/citas`
  responden 200 con «Sección en construcción» (Q1); cada HU posterior sustituye su
  plantilla.
- **Sin botón CTA en el hero**; «Agendar cita» vive solo en el menú.
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
  `C:\Users\Jaz\AppData\Local\Temp\opencode\capture_cdp.ps1`.

## Próximos pasos
- Commit pendiente en `feature/hu-001`: `static/css/main.css`, `docs/design-typography.md`,
  `specs/001_visualizar-pinicio/plan.md` y evidencia regenerada (29 tests PASS, 27
  comprobaciones de contrato PASS, `qa-hu-001.md` actualizado).
- Solicitar aceptación de HU-001; configurar remoto y hacer push cuando exista.
- Regenerar las capturas `*-devtools.png` (siguen mostrando la tipografía anterior).
- Arrancar HU-002 (Nosotros) sustituyendo el placeholder correspondiente.
