# Evidencia QA — HU-015 (Spec 015 · Consultar información de contacto)

**HU:** HU-015
**Rama (v1):** `feature/hu-015` — **Rama (ampliación 2026-10-12):** `feature/hu-015-diseno`
**Commits (v1):** `04640c7` (spec enmendada + plan + task), `942cf77` (contenido + espejo),
`7c14cfc` (servicio), `1f60bda` (web + plantilla + placeholders), `6eb32eb` (CSS),
`9670a9c` (tests), `1dd0498` (esta evidencia + MEMORY)
**Commits (ampliación):** `2bd6f53` (spec RF-7 + plan + task), `923f9b6` (`MAP_*` +
`ContactMap` + TC-017/018), `33bee8f` (cajón + iconos + mapa + TC-009/012/015/019)
**Fecha:** 2026-10-12

## Resumen

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **179 PASS / 0 FAIL** |
| Tests de la HU | `python -m pytest tests/test_contact_content.py tests/test_contact_service.py tests/test_contact_routes.py tests/test_hu_015.py -v` | **16 PASS / 0 FAIL** |
| Regresión HU-001/002/003/016/004/005/006/007/008 | mismos 163 tests previos dentro de la suite | **163 PASS** |
| Servidor de desarrollo | `GET http://127.0.0.1:5000/contacto` | **200** con h1 «Contacto», 5 bloques |
| Evidencia visual | `docs/evidencias/hu-015/*.png` | **2 archivos, PASS** |

16 pruebas nuevas (TC-015-001…016); ninguna relajada ni omitida.
`PLACEHOLDER_SECTIONS` pasó a `["/articulos"]` (D7) y la regresión sigue verde.

## Casos de prueba

| Caso | Archivo | Resultado |
|---|---|---|
| TC-015-001 módulo completo y espejo = spec (título, dirección, WhatsApp, correo, horarios, redes, etiquetas, `DEFAULT_*`) | `test_contact_content.py` | PASS |
| TC-015-002 formatos: `PHONE` vacío o dígitos, `WHATSAPP` dígitos, `EMAIL` válida, URLs `https://`, horarios completos | `test_contact_content.py` | PASS |
| TC-015-003 redes sin plataformas duplicadas ni etiquetas vacías | `test_contact_content.py` | PASS |
| TC-015-004 `get_contact_view()` → dirección + WhatsApp + correo, sin Teléfono, 2 horarios, Instagram, `fallback_active=False` | `test_contact_service.py` | PASS |
| TC-015-005 CL-1 dirección vacía → default + fallback; sin default → bloque omitido | `test_contact_service.py` | PASS |
| TC-015-006 CL-2 `PHONE=""` sin fallback (D16); WhatsApp/correo inválidos → default u omisión; canales con `href` | `test_contact_service.py` | PASS |
| TC-015-007 CL-3 horarios vacíos/inválidos → `DEFAULT_OFFICE_HOURS` | `test_contact_service.py` | PASS |
| TC-015-008 CL-4 red con `http://`, etiqueta vacía o duplicada → omitida; Instagram conservada | `test_contact_service.py` | PASS |
| TC-015-009 `GET /contacto` → 200 con `<h1>Contacto</h1>` y ≥4 bloques en `<main>` | `test_contact_routes.py` | PASS |
| TC-015-010 dirección + `wa.me/573168756020` + `mailto:` presentes; bloque «Teléfono» y `tel:` ausentes | `test_contact_routes.py` | PASS |
| TC-015-011 horarios (label/días/horas) y redes con `target="_blank" rel="noopener"` | `test_contact_routes.py` | PASS |
| TC-015-012 5 `<section>` propias con `<h2>`; sin mezcla de datos entre canales | `test_contact_routes.py` | PASS |
| TC-015-013 POST/PUT/DELETE → 405; `GET /contacto/horarios` → 404 con `errors/404.html` | `test_contact_routes.py` | PASS |
| TC-015-014 regresión: placeholders = `["/articulos"]`, `/articulos` «en construcción», nav de 6 hrefs → 200, buscador presente en `/contacto` | `test_contact_routes.py` | PASS |
| TC-015-015 RNF: viewport, `@media`, `.contact` 65ch, `justify` + `hyphens: none`, paleta ⊆ 6 hex | `test_hu_015.py` | PASS |
| TC-015-016 E2E portada → «Contacto» → 200 + «Volver al inicio»; `<main>` sin form/input ni chat | `test_hu_015.py` | PASS |

