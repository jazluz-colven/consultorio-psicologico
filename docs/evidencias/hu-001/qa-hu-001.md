# Evidencia QA — HU-001 (Spec 001 · Visualizar la página de inicio)

**HU:** HU-001
**Rama:** `feature/hu-001`
**Commits:** `2ebaa46` (docs), `85a0e9d` (feat), `3203047` (docs), `aa5379c` (evidencia),
`4c1266a` (tipografía), `6b7dc3f` (evidencia regenerada), `434ef1e` (evidencia DevTools)
**Fecha:** 2026-10-07 (actualizada tras el cambio tipográfico)

## Resumen

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **29 PASS / 0 FAIL** |
| Contrato HTTP y semántica | script de verificación sobre `test_client()` | **27 PASS / 0 FAIL** |
| Servidor de desarrollo | `GET http://127.0.0.1:5000/` | **200** |
| Evidencia visual | `docs/evidencias/hu-001/*.png` | **4 archivos, PASS** |

## Cambio tipográfico verificado en esta iteración

La portada adopta **Palatino** (`static/css/main.css`, `body { font-family: ... }`), el
párrafo del hero queda **justificado** de forma acotada (solo `.hero__intro`) y la base
tipográfica sube de **16 px a 18 px** con `html { font-size: 112.5% }`, según la
decisión documentada en `docs/design-typography.md` y reflejada en la D10 de
`specs/001_visualizar-pinicio/plan.md`.

Comprobaciones objetivas sobre `escritorio-1280.png` y `movil-375.png`:

- Justificación: los bordes derechos de las líneas completas del párrafo del hero son
  619 / 613 / 618 / 619 / 613 px y la última línea corta termina en 168 px.
- Cuerpo ampliado: el volumen de texto crece de forma medible respecto a la captura
  anterior (p. ej. RF-6 en móvil pasa de 1344 a 1671 px de texto y el pie de 575 a
  722), coherente con la escala 1.125×.
- Título del hero equilibrado con `text-wrap: balance`: en escritorio la línea 1 mide
  464 px y la línea 2 318 px, en lugar de una primera línea larga y «Gómez» solo.
- `python -m pytest -q` → 29 PASS después del cambio.

## Cobertura de RF

| RF | Verificación | Resultado |
|---|---|---|
| RF-1 presentación clara | `<h1>`, `<p>` e `<title>` con literales de la spec | PASS |
| RF-2 imagen representativa | `<img>` con `src` resuelto y `alt` literal, 720×713, archivo existe | PASS |
| RF-3 accesos a secciones | 6 enlaces en `<nav>`; cada `href` responde 200 | PASS |
| RF-4 orientación institucional | sin `<form>`/`<input>`/admin; `POST /` → 405 | PASS |
| RF-5 resumen de servicios | bloque completo + enlace «Ver todos los servicios» → 200 | PASS |
| RF-6 frase de valores | literal presente en `GET /` y texto visible en la banda de valores | PASS |
| RF-7 marca secundaria | «Contenidas» visible y precede al `<h1>` | PASS |
| RNF-1 responsive | `viewport`, `width`/`height` en `<img>`, `@media (max-width…)` | PASS |
| RNF-2 paleta coherente | únicamente los 6 hex aprobados en `main.css` | PASS |
| CL-1 imagen no disponible | fallback a `placeholder.svg` conservando el `alt` | PASS |
| CL-2 contenido incompleto | `validate_content`/`validate_services` completan desde defaults | PASS |
| CL-3 sección no disponible | `/nosotros`, `/servicios`, `/articulos`, `/contacto`, `/citas` → 200 «en construcción» | PASS |

## Evidencia visual

