# Evidencia QA — HU-003 (Spec 003 · Consultar los servicios)

**HU:** HU-003
**Rama:** `feature/hu-003`
**Commits:** `e6ad118` (plan + tasks), `6440e74` (spec: literales RF-3 + cierre Q1),
`72167bd` (espejo), `84169a4` (catálogo), `18f5a85` (tests contenido),
`c16a098` (servicio), `5b5dbdb` (tests servicio), `66d980a` (web + plantilla),
`5be6b48` (CSS), `249dae6` (tests ruta), `6d4a5f4` (tests HU), `6f2a9c4` (regresión)
**Fecha:** 2026-10-08

## Resumen

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **61 PASS / 0 FAIL** |
| Tests de la HU | `python -m pytest tests/test_services_content.py tests/test_services_service.py tests/test_services_routes.py tests/test_hu_003.py -v` | **16 PASS / 0 FAIL** |
| Regresión HU-001/002 | mismos 45 tests previos dentro de la suite | **45 PASS** |
| Servidor de desarrollo | `GET http://127.0.0.1:5000/servicios` | **200** con h1 «Servicios» y los 2 servicios |
| Evidencia visual | `docs/evidencias/hu-003/*.png` | **2 archivos, PASS** |

16 pruebas nuevas agrupadas en los 15 TC del plan (§6.1); ninguna relajada ni
omitida. Ejecución única: `61 passed in 2.10s`.

## Casos de prueba

| Caso | Archivo | Resultado |
|---|---|---|
| TC-003-001 claves aprobadas, sin campos vacíos ni beneficios duplicados | `test_services_content.py` | PASS |
| TC-003-002 `DEFAULT_*` = literales de la spec; título «Servicios» | `test_services_content.py` | PASS |
| TC-003-003 los 2 servicios mínimos, coherentes con `SERVICES_HIGHLIGHT` | `test_services_content.py` | PASS |
| TC-003-004 description y benefits no vacíos por servicio | `test_services_content.py` | PASS |
| TC-003-005 `get_services_view()` → 2 servicios completos, `fallback_active=False` | `test_services_service.py` | PASS |
| TC-003-006 CL-1 catálogo vacío (monkeypatch) → defaults + `fallback_active=True` | `test_services_service.py` | PASS |
| TC-003-007 CL-2 description/benefits vacíos → defaults por campo | `test_services_service.py` | PASS |
| TC-003-008 `GET /servicios` → 200 con h1 y los 2 nombres en `<main>` | `test_services_routes.py` | PASS |
| TC-003-009 2 `<section>` propias, cada una con descripción y `<ul>` de beneficios | `test_services_routes.py` | PASS |
| TC-003-010 POST/PUT/DELETE → 405 | `test_services_routes.py` | PASS |
| TC-003-011 CL-3 `GET /servicios/<recurso>` → 404 con `errors/404.html` | `test_services_routes.py` | PASS |
| TC-003-012 regresión: placeholders sin `/servicios`, resto 200, nav de 6 hrefs | `test_services_routes.py` | PASS |
| TC-003-013 RNF-1: viewport, `@media`, paleta ⊆ 6 hex, medida 65ch, justify + hyphens | `test_hu_003.py` | PASS |
| TC-003-014 E2E portada → «Ver todos los servicios» → `/servicios` → «Volver al inicio» | `test_hu_003.py` | PASS |
| TC-003-015 fuera de alcance: `<main>` sin form/input ni enlace a `/citas` | `test_hu_003.py` | PASS |

## Cobertura de RF