## Cobertura de RF

| RF | Verificación | Resultado |
|---|---|---|
| RF-1 datos de contacto disponibles | `GET /contacto` → 200 con h1 y bloques de datos en `<main>` (TC-009/016) | PASS |
| RF-2 dirección | bloque «Dirección» con las 3 líneas (TC-005/010) | PASS |
| RF-3 teléfono, WhatsApp y correo | WhatsApp (`wa.me/573168756020`) y correo (`mailto:`) visibles; **teléfono opcional no disponible** → sin bloque (D16; RF-3 condicional) (TC-006/010) | PASS |
| RF-4 horarios de atención | bloque «Horarios de atención» con Mañana/Tarde lun–vie (TC-007/011) | PASS |
| RF-5 redes sociales oficiales | Instagram con `https://…` `target="_blank" rel="noopener"` (TC-003/008/011) | PASS |
| RF-6 canales diferenciados | 5 `<section>` propias con su `<h2>`, sin mezcla (TC-012 + evidencia visual) | PASS |
| RNF-1 legible escritorio/móvil | mobile-first `.contact-*`, 65ch, `@media`, paleta intacta; sin desbordes (TC-015 + CDP) | PASS |
| RNF-2 clara y localizable | `<h2>` por canal, `<ul>` de horarios/redes, orden Dirección → Canales → Horarios → Redes (TC-012/015) | PASS |
| CL-1 dirección no aplicable | omisión del bloque; default aplicado si existe (TC-005) | PASS |
| CL-2 canal no disponible | canal omitido (Teléfono por diseño); ningún bloque vacío (TC-006) | PASS |
| CL-3 horarios no definidos | `DEFAULT_OFFICE_HOURS` (TC-007) | PASS |
| CL-4 red social no disponible | entrada inválida omitida; Instagram intacta (TC-008) | PASS |
| Fuera de alcance | sin formulario/chat; POST → 405; subrutas → 404 (TC-013/016) | PASS |
| Regresión HU anteriores | 163 tests previos verdes; placeholders y nav intactos (TC-014) | PASS |

## Evidencia visual

| Archivo | Dimensiones | Contenido comprobado | Resultado |
|---|---|---|---|
| `escritorio-1280.png` | 1280×1335 | nav de 6 accesos + buscador; h1 «Contacto»; 5 bloques salvia (Dirección, WhatsApp, Correo electrónico, Horarios de atención, Redes sociales); enlaces `wa.me`/`mailto:`/`Instagram`; «Volver al inicio»; pie; sin formularios | PASS |
| `movil-375.png` | 375×1552 | marca + botón «Menú»; bloques apilados **sin desbordamiento**; textos justificados y sin guiones; «Volver al inicio» y pie visibles; `scrollWidth` = `clientWidth` | PASS |

**Verificación CDP en vivo** (`Emulation.setDeviceMetricsOverride` + `Runtime.evaluate`,
puerto 9444, Chrome headless):

| Viewport | Resultado |
|---|---|
| 1280 | 5 `section.contact__block`; h1 «Contacto»; h2 = Dirección/WhatsApp/Correo electrónico/Horarios de atención/Redes sociales; `wa.me/573168756020` (sin `+`); `mailto:caritogomez26@gmail.com`; redes con `rel=noopener`; form/input en `<main>` = 0; `.contact__text` con `justify/none` (5/5); `scrollWidth`=1265=`clientWidth` (sin desborde) |
| 375 | `scrollWidth`=360=`clientWidth` (sin desborde), `scrollHeight`=1552; captura completa |

