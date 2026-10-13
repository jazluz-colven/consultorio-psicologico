# QA — Pulido frontend: contraste AA, back-links y foco visible

**Fecha:** 2026-10-12
**Rama:** `feature/contraste-aa`
**Alcance:** A3 (back-links), A1 (tonos oscuros AA), A2 (foco visible)
**Decisión de diseño:** `docs/design-contrast.md`
**Veredicto:** **PASS** (187/187 tests, sin desbordes, pares verificados)
**Aceptación de la usuaria:** 2026-10-12 — «Me gusta. Acepto.»

## Requisito y trazabilidad

| Item | Origen | Estado |
|---|---|---|
| Contraste AA texto ≥4.5:1, bordes/foco ≥3:1 | `AGENTS.md` («contraste y accesibilidad») + `docs/design-contrast.md` | [x] PASS |
| Back-link `/buscar` y placeholder consistentes | Revisión frontend (hallazgo A3, patrón de HU-001/002/003/015) | [x] PASS |
| Foco visible calendario/inputs/enlaces (WCAG 1.4.11) | Revisión frontend (hallazgo A2) | [x] PASS |

## Criterios de aceptación

- [x] **CA-1** `docs/design-contrast.md` creado con pares, ratios y alternativas descartadas.
- [x] **CA-2** `AGENTS.md` tabla de paleta con los 2 tonos funcionales y sus reglas.
- [x] **CA-3** `:root` con `--color-primary-dark: #3D5A4E` y `--color-accent-dark: #7F4527`.
- [x] **CA-4** Enlaces, botones, hero, errores, badge «Ocupado», estados del calendario usan los tonos AA.
- [x] **CA-5** `.search-page__back` (margen 36px + negrita) y `.placeholder__back` (margen 36px) = patrón del resto de páginas.
- [x] **CA-6** Sin `outline: none` en toda la hoja; foco visible en calendario (teclado real verificado), inputs y enlaces.
- [x] **CA-7** `expected_content.PALETTE` ampliado (8 hex) — los 8 tests de paleta la importan y pasan.
- [x] **CA-8** Nuevo `tests/test_contraste.py` con pares documentados (red de regresión).
- [x] **CA-9** Sin desbordes a 1280 y 375 (`scrollWidth` ≤ viewport en las 12 páginas medidas).

## Verificación de ratios (calculados por `tests/test_contraste.py`)

| Par | Ratio | Umbral | Resultado |
|---|---|---|---|
| `#3D5A4E` sobre marfil | 6.84 | 4.5 | PASS |
| `#3D5A4E` sobre verde agua | 4.96 | 4.5 | PASS |
| Marfil sobre `#3D5A4E` (botones) | 6.84 | 4.5 | PASS |
| `#7F4527` sobre marfil (hover/enlaces) | 6.81 | 4.5 | PASS |
| `#7F4527` sobre verde agua (errores) | 4.94 | 4.5 | PASS |
| Marfil sobre `#7F4527` (badge) | 6.81 | 4.5 | PASS |
| `#30454B` sobre marfil/verde/arena | 9.12 / 6.62 / 7.03 | 4.5 | PASS |
| Foco calendario `#30454B` sobre verde agua | 6.62 | 3 | PASS |
| Borde input `#3D5A4E` sobre marfil | 6.84 | 3 | PASS |

## Suite automatizada

| Prueba | Comando | Resultado |
|---|---|---|
| Suite completa (182 previos + 5 nuevos) | `python -m pytest -q` | **187 PASS / 0 FAIL** |
| `tests/test_contraste.py` (5 TC nuevos) | `python -m pytest tests/test_contraste.py -q` | **5 PASS** |

Regresiones revisadas: paleta (8 tests), regex de CSS de HU-003/004/005/006/015/016,
`justify + hyphens`, `:disabled`, media strings `(max-width: 767px)` / `(min-width: 768px)` — intactos.

## Validación manual (CDP, Chrome headless, perfil nuevo)

- [x] **Estilos computados (portada)**: `.nav-toggle` y botones = `rgb(61,90,78)`; `.hero__brand` = `rgb(127,69,39)`; `.hero__tagline` = `rgb(61,90,78)`.
- [x] **Estilos computados (`/citas`)**: submit/input/días = `rgb(61,90,78)`; panel decorativo conserva salvia original.
- [x] **Foco por teclado real (Tab vía CDP)**: día del calendario → `outline: solid 2px rgb(48,69,75)` (antes: `outline: none`).
- [x] **A3**: `.search-page__back` → `margin-top: 36px`, `font-weight: 700`; `.placeholder__back` → `36px`.
- [x] **Mediciones `scrollHeight`/`scrollWidth`**: 12 páginas (6 rutas × 1280/375); `w` = 1265/360 ≤ viewport en todas (sin desborde).

## Evidencia visual (capturas CDP secuenciales)

| Archivo | Dimensiones |
|---|---|
| `portada-1280.png` | 1280×1406 |
| `servicios-1280.png` | 1280×1931 |
| `citas-1280.png` | 1280×1486 |
| `contacto-1280.png` | 1280×1156 |
| `buscar-1280.png` | 1280×900 |
| `articulos-1280.png` | 1280×900 |
| `portada-375.png` | 375×2347 |
| `servicios-375.png` | 375×2435 |
| `citas-375.png` | 375×2673 |
| `contacto-375.png` | 375×1566 |
| `buscar-375.png` | 375×1223 |
| `articulos-375.png` | 375×801 |

Revisión por imagen: identidad conservada (salvia en superficies, terracota en acentos),
texto legible, back-links alineados con el resto de páginas.

## Pendientes / fuera de alcance

- Refactor DRY del CSS (M1), medida de portada en pantallas grandes (A4), specs 001–006/015/016 sin enmienda (decisión: no tocar `specs/`).
- Capturas de hover de botón no incluidas (el estado se verifica por test de ratios + estilo computado).
