# Evidencia QA — HU-003 (Spec 003 · Consultar los servicios)

**HU:** HU-003
**Rama:** `feature/hu-003`
**Commits:** `e6ad118` (plan + tasks), `6440e74` (spec: literales RF-3 + cierre Q1),
`72167bd` (espejo), `84169a4` (catálogo), `18f5a85` (tests contenido),
`c16a098` (servicio), `5b5dbdb` (tests servicio), `66d980a` (web + plantilla),
`5be6b48` (CSS), `249dae6` (tests ruta), `6d4a5f4` (tests HU), `6f2a9c4` (regresión),
`6992364` (evidencia + memory), `4ba8ce0` (imágenes: spec/plan Q6/D14 + WebP)
**Fecha:** 2026-10-08 (actualizada tras la ampliación de imágenes, Q6/D14)

## Resumen

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **63 PASS / 0 FAIL** |
| Tests de la HU | `python -m pytest tests/test_services_content.py tests/test_services_service.py tests/test_services_routes.py tests/test_hu_003.py -v` | **18 PASS / 0 FAIL** |
| Regresión HU-001/002 | mismos 45 tests previos dentro de la suite | **45 PASS** |
| Servidor de desarrollo | `GET http://127.0.0.1:5000/servicios` | **200** con h1 «Servicios», los 2 servicios y sus banners |
| Imágenes servidas | `GET /static/img/servicios/*.webp` | **200** `image/webp` (55 KB y 52 KB) |
| Evidencia visual | `docs/evidencias/hu-003/*.png` | **2 archivos, PASS** |

18 pruebas nuevas agrupadas en los 16 TC del plan (§6.1); ninguna relajada ni
omitida. Ejecución única: `63 passed`.

## Casos de prueba

| Caso | Archivo | Resultado |
|---|---|---|
| TC-003-001 claves aprobadas, sin campos vacíos (incl. `image`/`image_alt`) ni beneficios duplicados | `test_services_content.py` | PASS |
| TC-003-002 `DEFAULT_*` = literales de la spec (desc, beneficios, imagen, alt); título «Servicios» | `test_services_content.py` | PASS |
| TC-003-003 los 2 servicios mínimos, coherentes con `SERVICES_HIGHLIGHT` | `test_services_content.py` | PASS |
| TC-003-004 description y benefits no vacíos por servicio | `test_services_content.py` | PASS |
| TC-003-016 cada `image` existe como fichero estático y su `image_alt` no está vacío | `test_services_content.py` | PASS |
| TC-003-005 `get_services_view()` → 2 servicios completos (incl. imagen y alt), `fallback_active=False` | `test_services_service.py` | PASS |
| TC-003-006 CL-1 catálogo vacío (monkeypatch) → defaults + `fallback_active=True` | `test_services_service.py` | PASS |
| TC-003-007 CL-2 campos vacíos → defaults por campo (imagen y alt incluidos) | `test_services_service.py` | PASS |
| TC-003-008 `GET /servicios` → 200 con h1 y los 2 nombres en `<main>` | `test_services_routes.py` | PASS |
| TC-003-009 2 `<section>` propios, cada uno con `<img>` (src + alt), descripción y `<ul>` de beneficios | `test_services_routes.py` | PASS |
| TC-003-010 POST/PUT/DELETE → 405 | `test_services_routes.py` | PASS |
| TC-003-011 CL-3 `GET /servicios/<recurso>` → 404 con `errors/404.html` | `test_services_routes.py` | PASS |
| TC-003-012 regresión: placeholders sin `/servicios`, resto 200, nav de 6 hrefs | `test_services_routes.py` | PASS |
| extra imágenes 200 `image/webp` | `test_services_routes.py` | PASS |
| TC-003-013 RNF-1: viewport, `@media`, paleta ⊆ 6 hex, medida 65ch, justify + hyphens, banner (`aspect-ratio: 2/1` + `object-fit: cover` + `border-radius`) | `test_hu_003.py` | PASS |
| TC-003-014 E2E portada → «Ver todos los servicios» → `/servicios` → «Volver al inicio» | `test_hu_003.py` | PASS |
| TC-003-015 fuera de alcance: `<main>` sin form/input ni enlace a `/citas` | `test_hu_003.py` | PASS |

## Cobertura de RF

