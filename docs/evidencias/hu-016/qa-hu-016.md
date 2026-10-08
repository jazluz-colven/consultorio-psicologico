# Evidencia QA — HU-016 (Spec 016 · Buscar contenido del sitio)

**HU:** HU-016 (incluye la enmienda de identidad de la Spec 001)
**Rama:** `feature/identidad-buscador`
**Commits:** `d0e2d4c` (docs: spec 016 + enmiendas 001-003 + decisiones de diseño),
`ed36013` (feat: identidad + buscador), `f53282d` (tests), y el commit de este
documento con `MEMORY.md`
**Fecha:** 2026-10-08

## Resumen

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **74 PASS / 0 FAIL** |
| Tests de la HU | `python -m pytest tests/test_search_service.py tests/test_search_routes.py tests/test_hu_016.py -v` | **11 PASS / 0 FAIL** |
| Regresión HU-001/002/003 | `python -m pytest tests/test_home_*.py tests/test_hu_001.py tests/test_hu_002.py tests/test_hu_003.py -q` | **37 PASS** (63 previos verdes dentro de la suite) |
| Demo manual: con resultados | `GET /buscar?q=psicología` | **200**, «2 resultados para «psicología».» con enlaces |
| Demo manual: sin resultados | `GET /buscar?q=zzzzz` | **200**, «No se encontraron resultados para «zzzzz».» |
| Demo manual: consulta vacía | `GET /buscar?q=` | **200**, «Escribe un término para buscar en el sitio.» |
| Evidencia visual | documentada abajo, **sin PNG en el repo** (Q6) | PASS |

11 pruebas nuevas cubren los 11 TC del plan (§6.1); ninguna relajada ni omitida.
Ejecución única: `74 passed`.

## Casos de prueba

| Caso | Archivo | Resultado |
|---|---|---|
| TC-016-001 `search("psicología")` → ≥1 resultado con título, extracto y URL | `test_search_service.py` | PASS |
| TC-016-002 índice cubre portada, Nosotros, Servicios y navegación | `test_search_service.py` | PASS |
| TC-016-003 `search("zzzzz")` → lista vacía | `test_search_service.py` | PASS |
| TC-016-004 `search("")` / `search("   ")` → estado «vacío», sin resultados | `test_search_service.py` | PASS |
| TC-016-011 consulta larga o con caracteres especiales → sin excepción | `test_search_service.py` | PASS |
| TC-016-005 `GET /buscar?q=…` → 200 con «Resultados de búsqueda» y enlaces | `test_search_routes.py` | PASS |
| TC-016-006 `psiconutricion` / `PSICONUTRICION` / `Psiconutrición` → encuentra «Psiconutrición» | `test_search_routes.py` | PASS |
| TC-016-007 consulta vacía y `zzzzz` → 200 con sus literales | `test_search_routes.py` | PASS |
| TC-016-008 formulario `action="/buscar"` en `/`, `/nosotros`, `/servicios`, `/articulos`, `/contacto`, `/citas` y `/buscar`, **fuera del `<nav>`**; POST → 405 | `test_search_routes.py` | PASS |
| TC-016-009 `main.css`: `.site-search*` + `.search-*`, `@media` móvil/escritorio, colores ⊆ paleta | `test_hu_016.py` | PASS |
| TC-016-010 regresión `/`, `/nosotros`, `/servicios`, 404 y navegación con el formulario presente | `test_hu_016.py` | PASS |

### Tests de la enmienda de identidad (Spec 001)

| Caso | Archivo | Resultado |
|---|---|---|
| TC-001-001/003 contenido con `brand_name` = «Carolina Gómez» (espejo) | `test_home_content.py` | PASS |
| TC-001-004 imagen representativa **acotada al `<figure>` del hero** → `hero-presentacion.png` + alt nuevo | `test_home_routes.py` | PASS |
| TC-001-008 sin formularios de reserva/administración (**admite `site-search`**) | `test_home_routes.py` | PASS |
| Identidad del view y del hero (src/alt) | `test_home_service.py` | PASS |

## Cobertura de RF

| RF | Verificación | Resultado |
|---|---|---|
| RF-1 página de resultados con título, extracto y enlace | TC-016-001/002/005: `.search-result` con `<h2><a>`, extracto y URL de sección | PASS |
| RF-2 mensaje cuando no hay coincidencias | TC-016-003/007: literal «No se encontraron resultados para «{término}».» | PASS |
| RF-3 consulta vacía con 200 | TC-016-004/007: literal «Escribe un término para buscar en el sitio.», HTTP 200 | PASS |
| RF-4 formulario en la cabecera de `base.html`, bajo el menú | TC-016-008 en las 7 páginas con `base.html`, fuera del `<nav>` | PASS |
| RF-5 insensible a mayúsculas y acentos | TC-016-006 (`unicodedata`), TC-016-001/005 | PASS |
| RNF-1 legible en escritorio y móvil, paleta y tipografía vigentes | TC-016-009 + verificación visual CDP (1280/1100/900/375) | PASS |
| RNF-2 sin dependencias nuevas | `unicodedata` (estándar); Google Fonts vía `@import` aprobado en `docs/design-typography.md` | PASS |
| Casos límite | consulta vacía, sin coincidencias, 1000 caracteres y símbolos → 200 sin excepción (TC-016-004/007/011) | PASS |
| Regresión HU-001/002/003 | 63 tests previos verdes; nav de 6 enlaces intacto; placeholders responden (TC-016-010) | PASS |

