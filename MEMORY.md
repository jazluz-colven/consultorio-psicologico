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
- Commits en `feature/hu-001`: `2ebaa46` (docs) y `85a0e9d` (feat). **Sin remoto
  configurado**: no se puede hacer push.

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

## Próximos pasos
- Evidencia de HU-001 **completa y PASS**: `docs/evidencias/hu-001/`
  (`escritorio-1280.png`, `movil-375.png`, `*-devtools.png`, `qa-hu-001.md`).
- Solicitar aceptación de HU-001; configurar remoto y hacer push cuando exista.
- Arrancar HU-002 (Nosotros) sustituyendo el placeholder correspondiente.