| RF | Verificación | Resultado |
|---|---|---|
| RF-1 mostrar servicios | `GET /servicios` → 200, h1 «Servicios», 2 bloques con nombre y banner en `<main>` (TC-008/014/016) | PASS |
| RF-2 mínimo Psicología Integral y Psiconutrición | catálogo + HTML con los 2 nombres; coherencia con la portada (TC-003/008) | PASS |
| RF-3 descripción clara y beneficios | `<p>` de descripción no vacío + `<ul>` con ≥1 `<li>` por servicio; fallback por campo (TC-004/007/009) | PASS |
| RF-4 información diferenciada | 1 `<section>` propia por servicio con su `<h2>` e imagen propia; sin campos mezclados (TC-009) | PASS |
| Imágenes (Q6/D14) | `<img>` con src = fichero existente (200 `image/webp`) y alt no vacío; PNG original convertido a WebP (1 MB → 55 KB) (TC-016 + extra) | PASS |
| RNF-1 claridad escritorio y móvil | `viewport`, `@media (max-width…)`, `.services-page__block { max-width: 65ch }`, párrafos `justify` + `hyphens: none`, banner `aspect-ratio: 2/1` + `object-fit: cover`, paleta intacta (TC-013 + CDP) | PASS |
| CL-1 sin servicios publicados | catálogo vacío → 2 defaults completos con `fallback_active=True` (TC-006) | PASS |
| CL-2 servicio sin descripción/benefits/imagen | defaults por campo; ningún bloque incompleto emitido (TC-007) | PASS |
| CL-3 servicio no disponible | `GET /servicios/<recurso>` → 404 con `errors/404.html` (TC-011) | PASS |
| Fuera de alcance | sin CTA de reserva en `<main>`; POST → 405 (TC-010/015) | PASS |
| Regresión HU-001/002 | `/articulos`, `/contacto`, `/citas` siguen «en construcción»; `/`, `/nosotros` intactos; nav de 6 → 200; 45 tests previos verdes (TC-012) | PASS |

## Evidencia visual

| Archivo | Dimensiones | Contenido comprobado | Resultado |
|---|---|---|---|
| `escritorio-1280.png` | 1280×1965 | nav de 6 accesos; h1 «Servicios»; 2 bloques salvia con **banner de foto con esquinas redondeadas**, «Psicología Integral» y «Psiconutrición», descripciones completas justificadas y listas de 4 beneficios; «Volver al inicio»; pie con marca; sin formularios ni CTA a `/citas` | PASS |
| `movil-375.png` | 375×2286 | marca + botón «Menú»; los 2 bloques apilados con sus banners a todo el ancho y **sin desbordamiento**; literales completos justificados y sin guiones; «Volver al inicio» y pie visibles; `scrollWidth` = 375 | PASS |

**Verificación CDP en vivo** (`Emulation.setDeviceMetricsOverride` + `Runtime.evaluate`):

| Viewport | Resultado |
|---|---|
| 1280 | `lang=es`; 2 `.services-page__block`; h1 «Servicios»; 2 `.services-page__image` cargadas (`complete: true`, naturales 1200×600 y 1200×800), 531×265.5 px con `aspect-ratio: 2 / 1` y `object-fit: cover`; los 2 `.services-page__text` con `text-align: justify` + `hyphens: none`; 8 beneficios; `scrollWidth`=1280; `form`/`input` en `<main>` = 0; enlaces a `/citas` en `<main>` = 0 |
| 375 | `scrollWidth`=375 (sin desborde), `scrollHeight`=2286; 2 secciones con imágenes 285×142.5 cargadas; los 2 textos con justify + none; botón «Menú» visible (`display: block`); «Volver al inicio» presente |

**Método**: Chrome 154 headless vía DevTools Protocol en el puerto 9444
(`capture_cdp.ps1`, recarga con `ignoreCache` para evitar CSS de caché — incidente
conocido de `/nosotros`). Alturas medidas con `Runtime.evaluate`
(`scrollHeight` 1965 px a 1280 y 2286 px a 375) y capturas generadas con esas
alturas exactas; dimensiones de los PNG verificadas por cabecera IHDR.

## Defectos encontrados

- Ninguno. La suite nunca estuvo en rojo durante el desarrollo de la HU ni de la
  ampliación de imágenes (45 → 63 PASS sin regresiones).

## Pendientes de cierre

- [x] Spec 003 con literales RF-3 y duda Q1 cerrada (`6440e74`).
- [x] Spec/plan actualizados con imágenes (Q6/D14; `4ba8ce0`) antes de implementar.
- [x] `plan.md` aprobado (2026-10-07) y task.md seguido por orden.
- [x] Implementación y tests en verde (18 tests nuevos; 63 PASS).
- [x] Evidencia QA + capturas escritorio/móvil regeneradas con banners.
- [x] Commit/Push de la evidencia y actualización de `MEMORY.md` (`d659139`).
- [x] Aceptación de la HU (checkbox de abajo).

## Veredicto

**PASS** — 63 tests en verde (los 45 de HU-001/002 intactos como regresión),
cobertura completa de RF-1..RF-4, imágenes por servicio (Q6/D14), RNF-1,
CL-1..CL-3 y fuera de alcance, y evidencia visual escritorio/móvil regenerada y
verificada por DOM + medidas de PNG. HU aceptada por la usuaria el 2026-10-08:
**HU-003 CERRADA**.

---

## Aceptación de la HU

- [x] Aceptada por la usuaria el 08/10/2026
