# Evidencia QA — HU-001 (Spec 001 · Visualizar la página de inicio)

**HU:** HU-001
**Rama:** `feature/hu-001`
**Commits:** `2ebaa46` (docs), `85a0e9d` (feat), `3203047` (docs)
**Fecha:** 2026-10-07

## Resumen

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **29 PASS / 0 FAIL** |
| Contrato HTTP y semántica | script de verificación sobre `test_client()` | **27 PASS / 0 FAIL** |
| Servidor de desarrollo | `GET http://127.0.0.1:5000/` | **200** |
| Evidencia visual | `docs/evidencias/hu-001/*.png` | **4 archivos, PASS** |

## Cobertura de RF

| RF | Verificación | Resultado |
|---|---|---|
| RF-1 presentación clara | `<h1>`, `<p>` e `<title>` con literales de la spec | PASS |
| RF-2 imagen representativa | `<img>` con `src` resuelto y `alt` literal, 720×713, archivo existe | PASS |
| RF-3 accesos a secciones | 6 enlaces en `<nav>`; cada `href` responde 200 | PASS |
| RF-4 orientación institucional | sin `<form>`/`<input>`/admin; `POST /` → 405 | PASS |
| RF-5 resumen de servicios | bloque completo + enlace «Ver todos los servicios» → 200 | PASS |
| RF-6 frase de valores | literal presente en `GET /` | PASS |
| RF-7 marca secundaria | «Contenidas» visible y precede al `<h1>` | PASS |
| RNF-1 responsive | `viewport`, `width`/`height` en `<img>`, `@media (max-width…)` | PASS |
| RNF-2 paleta coherente | únicamente los 6 hex aprobados en `main.css` | PASS |
| CL-1 imagen no disponible | fallback a `placeholder.svg` conservando el `alt` | PASS |
| CL-2 contenido incompleto | `validate_content`/`validate_services` completan desde defaults | PASS |
| CL-3 sección no disponible | `/nosotros`, `/servicios`, `/articulos`, `/contacto`, `/citas` → 200 «en construcción» | PASS |

## Evidencia visual

| Archivo | Dimensiones | Contenido comprobado | Resultado |
|---|---|---|---|
| `escritorio-1280.png` | 1280×1900 | RF-1, RF-2, RF-3, RF-5, RF-6 (y=950-980) y pie (y=1055-1160); **sin botón «Menú»** (corrección de escritorio verificada) | PASS |
| `movil-375.png` | 375×2800 | RF-1, RF-2, RF-5, RF-6 (y=1495-1525), pie (y=1650-1695), botón «Menú» con nav oculta por defecto | PASS |
| `escritorio-1280-devtools.png` | recorte 759×598 | Viewport DevTools «Responsive 1280» (prueba del ancho de prueba) | PASS |
| `movil-375-devtools.png` | recorte 716×600 | Viewport DevTools «Responsive 375» (prueba del ancho de prueba) | PASS |

Las dos capturas completas se obtuvieron con Chrome headless a ancho exacto (1280 y 375)
y la presencia de cada bloque se verificó por muestreo de color, no por inspección
visual. El estado inicial del nav en móvil está comprobado además por código:
`base.html` no incluye la clase `is-open` y `main.css` aplica `display: none` bajo
`@media (max-width: 767px)`.

## Defectos encontrados

- Ninguno funcional. La única incidencia detectada en la revisión visual (botón «Menú»
  visible en escritorio) fue corregida en `static/css/main.css` y está verificada en
  `escritorio-1280.png`.

## Pendientes de cierre

- [ ] Commit de la evidencia y de este informe.
- [ ] Aceptación de la HU.

## Veredicto

**PASS** — los 29 tests y las 27 comprobaciones de contrato están en verde, y la
evidencia visual cubre la totalidad de los RF y los casos límite. Quedan como trámite
el commit de la evidencia y la aceptación de la HU.