**Método**: DevTools Protocol (no `--window-size`, regla de AGENTS.md); alturas
medidas con `Runtime.evaluate` antes de capturar; emulación fijada por sesión.

## Demo manual

- `GET /contacto` → 200; se muestran dirección, WhatsApp, correo, horarios y
  Instagram; no se muestra bloque «Teléfono» (D16).
- Clic en WhatsApp → `https://wa.me/573168756020`; clic en correo → cliente de
  correo (`mailto:`); clic en Instagram → nueva pestaña (`rel="noopener"`).
- `POST /contacto` → 405; `GET /contacto/noexiste` → 404.
- Servidor de revisión en marcha: **http://127.0.0.1:5000/contacto**

## Veredicto (v1)

**PASS** — 16/16 TC en verde, suite 179/179, regresión intacta y evidencia visual verificada.

- [x] Tests automatizados PASS.
- [x] Regresión revisada (163 previos intactos).
- [x] Evidencia visual PASS (1280 y 375, sin desbordes).
- [x] Demo manual realizada.
- [x] **Aceptación de la HU por la usuaria**: 2026-10-12.

---

## Ampliación 2026-10-12 — cajón con iconos + mapa (RF-7)

**Rama:** `feature/hu-015-diseno` (spec 015 enmendada con RF-7 + literales `MAP_*` + caso
límite «Mapa no disponible»; plan/task de ampliación aprobados por la usuaria).

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **182 PASS / 0 FAIL** |
| Tests de la HU | `python -m pytest tests/test_contact_content.py tests/test_contact_service.py tests/test_contact_routes.py tests/test_hu_015.py -v` | **19 PASS / 0 FAIL** |
| Regresión resto de HUs | mismos 163 tests previos dentro de la suite | **163 PASS** |
| Servidor de desarrollo | `GET http://127.0.0.1:5000/contacto` | **200** con cajón de 5 filas + mapa |
| Evidencia visual | `docs/evidencias/hu-015/*.png` (regeneradas) | **2 archivos, PASS** |

### Casos de prueba de la ampliación

| Caso | Archivo | Resultado |
|---|---|---|
| TC-015-017 literales `MAP_*` = espejo; embed `output=embed` y link con la consulta URL-encoded; «Abrir en Google Maps» y título | `test_contact_content.py` | PASS |
| TC-015-018 RF-7 servicio: `map` completo sin fallback; CL-5 `MAP_QUERY` vacío → default y `fallback_active=True`; ambos vacíos → `map is None`; CL-1 sin dirección → `map is None` | `test_contact_service.py` | PASS |
| TC-015-019 iframe `www.google.com/maps` con `title` + `loading="lazy"` y enlace de respaldo `target="_blank" rel="noopener"`; dirección visible fuera del iframe | `test_contact_routes.py` | PASS |
| TC-015-009 (adaptado) h1 + `.contact__panel` con ≥5 `<li class="contact__row">` | `test_contact_routes.py` | PASS |
| TC-015-012 (adaptado) 5 filas con `<svg aria-hidden="true">`, etiqueta y valor; sin mezcla de datos entre canales | `test_contact_routes.py` | PASS |
| TC-015-015 (adaptado) RNF: viewport, `@media`, `.contact` 65ch, `.contact__value` justify/none, grid 2 columnas `@media (min-width: 900px)`, paleta ⊆ 6 hex | `test_hu_015.py` | PASS |

TC-015-001…008/010/011/013/014/016 de v1: **sin cambios y en verde** (marcado de
enlaces idéntico a v1, D5). Ninguna aserción relajada.

### Cobertura RF-7 y casos límite

