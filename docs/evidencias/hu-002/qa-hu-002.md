# Evidencia QA — HU-002 (Spec 002 · Conocer el consultorio)

**HU:** HU-002
**Rama:** `feature/hu-002`
**Commits:** `c71c78c` (docs: spec + plan), `f782797` (feat), `a686a58` (plan: estado),
`6ed88eb` (evidencia), `8103b91` (justificación generalizada sin guiones)
**Fecha:** 2026-10-07 (actualizada tras la regeneración de capturas)

## Resumen

| Verificación | Comando | Resultado |
|---|---|---|
| Suite automatizada | `python -m pytest -q` | **45 PASS / 0 FAIL** |
| Regresión HU-001 | mismos 29 tests previos dentro de la suite | **29 PASS** |
| Servidor de desarrollo | `GET http://127.0.0.1:5000/nosotros` | **200** con «Misión» |
| Evidencia visual | `docs/evidencias/hu-002/*.png` | **2 archivos, PASS** |

16 pruebas nuevas agrupadas en los 13 TC del plan (§6.1); ninguna relajada ni
omitida. Ejecución única: `45 passed in 0.48s`.

## Cobertura de RF

| RF | Verificación | Resultado |
|---|---|---|
| RF-1 misión | `GET /nosotros` → 200 con `<h2>Misión</h2>` y literal completo en `<main>` (TC-002-001/003/005) | PASS |
| RF-2 visión | `<h2>Visión</h2>` + literal completo (TC-002-001/003/005) | PASS |
| RF-3 experiencia profesional | `<h2>Experiencia profesional</h2>` + literal completo (TC-002-001/003/005) | PASS |
| RF-4 valores | `<h2>Valores</h2>` + literal completo (TC-002-001/003/005) | PASS |
| RF-5 diferenciada de servicios y citas | `<main>` sin «Psicología Integral»/«Psiconutrición»/«Ver todos los servicios»/«Agendar cita», sin `<form>`/`<input>`; `POST /nosotros` → 405; literales sin textos de servicios (TC-002-006/007/009) | PASS |
| RNF-1 legible en escritorio y móvil | `viewport` presente, `@media (max-width…)`, colores ⊆ 6 hex de la paleta, `scrollWidth` = ancho pedido (1280 y 375 → sin desbordamiento) (TC-002-010) | PASS |
| CL-1 contenido faltante | `DEFAULT_*` = literales de la spec; campos vacíos/whitespace → fallback con `fallback_active=True` y ningún bloque vacío (TC-002-002/004) | PASS |
| CL-2 contenido excesivamente extenso | 4 bloques con `<h2>` + `.about { max-width: 65ch }` en CSS, sin truncar el texto (TC-002-011) | PASS |
| Criterios de finalización | E2E: portada → enlace «Nosotros» → 200 con misión visible; «Volver al inicio» → `/` (TC-002-012) | PASS |
| Regresión HU-001 | `/servicios`, `/articulos`, `/contacto`, `/citas` siguen «en construcción»; nav completa 200 desde `/nosotros`; 29 tests previos en verde (TC-002-008/013) | PASS |

## Evidencia visual

| Archivo | Dimensiones | Contenido comprobado | Resultado |
|---|---|---|---|
| `escritorio-1280.png` | 1280×1394 | cabecera sin botón «Menú» y nav de 6 accesos; `<h1>Nosotros</h1>`; 4 bloques salvia con títulos «Misión/Visión/Experiencia profesional/Valores» y sus literales completos **justificados y sin guiones** (bordes de línea en x375..904); «Volver al inicio» (y=1328-1340); pie con marca; columna centrada a 65ch; Palatino 18 px; solo colores de la paleta | PASS |
| `movil-375.png` | 375×1903 | marca + botón «Menú» salvia (DOM: `display: block` con `.site-nav` oculto); los 4 bloques apilados con literales completos **justificados y sin guiones** (DOM: `hyphens: none` en los 4); «Volver al inicio» y pie visibles; `scrollWidth` = 375 (sin desbordamiento horizontal) | PASS |

**Verificación tras `8103b91`** (CDP `Runtime.evaluate` con viewport exacto):

| Viewport | Resultado |
|---|---|
| 1280×1394 | los 4 `.about__text` con `text-align: justify` + `hyphens: none`; líneas 531·531·531·477 / 531·531·531·460 / 531·531·531·235 / 531·531·451 (las completas = ancho del bloque); `lang=es`; `scrollWidth`=1280 |
| 375×1903 | los 4 `.about__text` con justify + none; líneas 285×6·269 / 285×7·219 / 285×7·80 / 285×5·109; `scrollWidth`=375; `form`/`input` = 0; «Volver al inicio» presente |

**Método**: Chrome 154 headless vía DevTools Protocol
(`Emulation.setDeviceMetricsOverride` + `Page.captureScreenshot`, script
`capture_cdp.ps1`, perfil limpio en el puerto 9445, emulación fijada en la misma sesión
que captura). Las alturas se midieron con `Runtime.evaluate`
(`scrollHeight` 1394 px a 1280 y 1903 px a 375) y las capturas se regeneraron el
2026-10-07 con esas alturas exactas. Además, muestreo de píxeles sobre la captura de
escritorio confirma los bordes de línea justificados (x375..904 en las líneas
completas de los 4 bloques y última línea corta de cada uno).

## Defectos encontrados

- **Bug de plantilla detectado y corregido durante el desarrollo**: `{{ about.titles.values }}`
  resolvía al método `dict.values` de Jinja en lugar de la clave del diccionario y el
  título «Valores» se renderizaba como `<built-in method values…>`. Detectado por
  TC-002-005 en la primera ejecución (1 FAIL) y corregido con subíndice explícito
  `about.titles["values"]`. Vuelve a 45 PASS.
- Ningún defecto funcional pendiente.

## Pendientes de cierre

- [x] Spec 002 con literales y duda abierta cerrada (`c71c78c`).
- [x] `plan.md` aprobado y actualizado (`c71c78c`, `a686a58`).
- [x] Implementación y tests en verde (`f782797`; 45 PASS).
- [x] Evidencia QA + capturas escritorio/móvil (`6ed88eb`).
- [x] Commit/Push de la evidencia (`6ed88eb`).
- [x] Capturas y QA regenerados tras la justificación generalizada (`8103b91`).
- [ ] Aceptación de la HU.

## Veredicto

**PASS** — 45 tests en verde (los 29 de HU-001 intactos como regresión), cobertura
completa de RF-1..RF-5, RNF-1 y ambos casos límite, y evidencia visual escritorio/móvil
regenerada y verificada por DOM + muestreo de píxeles tras la justificación
generalizada. Único trámite pendiente: la aceptación de la HU.