## Demo manual (criterio de finalización de la spec)

| Consulta | Ruta | Resultado |
|---|---|---|
| `psicología` | `/buscar?q=psicología` | 200, «2 resultados para «psicología».» → Psicología Integral (/servicios) y Experiencia profesional (/nosotros) |
| `zzzzz` | `/buscar?q=zzzzz` | 200, «No se encontraron resultados para «zzzzz».» |
| (vacía) | `/buscar?q=` | 200, «Escribe un término para buscar en el sitio.» |
| `psiconutricion` (sin acento) | `/buscar?q=psiconutricion` | 200, encuentra «Psiconutrición» |

## Evidencia visual (documentada, sin regenerar PNG — Q6)

Decisión de la usuaria (2026-10-08): **no se regeneran los PNG** de HU-001/002/003;
el cambio visual se documenta aquí. Verificación con Chrome 154 headless vía
DevTools Protocol (`Emulation.setDeviceMetricsOverride`, puerto 9444):

| Viewport | Página | Observación |
|---|---|---|
| 1280 | `/` | cabecera en **una fila**: logotipo «Contenidas» + «Carolina Gómez» (sin partir), menú de 6 accesos, campo + botón a la derecha; hero con foto `hero-presentacion.png` en marco elíptico (50 %, decisión del usuario) y «CONTENIDAS» sobre el h1; Open Sans aplicada |
| 1100 y 900 | `/` | regla D10: el formulario pasa a **su propia fila, alineado a la derecha**; el menú no se parte de forma desordenada; `scrollWidth` = ancho del viewport (sin desbordamiento) |
| 375 | `/` y `/buscar` | marca + botón «Menú»; formulario **debajo del menú** (etiqueta oculta, placeholder visible); tarjetas de resultado apiladas sin desbordamiento |
| 1280 | `/buscar?q=psicología` | h1 «Resultados de búsqueda», línea «2 resultados para «psicología».», tarjetas salvia con título enlazado, extracto justificado y «Volver al inicio» |

## Defectos encontrados (corregidos en la misma rama)

1. **Cabecera a 1280**: la etiqueta visible del campo empujaba el menú y partía
   «Agendar cita» a una segunda fila, y el nombre se partía en dos líneas →
   etiqueta *visually-hidden* (D9) + `flex: 0 0 auto`/`white-space: nowrap` en la
   marca (D9) y regla responsive 768-1199 (D10).
2. **TC-001-004** tomaba el primer `<img>` del documento (ahora el logotipo de
   cabecera) → test acotado al `<figure>` del hero.
3. **TC-001-008** prohibía cualquier `<form>` → acotado a formularios de
   reserva/administración con aserción positiva del buscador (D8).

## Pendientes de cierre

- [x] Docs de diseño primero (`docs/design-identity.md`, `docs/design-typography.md`).
- [x] Spec 016 + plan; enmiendas de specs/planes 001-003 antes de tocar código.
- [x] Implementación (identidad, tipografía, buscador) y `create_app()` registrado.
- [x] Tests: espejo + enmiendas + 11 nuevos; suite en verde (74 PASS).
- [x] Regresión HU-001/002/003 revisada (63 previos intactos).
- [x] Demo manual de las 3 consultas + verificación visual 1280/1100/900/375.
- [x] Evidencia QA documentada (este documento, sin PNG por Q6).
- [x] Commits por fase y `MEMORY.md` actualizado.
- [x] Push verificado contra `origin` (rama sincronizada en `2c1c146`).
- [x] Aceptación de la HU (checkbox de abajo).

## Veredicto

**PASS** — 74 tests en verde (los 63 previos intactos como regresión), cobertura
completa de RF-1..RF-5, RNF-1/RNF-2 y casos límite de la Spec 016, enmienda de
identidad de la Spec 001 verificada (nombre, hero, cabecera, Open Sans) y demo
manual de las 3 consultas con evidencia visual documentada.
HU aceptada por la usuaria el 2026-10-08: **HU-016 CERRADA**.

---

## Aceptación de la HU

- [x] Aceptada por la usuaria el 08/10/2026
