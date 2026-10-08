# Decisión de diseño — Identidad visual (nombre, cabecera y hero)

**Fecha:** 2026-10-08
**HU:** Enmienda de HU-001 (Spec 001 — Visualizar la página de inicio) y de HU-002/HU-003 en lo que referencian identidad
**Estado:** Aprobada
**Afecta:** `static/css/main.css`, `templates/base.html`, `templates/home/index.html`,
`consultorio/content/home_content.py`, `consultorio/content/hero_image.py`,
`consultorio/config.py`, `specs/001_visualizar-pinicio/spec.md` y su `plan.md`,
`tests/expected_content.py`, RNF-2

## Decisión

### 1. Nombre del consultorio → «Carolina Gómez»

Petición explícita del usuario (2026-10-08): **solo dejar «Carolina Gómez» donde
corresponda, en todo el sitio.**

- El literal `Consultorio Psicológico Carolina Gómez` pasa a **`Carolina Gómez`** en:
  `<h1>` del hero, cabecera (`.site-brand__name`), pie de página, `<title>` de todas
  las páginas (`base.html`, `about`, `services`), `Config.SITE_NAME` y el espejo de
  tests `tests/expected_content.py`.
- Al ser un texto contractual de la Spec 001, la especificación y su `plan.md` se
  enmiendan **antes** de tocar el código (regla de texto contractual de `AGENTS.md`).
- La marca secundaria **`Contenidas`** no se elimina: permanece visible en el hero de
  la portada (RF-7) y en el pie (`Carolina Gómez · Contenidas`).

### 2. Cabecera: ilustración de Contenidas + nombre

- La cabecera sustituye el texto en versalitas «CONTENIDAS» por la **ilustración
  `static/img/hero-contenidas.png` en miniatura** (`height: 3.25rem`) a la izquierda y
  **`Carolina Gómez`** a la derecha, en fila (`flex-direction: row`).
- El `alt` de la ilustración es `Contenidas`, por lo que la marca secundaria sigue
  siendo accesible en la cabecera; además RF-7 se verifica en el hero.
- `hero-contenidas.png` deja de ser la imagen representativa del hero y se reutiliza
  como logotipo de cabecera: **ningún asset se elimina del repositorio**.

### 3. Hero de la portada → `hero-presentacion.png`

- La imagen representativa (RF-2) pasa de la ilustración a la **fotografía real**
  `static/img/hero-presentacion.png` (380×511, retrato de la profesional en su
  consultorio con la leyenda «Salud mental»), suministrada por el consultorio.
- `width`/`height` del `<img>` se actualizan a 380×511 (evita saltos de layout, RNF-1).
- Nuevo texto alternativo literal (aprobado con la enmienda de la Spec 001):
  `Retrato de Carolina Gómez en su consultorio con la leyenda «Salud mental»`.
- **Se conserva el marco circular actual** (`.hero__figure img { border-radius: 50% }`),
  decisión explícita del usuario pese a que la foto es vertical (380×511) y el recorte
  será elíptico, ligerando cabeza y pies del retrato.

## Justificación

- **Registro personal.** El sitio presenta a la profesional: el nombre propio corto
  comunica cercanía y es más legible en títulos, cabecera y buscadores.
- **Coherencia de marca.** La ilustración «Contenidas» actúa como logotipo en la
  cabecera (donde el contenido es de navegación) y la fotografía profesional ocupa el
  espacio de presentación (hero), donde aporta confianza y cercanía (RNF-2).
- **Sin dependencias nuevas (constitución #1).** Todos los assets están versionados
  en `static/img/`; no se descarga nada desde terceros.
- **Sin cambios de RF.** Solo cambian literales y recursos asociados; los RF de la
  Spec 001 se conservan íntegros y sus tests se ajustan a los nuevos literales.

## Alternativas descartadas

| Alternativa | Por qué se descarta |
|---|---|
| Mantener «Consultorio Psicológico Carolina Gómez» en el `<h1>` y usar «Carolina Gómez» solo en la cabecera | El usuario pidió el cambio «donde corresponda», en todo el sitio. |
| Eliminar del todo la marca «Contenidas» | RF-7 de la Spec 001 exige su visibilidad en la portada. |
| Foto del hero en rectángulo redondeado | El usuario eligió conservar el marco circular existente. |
| Borrar `hero-contenidas.png` al dejar de ser hero | Se reutiliza como logotipo; además TC-001-009/019 ya no lo referencian pero el asset sigue disponible para cabecera. |

## Consecuencias

- Cambios de presentación: **ningún RF cambia de definición**, solo literales
  contractuales (nombre, alt) y el recurso de RF-2.
- `tests/expected_content.py` (espejo de literales) y los tests de portada se
  actualizan en el mismo PR (regla de `AGENTS.md` sobre textos contractuales).
- TC-001-008 (sin formularios) se acota a formularios de reserva/administración para
  admitir el formulario de búsqueda de la Spec 016.
- TC-001-004 (imagen representativa) se acota a la imagen del `<figure>` del hero,
  porque la cabecera pasará a contener el primer `<img>` del documento.
- La evidencia visual existente de HU-001/002/003 queda **histórica**: por decisión
  del usuario no se regeneran capturas, solo se documenta el cambio.