| RF | Verificación | Resultado |
|---|---|---|
| RF-1 mostrar servicios | `GET /servicios` → 200, h1 «Servicios», 2 bloques con nombre en `<main>` (TC-008/014) | PASS |
| RF-2 mínimo Psicología Integral y Psiconutrición | catálogo + HTML con los 2 nombres; coherencia con la portada (TC-003/008) | PASS |
| RF-3 descripción clara y beneficios | `<p>` de descripción no vacío + `<ul>` con ≥1 `<li>` por servicio; fallback por campo (TC-004/007/009) | PASS |
| RF-4 información diferenciada | 1 `<section>` propia por servicio con su `<h2>`; sin campos mezclados (TC-009) | PASS |
| RNF-1 claridad escritorio y móvil | `viewport`, `@media (max-width…)`, `.services-page__block { max-width: 65ch }`, párrafos `justify` + `hyphens: none`, paleta intacta (TC-013 + CDP) | PASS |
| CL-1 sin servicios publicados | catálogo vacío → 2 defaults completos con `fallback_active=True` (TC-006) | PASS |
| CL-2 servicio sin descripción/benefits | defaults por campo; ningún bloque incompleto emitido (TC-007) | PASS |
| CL-3 servicio no disponible | `GET /servicios/<recurso>` → 404 con `errors/404.html` (TC-011) | PASS |
| Fuera de alcance | sin CTA de reserva en `<main>`; POST → 405 (TC-010/015) | PASS |
| Regresión HU-001/002 | `/articulos`, `/contacto`, `/citas` siguen «en construcción»; `/`, `/nosotros` intactos; nav de 6 → 200; 45 tests previos verdes (TC-012) | PASS |

## Evidencia visual

| Archivo | Dimensiones | Contenido comprobado | Resultado |
|---|---|---|---|
| `escritorio-1280.png` | 1280×1398 | nav de 6 accesos; h1 «Servicios»; 2 bloques salvia con «Psicología Integral» y «Psiconutrición», descripciones completas justificadas y listas de 4 beneficios; «Volver al inicio»; pie con marca; sin formularios ni CTA a `/citas` | PASS |
| `movil-375.png` | 375×1965 | marca + botón «Menú»; los 2 bloques apilados con literales completos justificados y sin guiones; «Volver al inicio» y pie visibles; `scrollWidth` = 375 (sin desbordamiento horizontal) | PASS |

**Verificación CDP en vivo** (`Emulation.setDeviceMetricsOverride` + `Runtime.evaluate`):

| Viewport | Resultado |
|---|---|
| 1280 | `lang=es`; 2 `.services-page__block`; h1 «Servicios»; los 2 `.services-page__text` con `text-align: justify` + `hyphens: none`; 8 beneficios; `scrollWidth`=1280; `form`/`input` en `<main>` = 0; enlaces a `/citas` en `<main>` = 0 |
| 375 | `scrollWidth`=375 (sin desborde), `scrollHeight`=1965; 2 secciones; los 2 textos con justify + none; botón «Menú» visible (`display: block`); «Volver al inicio» presente |

**Método**: Chrome 154 headless vía DevTools Protocol en el puerto 9444
(`capture_cdp.ps1`, perfil limpio). Alturas medidas con `Runtime.evaluate`
(`scrollHeight` 1398 px a 1280 y 1965 px a 375) y capturas generadas con esas
alturas exactas; dimensiones de los PNG verificadas por cabecera IHDR.

## Defectos encontrados

- Ninguno. La suite nunca estuvo en rojo durante el desarrollo de la HU
  (45 → 61 PASS sin regresiones; los 45 previos intactos).

## Pendientes de cierre

- [x] Spec 003 con literales RF-3 y duda Q1 cerrada (`6440e74`).
- [x] `plan.md` aprobado (2026-10-07) y task.md seguido por orden.
- [x] Implementación y tests en verde (16 tests nuevos; 61 PASS).
- [x] Evidencia QA + capturas escritorio/móvil.
- [ ] Commit/Push de la evidencia y actualización de `MEMORY.md`.
- [ ] Aceptación de la HU (checkbox de abajo).

## Veredicto

**PASS** — 61 tests en verde (los 45 de HU-001/002 intactos como regresión),
cobertura completa de RF-1..RF-4, RNF-1, CL-1..CL-3 y fuera de alcance, y
evidencia visual escritorio/móvil verificada por DOM + medidas de PNG.

---

## Aceptación de la HU

- [ ] Aceptada por la usuaria el ____/____/________
