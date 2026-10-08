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
- **HU-003 (Spec 003) EN EVIDENCIA** (2026-10-08, rama `feature/hu-003` nacida de
  `main` tras merge de HU-002): página `/servicios` con los 2 servicios (catálogo +
  servicio + blueprint + plantilla + CSS `.services-page-*`), fallback por campo,
  404 de subrutas. Veredicto QA **PASS** en `docs/evidencias/hu-003/qa-hu-003.md`;
  capturas `escritorio-1280.png` (1280×1398) y `movil-375.png` (375×1965).
  Commits: `e6ad118` plan/tasks, `6440e74` spec, `72167bd` espejo, `84169a4` catálogo,
  `18f5a85` tests contenido, `c16a098` servicio, `5b5dbdb` tests servicio,
  `66d980a` web+plantilla, `5be6b48` CSS, `249dae6` tests ruta, `6d4a5f4` tests HU,
  `6f2a9c4` regresión, `6992364` evidencia+memory (push OK). Pendiente: aceptación
  de la usuaria.
- Tests: **61 PASS / 0 FAIL** (`python -m pytest -q`), Python 3.14.8 + Flask 3.1.3 +
  pytest 9.1.1 (29 de HU-001 + 16 de HU-002 + 16 de HU-003). Contrato HU-001: 28 PASS.
- **Tipografía vigente**: Palatino, cuerpo base 18 px, h1 con `text-wrap: balance` y
  **justificación generalizada a todo el sitio** (`text-align: justify` +
  `hyphens: none`, sin guiones). Decisiones en `docs/design-typography.md`
  (D10 del plan 002); reglas permanentes en `AGENTS.md`.
- **Evidencia visual HU-001/002** (2026-10-07): `hu-001/escritorio-1280.png` 1280×1268,
  `hu-001/movil-375.png` 375×2215, `hu-002/*.png` 1280×1394 y 375×1903; los
  `*-devtools.png` se conservan (verificados por píxeles).
- Servidor de revisión en marcha: `python app.py` → http://127.0.0.1:5000/
  (`/servicios` responde 200).

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
- HU-003 en evidencia (QA PASS 2026-10-08): falta **push de la evidencia y
  aceptación de la usuaria** (`qa-hu-003.md` checkbox). Después: siguiente HU según
  prioridad (spec y plan primero, regla de oro SDD).