| Archivo | Dimensiones | Contenido comprobado | Resultado |
|---|---|---|---|
| `escritorio-1280.png` | 1280×1900 | cabecera (y=0-135) **sin botón «Menú»** (0 px salvia en la zona de nav), hero (y=136-597) con imagen (89 784 px fuera de fondo), servicios/tarjetas (y=598-881), botón (y=882-935), RF-6 (y=981-1067, 1660 px de texto) y pie RF-7 (y=1149-1267, 748 px de texto) | PASS |
| `movil-375.png` | 375×2800 | cabecera con marca (y=0-131) y botón «Menú» (y=133-177), nav cerrado (0 px de texto en y=179-221), hero (y=222-1108), «Nuestros servicios» (y=1109-1219), tarjetas (y=1220-1422 e y=1446-1649), botón (y=1677-1730), RF-6 (y=1776-1994, 1671 px de texto) y pie RF-7 (y=2067-2214, 722 px de texto) | PASS |
| `escritorio-1280-devtools.png` | 1028×563 | Toolbar real de DevTools «Dimensions: Responsive **1280 × 650** · Fit to window · No throttling» + regla + viewport **sin botón «Menú»** (`display: none` comprobado por DOM), hero con h1 equilibrado e intro justificada en Palatino y base 18 px | PASS |
| `movil-375-devtools.png` | 1028×563 | Toolbar real «Dimensions: Responsive **375 × 512**» + viewport con la marca, botón «Menú» y **nav desplegada** (`aria-expanded=true`, `is-open`), hero sage visible; Palatino y base 18 px | PASS |

Las dos capturas completas se generan con Chrome headless **vía DevTools Protocol**
(`Emulation.setDeviceMetricsOverride` + `Page.captureScreenshot`), por lo que el ancho
renderizado es exactamente 1280 y 375 px. La presencia y posición de cada bloque se
verificó por muestreo de color (bandas de fila) y conteo de píxeles de texto, no por
inspección visual. El estado inicial del nav en móvil está comprobado además por código:
`base.html` no incluye la clase `is-open` y `main.css` aplica `display: none` bajo
`@media (max-width: 767px)`.

Las dos capturas `*-devtools.png` se regeneraron el 2026-10-07 desde una **ventana real
de Chrome** (perfil de depuración, DevTools abierto y acoplado abajo, device toolbar
activo) usando `PrintWindow`, recortando solo el área de página (x=8, y=87, 1028×563 px)
para excluir la barra del navegador y los paneles de DevTools. Verificación: `btnDisplay:
'none'` y `base: 18px`/`font: Palatino` leídos por DOM en 1280, y `aria-expanded: true`
con clase `is-open` en 375; geometría por muestreo de píxeles (viewport 375×512 a zoom
100 % centrado con margen de fondo a ambos lados).

Geometría comprobada en `movil-375.png`: el hero termina en x≈356 y el fondo de página
ocupa x≥362 (padding de 24 px), es decir, sin desbordamiento horizontal a 375 px.

## Defectos encontrados

- Ninguno funcional. La única incidencia funcional detectada en la revisión visual
  (botón «Menú» visible en escritorio) fue corregida en `static/css/main.css` y está
  verificada en `escritorio-1280.png`.
- **Defecto de metodología corregido**: las capturas anteriores se hacían con
  `chrome --headless --window-size=375,2800`, pero Chrome 154 limita la ventana a un
  mínimo de 500 px y recorta la imagen al ancho pedido; por eso el contenido aparecía
  cortado en el borde derecho. No era un fallo de la maqueta (la captura DevTools a 375
  y la geometría CDP lo demuestran). Las capturas se regeneraron con emulación CDP.

## Pendientes de cierre

- [x] Commit del cambio tipográfico y de la evidencia regenerada.
- [x] Commit de la evidencia DevTools `*-devtools.png` regenerada (`434ef1e`, 2026-10-07).
- [x] Aceptación de la HU (2026-10-07).

## Veredicto

**PASS** — los 29 tests y las 27 comprobaciones de contrato están en verde tras el
cambio tipográfico, y la evidencia visual regenerada cubre la totalidad de los RF y los
casos límite con anchos de render exactos. HU aceptada por el usuario el 2026-10-07:
**HU-001 CERRADA**.