| Elemento | Verificación | Resultado |
|---|---|---|
| RF-7 mapa con dirección | iframe embed de Google Maps + enlace de respaldo en `/contacto` (TC-018/019 + CDP) | PASS |
| CL-1 dirección no aplicable | `map is None` con dirección y default vacíos (TC-018) | PASS |
| CL-5 consulta de mapa vacía | default aplicado (`fallback_active=True`); ambos vacíos → bloque omitido (TC-018) | PASS |
| «Mapa no disponible» (spec) | dirección escrita permanece visible fuera del iframe (TC-019 + CDP) | PASS |
| RNF-1 legible escritorio/móvil | grid 2 columnas ≥900 px, apilado <900 px, sin desbordes (TC-015 + CDP) | PASS |

### Evidencia visual (capturas regeneradas)

| Archivo | Dimensiones | Contenido comprobado | Resultado |
|---|---|---|---|
| `escritorio-1280.png` | 1280×1156 | h1 «Contacto»; cajón salvia con 5 filas (icono SVG + etiqueta + valor): Dirección, WhatsApp, Correo electrónico, Horarios de atención, Redes sociales; mapa de Google a la derecha (grid 2 columnas); enlace «Abrir en Google Maps»; «Volver al inicio»; sin formularios | PASS |
| `movil-375.png` | 375×1574 | filas apiladas (valor en línea propia cuando no cabe), mapa debajo, **sin desbordes** (`scrollWidth` = `clientWidth` = 375) | PASS |

**Verificación CDP en vivo** (`Emulation.setDeviceMetricsOverride` +
`Runtime.evaluate`, puerto 9444, Chrome headless):

| Viewport | Resultado |
|---|---|
| 1280 | `contactDisplay=grid`; 5 filas con 5 iconos `aria-hidden`; labels Dirección/WhatsApp/Correo electrónico/Horarios de atención/Redes sociales; iframe `google.com/maps…output=embed` con title y `loading=lazy`; enlace «Abrir en Google Maps» `rel=noopener`; `wa.me/573168756020`; `mailto:caritogomez26@gmail.com`; Instagram `rel=noopener`; `justify/none` en `.contact__value`; form/input en `<main>` = 0; `scrollWidth` = `clientWidth` = 1265 (sin desborde) |
| 375 | `contactDisplay=block` (sin grid); mismo contenido; `scrollWidth` = `clientWidth` = 375 (sin desborde), `scrollHeight` = 1574; captura completa |

**Corrección durante la ampliación:** la primera pasada a 375 px desbordaba
(`scrollWidth` 512) porque `.contact__label` (10,5 rem) empujaba el valor con tokens
largos (`caritogomez26@gmail.com`); se añadió `flex-wrap: wrap` a `.contact__row` y
`flex: 1 1 12rem; min-width: 0` a `.contact__value`, y la verificación CDP quedó en
`scrollWidth` = 375.

**Método**: DevTools Protocol (no `--window-size`, regla de AGENTS.md); alturas
medidas con `Runtime.evaluate` antes de capturar; emulación fijada por sesión.

### Demo manual (ampliación)

- `GET /contacto` → 200; cajón con iconos + mapa de Google y «Abrir en Google Maps».
- Clic en WhatsApp/correo/Instagram → mismos comportamientos de v1.
- Mapa visible a 1280 px (columna derecha) y debajo del cajón a 375 px.
- Servidor de revisión en marcha: **http://127.0.0.1:5000/contacto**

### Veredicto de la ampliación

**PASS** — 19/19 TC de HU-015 en verde, suite **182/182**, regresión intacta y
evidencia visual regenerada sin desbordes.

- [x] Tests automatizados PASS (182/182).
- [x] Regresión revisada (163 previos intactos).
- [x] Evidencia visual PASS (1280 y 375, sin desbordes; capturas regeneradas).
- [x] Demo manual realizada.
- [x] **Aceptación de la ampliación por la usuaria**: 2026-10-12.
