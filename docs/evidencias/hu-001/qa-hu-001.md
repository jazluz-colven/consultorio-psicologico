# Evidencia QA — HU-001 (Spec 001 · Visualizar la página de inicio)

**HU:** HU-001
**Rama:** `feature/hu-001`
**Commits:** `2ebaa46` (docs), `85a0e9d` (feat), `3203047` (docs), `aa5379c` (evidencia),
`4c1266a` (tipografía), `6b7dc3f` (evidencia regenerada), `434ef1e` (evidencia DevTools),
`8103b91` (justificación generalizada sin guiones)
**Fecha:** 2026-10-07 (actualizada tras la justificación generalizada del sitio)

## Resumen

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **45 PASS / 0 FAIL** (29 de HU-001 + 16 de HU-002) |
| Contrato HTTP y semántica | script de verificación sobre `test_client()` | **28 PASS / 0 FAIL** |
| Servidor de desarrollo | `GET http://127.0.0.1:5000/` | **200** |
| Evidencia visual | `docs/evidencias/hu-001/*.png` | **4 archivos, PASS** |

## Cambio tipográfico verificado en esta iteración

La portada adopta **Palatino** (`static/css/main.css`, `body { font-family: ... }`) y la
base tipográfica sube de **16 px a 18 px** con `html { font-size: 112.5% }` (decisión
documentada en `docs/design-typography.md`, D10 de `specs/001_visualizar-pinicio/plan.md`).

Desde `8103b91` la justificación se **generalizó a todo el sitio** con
`text-align: justify` + `hyphens: none` (sin guiones ni cortes de palabras) en
`.hero__intro`, `.service-card__summary`, `.values__line` y `.site-footer`
(ambas reglas permanentes recogidas en `AGENTS.md`).

Verificación por CDP DOM (`Runtime.evaluate` + `Emulation.setDeviceMetricsOverride`,
viewport exacto) sobre `/`:

| Elemento | 1280 px | 375 px |
|---|---|---|
| `.hero__intro` | justify + `hyphens: none`, líneas 540·540·540·101 | justify + none, 7 líneas de 285 + 210 |
| `.service-card__summary` | justify + none, 551·341 | justify + none, 288·288·288·81 |
| `.values__line` | justify + none, 1120 (línea única) | justify + none, 285·285·285·285·230 |
| `.site-footer p` | justify, 428 (línea única) | justify, 321·161 |
| `scrollWidth` | 1280 (sin desbordamiento) | 375 (sin desbordamiento) |

Verificación por muestreo de píxeles sobre `escritorio-1280.png` (bordes de línea):

- Título del hero equilibrado con `text-wrap: balance`: la línea 1 mide 464 px
  (x 83..547) y la línea 2 318 px (x 83..401).
- Intro del hero: líneas completas terminan en x=620 / 619 / 620 y la última corta en
  180 (justificación sin guiones visibles).
- Tarjeta «Psicología Integral»: título en 56..238, línea 1 del resumen en 56..605
  (borde derecho parejo) y línea 2 corta en 56..394.
- `python -m pytest -q` → 45 PASS después del cambio (29 propios intactos).

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
| `escritorio-1280.png` | 1280×1268 | cabecera (y=0-135) **sin botón «Menú»** (DOM: `display: none` ≥768 px), hero (y=136-597) con imagen, h1 equilibrado e intro justificada (bordes 620/619/620, última línea 180), servicios/tarjetas (y=598-881) con resumen justificado (línea 1 en x56..605), botón (y=882-935), RF-6 (y=981-1067) y pie RF-7 (y=1149-1267) con texto justificado | PASS |
| `movil-375.png` | 375×2215 | cabecera con marca (y=0-131) y botón «Menú» (y=133-177; DOM: `display: block` con `.site-nav` oculto, nav cerrada), hero (y=222-1108), «Nuestros servicios» (y=1109-1219), tarjetas (y=1220-1422 e y=1446-1649), botón (y=1677-1730), RF-6 (y=1776-1994; 4 líneas a x45..328 + última corta) y pie RF-7 (y=2067-2214; línea 1 a x28..347), todo justificado y sin guiones; `scrollWidth`=375 | PASS |
| `escritorio-1280-devtools.png` | 1028×563 | Toolbar real de DevTools «Dimensions: Responsive **1280 × 650** · Fit to window · No throttling» + regla + viewport **sin botón «Menú»** (`display: none` comprobado por DOM), hero con h1 equilibrado e intro justificada (muestreo: bordes 499/499/500, última línea 192) y mismos cortes de línea que la captura completa | PASS |
| `movil-375-devtools.png` | 1028×563 | Toolbar real «Dimensions: Responsive **375 × 512**» + viewport con la marca, botón «Menú» y **nav desplegada** (`aria-expanded=true`, `is-open`), hero sage visible; Palatino y base 18 px | PASS |

Las dos capturas completas se regeneraron el 2026-10-07 tras `8103b91` con Chrome
headless **vía DevTools Protocol** (`Emulation.setDeviceMetricsOverride` +
`Page.captureScreenshot`, perfil limpio en el puerto 9445 para evitar CSS en caché), con
las alturas exactas medidas por `scrollHeight` (1268 px a 1280 y 2215 px a 375, sin
holgura inferior): los anchos renderizados son exactamente 1280 y 375 px y la emulación
se fija en la misma sesión CDP que toma la captura. La presencia y posición de cada
bloque se verificó por muestreo de píxeles (bandas de fila, bordes de línea y
conteo) combinado con lectura DOM (`Runtime.evaluate`), no por inspección visual. El
estado inicial del nav está comprobado por DOM en ambos viewports: botón «Menú»
`display: none` en 1280 y `display: block` con `.site-nav { display: none }` en 375,
coherente con `base.html` (sin `is-open`) y `@media (max-width: 767px)`.

Las dos capturas `*-devtools.png` **no necesitaron regenerarse**: se verificaron por
muestreo de píxeles que la intro del hero aparece justificada (bordes 499/499/500) con
los mismos cortes de línea que la captura completa nueva (la pasada de `hyphens: auto`
a `none` no alteró el render de la portada) y que el resto de su contenido (toolbar de
DevTools, nav) no depende de la tipografía. Se conservan tal cual, tomadas el
2026-10-07 desde una **ventana real de Chrome** (perfil de depuración, DevTools abierto
y acoplado abajo, device toolbar activo) con `PrintWindow`, recortando solo el área de
página (x=8, y=87, 1028×563 px). Verificación adicional: `btnDisplay: 'none'` y
`base: 18px`/`font: Palatino` leídos por DOM en 1280, y `aria-expanded: true` con clase
`is-open` en 375.

Sin desbordamiento horizontal en móvil comprobado por DOM: `scrollWidth` = 375 px
(igual que el viewport pedido) en `/` y `/nosotros`.

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

**PASS** — la suite (45 tests: los 29 de HU-001 intactos) y las 28 comprobaciones de
contrato están en verde tras la justificación generalizada sin guiones
(`8103b91`), y la evidencia visual regenerada (alturas exactas 1268/2215) cubre la
totalidad de los RF y los casos límite con anchos de render exactos. HU aceptada por el
usuario el 2026-10-07: **HU-001 CERRADA**.
