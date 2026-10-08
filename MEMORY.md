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
- Tests: **45 PASS / 0 FAIL** (`python -m pytest -q`), Python 3.14.8 + Flask 3.1.3 +
  pytest 9.1.1 (29 de HU-001 + 16 de HU-002). Contrato HU-001: 28 PASS (script
  actualizado tras implementarse `/nosotros`).
- **Tipografía vigente**: Palatino, cuerpo base 18 px, h1 con `text-wrap: balance` y
  **justificación generalizada a todo el sitio** (`text-align: justify` +
  `hyphens: none`, sin guiones): `.hero__intro`, `.service-card__summary`,
  `.values__line`, `.site-footer`, `.about__text`. Decisiones en
  `docs/design-typography.md` (D10 del plan); reglas permanentes en `AGENTS.md`.
- **Evidencia visual regenerada** (2026-10-07): `hu-001/escritorio-1280.png` 1280×1268,
  `hu-001/movil-375.png` 375×2215, `hu-002/*.png` 1280×1394 y 375×1903 (alturas exactas,
  sin holgura); los `*-devtools.png` se conservan (verificados por píxeles).
- Servidor de revisión en marcha: `python app.py` → http://127.0.0.1:5000/.

## Decisiones (y por qué)
- **Sin SQLite hasta que una HU lo pida**: contenido en `consultorio/content/`
  (constitución #1); `persistence/` se crea con la primera HU con BD.
- **Spec 001/002 con textos literales contractuales** (Q8): cambiar un copy obliga a PR
  de spec primero; `tests/expected_content.py` es su espejo.
- **Rutas placeholder** (Q1): ahora solo `/servicios`, `/articulos`, `/contacto`,
  `/citas` responden «Sección en construcción»; `/nosotros` la sustituyó (D11).
- **Sin botón CTA en el hero**; «Agendar cita» vive solo en el menú.
- **Todos los párrafos justificados y sin guiones** (regla permanente del usuario,
  2026-10-07): `justify` + `hyphens: none`, ajustados al cajón.
- Colores de la ilustración NO se usan como UI: paleta Serenidad Natural intacta
  (solo los 6 hex aprobados).

## Aprendizajes y errores a evitar
- `pip` está **bloqueado por AppLocker**: usar `python -m pip install ...`.
- Imagen de portada: 720×713; llegó `hero-contenidas.png.png` (nombres dobles); fondo
  blanco se ve como caja sobre `#F7F3EA`.
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
- HU-002 cerrada (aceptada 2026-10-07). Siguiente: **HU-003 (Servicios)** — spec y
  plan primero (regla de oro SDD).
