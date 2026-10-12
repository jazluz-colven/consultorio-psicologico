# Evidencia QA — HU-015 (Spec 015 · Consultar información de contacto)

**HU:** HU-015
**Rama:** `feature/hu-015`
**Commits:** `04640c7` (spec enmendada + plan + task), `942cf77` (contenido + espejo),
`7c14cfc` (servicio), `1f60bda` (web + plantilla + placeholders), `6eb32eb` (CSS),
`9670a9c` (tests), `<evidencia>` (esta carpeta + MEMORY)
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

## Veredicto

**PASS** — 16/16 TC en verde, suite 179/179, regresión intacta y evidencia visual verificada.

- [x] Tests automatizados PASS.
- [x] Regresión revisada (163 previos intactos).
- [x] Evidencia visual PASS (1280 y 375, sin desbordes).
- [x] Demo manual realizada.
- [ ] **Aceptación de la HU por la usuaria**: _______________ (fecha: ______)
