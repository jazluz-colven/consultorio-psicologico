# Decisión de diseño — Contraste accesible (WCAG 2.1 AA)

**Fecha:** 2026-10-12
**HU:** Pulido frontend sin HU propia (mantenimiento de accesibilidad; ramas de HU-001/004/005/006/015/016 afectadas solo en presentación)
**Estado:** Aprobada
**Afecta:** `static/css/main.css`, `tests/expected_content.py`, `tests/test_contraste.py` (nuevo),
`AGENTS.md` (tabla de paleta), RNF de accesibilidad de las specs existentes

## Problema

Auditoría de contraste (2026-10-12) sobre la paleta Serenidad Natural. Ratios
WCAG 2.1 (luminancia relativa) de los pares en uso:

| Par | Ratio | Requisito | Resultado |
|---|---|---|---|
| Texto `#30454B` sobre marfil `#F7F3EA` | 9.12 | 4.5 | ✅ |
| Texto marfil sobre botón salvia `#789B8A` | 2.77 | 4.5 | ❌ |
| Enlaces `#789B8A` sobre marfil | 2.77 | 4.5 | ❌ |
| Hover enlaces/botones `#D99A7A` sobre marfil | 2.14 | 4.5 | ❌ |
| `hero__tagline` `#789B8A` sobre verde agua `#B8D8CE` | 2.01 | 4.5 | ❌ |
| `hero__brand` «CONTENIDAS» `#D99A7A` sobre verde agua | 1.55 | 4.5 | ❌ |
| Mensajes de error `#D99A7A` sobre verde agua | 2.14 | 4.5 | ❌ |
| Badge «Ocupado» marfil sobre `#D99A7A` | 2.14 | 4.5 | ❌ |
| Borde de inputs `#789B8A`/`#E8D5B5` sobre marfil | 2.77 / 1.30 | 3 (1.4.11) | ❌ |
| Foco de días del calendario (outline eliminado) | ~1.55 efectivo | 3 (1.4.11) | ❌ |

`AGENTS.md` exige que los colores «cumplan requisitos de contraste y
accesibilidad». La paleta no tenía variantes oscuras para texto sobre color ni
color sobre fondo claro.

## Decisión

### 1. Dos tonos funcionales derivados (la paleta base no cambia)

Se añaden dos variables en `:root`, derivadas de los colores de marca ya
aprobados (salvia y terracota, oscurecidos hasta cumplir AA):

| Variable | Hex | Rol |
|---|---|---|
| `--color-primary-dark` | `#3D5A4E` | Salvia oscura: texto de enlaces, títulos de color, fondos de botones, bordes y focos funcionales |
| `--color-accent-dark` | `#7F4527` | Terracota oscura: hover de enlaces/botones, mensajes de error, badge «Ocupado», estado `is-bookable:hover` |

Ratios verificados (fórmula WCAG, luminancia relativa):

| Par | Ratio | Umbral |
|---|---|---|
| `#3D5A4E` sobre marfil | 6.84 | 4.5 ✅ |
| `#3D5A4E` sobre verde agua | 4.96 | 4.5 ✅ |
| Marfil sobre `#3D5A4E` (botón) | 6.84 | 4.5 ✅ |
| `#7F4527` sobre marfil | 6.81 | 4.5 ✅ |
| `#7F4527` sobre verde agua (errores) | 4.94 | 4.5 ✅ |
| Marfil sobre `#7F4527` (badge) | 6.81 | 4.5 ✅ |

Los 6 hex originales de la Serenidad Natural **se conservan** con sus roles
actuales (fondos, superficies, decoración, texto). Los tonos oscuros son
**derivados funcionales**, no nuevos colores de marca: no alteran la identidad,
solo hacen legible la interfaz.

### 2. Asignación

- **Texto sobre fondo claro** (enlaces, títulos en color, tagline, hints,
  estados del buscador, `placeholder__message`): `--color-primary-dark`.
- **Hover/foco de enlace y botón, errores, badge «Ocupado»,
  `is-bookable:hover`**: `--color-accent-dark` (con texto marfil cuando es
  fondo relleno).
- **Botones rellenos** (`.nav-toggle`, `.site-search__button`,
  `.services__link`, `.appointment__calendar-nav`, `.appointment__submit`):
  fondo `--color-primary-dark` + texto marfil; hover `--color-accent-dark`.
- **Estados del calendario y horas** (`is-selected`, hora marcada): fondo
  `--color-primary-dark` + texto marfil.
- **Bordes y focos funcionales** (inputs, días agendables, chips de hora,
  leyenda): `--color-primary-dark` (≥3:1). Decoración no esencial (divisores
  de filas de contacto, borde izquierdo de tarjetas) mantiene el salvia
  original por ser prescindible para entender el contenido.
- **Indicador de foco visible**: `outline: 2px solid var(--color-text)` donde
  el elemento ya tiene fondo de color propio; `--color-primary-dark` sobre
  marfil/verde. Se elimina el `outline: none` del calendario (WCAG 1.4.11).

### 3. Trazabilidad

- `tests/expected_content.py` → `PALETTE` incluye los 2 tonos nuevos (los 8
  tests de paleta `used <= expected.PALETTE` la importan).
- Nuevo `tests/test_contraste.py`: parsea `:root` y asierta los pares
  documentados (≥4.5 texto, ≥3 bordes/foco) — red de regresión.
- El HTML del correo (HU-008) **no** usa los tonos nuevos: su paleta sigue
  siendo la de 6 hex (`tests/test_email_service.py` intacto).

## Justificación

- **Accesibilidad AA (WCAG 2.1, 1.4.3 y 1.4.11)**: texto legible y foco
  visible, exigido por `AGENTS.md` («contraste y accesibilidad»).
- **Identidad intacta**: los tonos son oscurecimientos de salvia/terracota
  existentes; los 6 hex originales siguen cubriendo fondos y decoración.
- **Sin dependencias** (constitución #1): solo variables CSS.

## Alternativas descartadas

| Alternativa | Por qué se descarta |
|---|---|
| Solo los 6 hex (texto siempre `#30454B`, botones con texto oscuro sobre salvia a tamaño grande) | Pierde el color en hovers y varios textos; el «truco» de tamaño grande frágil ante cambios de copy. |
| Botones `#30454B` + marfil | Máxima legibilidad pero los botones dejan de ser salvia: cambio de identidad más visible. |
| Fondo salvia original + texto marfil agrandado (3:1 como texto grande) | Depende de que ningún copy baje de 18.66px bold; frágil. |

## Consecuencias

- Los botones y estados rellenos se ven en verde salvia oscuro en lugar de
  salvia claro; los enlaces y títulos de color en salvia oscura; hovers y
  errores en terracota oscura. Evidencia visual nueva en
  `docs/evidencias/pulido-contraste-aa/`.
- Los textos «paleta de 6 hex» de los `plan.md`/`task.md` de specs 001–006 /
  015 / 016 quedan **superados** por esta decisión y por la tabla de paleta
  de `AGENTS.md` (los specs no se modifican; la fuente de verdad de la
  restricción es `expected_content.PALETTE` + este documento).
- El correo de confirmación mantiene la paleta de 6 hex: es un medio distinto
  (clientes de correo) y su HTML inline ya cumple la paleta aprobada.
