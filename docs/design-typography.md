# Decisión de diseño — Tipografía de la portada

**Fecha:** 2026-10-07
**HU:** HU-001 (Spec 001 — Visualizar la página de inicio)
**Estado:** Aprobada
**Afecta:** `static/css/main.css`, `specs/001_visualizar-pinicio/plan.md` (D10), RNF-2

## Decisión

La portada utiliza una pila de tipografías **Palatino** (serif humanista de trazo
caligráfico) para todos los textos, y el párrafo de presentación del hero se alinea
**justificado**.

```css
font-family: "Palatino Linotype", "Book Antiqua", Palatino, "Palatino URW",
             "URW Palladio L", P052, serif;
```

Ámbito original de la justificación: **únicamente** `.hero__intro` (párrafo de
presentación). **Ampliado el 2026-10-07** a todos los párrafos de contenido, ver
sección «Justificación generalizada de párrafos».

## Ampliación del cuerpo base — 2026-10-07

Petición explícita del usuario: aumentar el tamaño de letra en **todo el sitio**.

**Decisión:** la base tipográfica pasa de **16 px a 18 px** mediante

```css
html {
    font-size: 112.5%;
}
```

- Es la única regla añadida: al declararse en la raíz, todos los tamaños expresados en
  `rem` (títulos, marca, tagline, frase de valores, espaciados y paddings) crecen en la
  misma proporción 1.125×, de modo que se conserva la armonía visual existente.
- Los cortes `@media` siguen en `px` (768), por lo que **no se alteran** los puntos de
  quiebre responsive ni la lógica del menú.
- 18 px es el cuerpo recomendado para lectura cómoda en pantalla (WCAG 1.4.4 permite
  escalar hasta 200 %); el interlineado 1.6 se mantiene.
- Alternativa descartada: fijar `font-size` en `body` — no escala los tamaños declarados
  en `rem`, que se calculan contra la raíz, y produciría un sitio a medio escalar.

No toca RF, textos literales ni RNF-2 (paleta intacta).

## Equilibrio del h1 del hero — 2026-10-07

Al pasar la base a 18 px el título del hero se partía en escritorio dejando «Gómez»
solo en la segunda línea. **Decisión:** aplicar `text-wrap: balance` a `.hero h1`, de
modo que el navegador reparte el título en líneas de longitud parecida
(«Consultorio Psicológico» / «Carolina Gómez»).

- Propiedad nativa del CSS, sin dependencias; los navegadores que no la soportan
  conservan el corte anterior.
- Afecta únicamente la presentación: sin cambios de RF, de textos literales ni de
  paleta.

## Justificación generalizada de párrafos — 2026-10-07

Petición explícita del usuario: **de ahora en adelante, todos los párrafos y textos
del sitio deben ir justificados.** Esta decisión anula el ámbito acotado anterior
(únicamente `.hero__intro`) y la alternativa «Justificar todos los párrafos» que
figuraba como descartada más abajo.

**Decisión:** `text-align: justify` con **`hyphens: none`** en todos los párrafos de
contenido, ajustados a su cajón de texto: **sin guiones visibles ni cortes de
palabras** (los saltos de línea se producen únicamente en espacios).

Ámbito aplicado el 2026-10-07 (confirmación del usuario): `/nosotros` (`.about__text`)
y portada (`.hero__intro`, `.service-card__summary`, `.values__line` y pie
`.site-footer`). Regla permanente incorporada a `AGENTS.md`.

- Se justifican párrafos de lectura; títulos, marcas, botones y enlaces conservan su
  alineación.
- Sustituye a cualquier `hyphens: auto` anterior (los guiones «-» de partición no
  deben verse en ninguna página).
- Cambio de presentación: sin cambios de RF ni de literales; la evidencia visual de
  las secciones afectadas debe regenerarse tras el ajuste.

## Justificación

- **Coherencia con la identidad.** La paleta Serenidad Natural y la ilustración de
  portada remiten a un registro cálido, artesanal y sereno. Palatino comparte ese
  registro: su trazo conserva la huella de la pluma frente al aspecto mecánico de
  Georgia o Times.
- **Legibilidad (RNF-1).** Es una serif de texto con buena lectura en cuerpos pequeños
  y en pantalla; el interlineado actual (1.6) ya es el recomendado para serif.
- **Sin dependencias nuevas (constitución #1).** Es una pila de fuentes del sistema:
  no se descarga nada desde terceros y la página sigue funcionando sin conexión.
- **Justificación acotada.** Alinear todo el sitio crea ríos blancos en anchos pequeños
  y perjudica la lectura en móvil; el párrafo largo del hero es el único bloque donde
  la justificación aporta un borde tipográfico limpio.

## Alternativas descartadas

| Alternativa | Por qué se descarta |
|---|---|
| **Charter / Constantia** | Serif de texto más firme y contemporánea; proyecta «profesional-serio» en lugar de «cálido», que es el registro del consultorio. |
| **Candara / Corbel (sans humanista)** | Deja el conjunto más ligero y accesible, pero rompe la continuidad con el sello dibujado a mano de la portada. |
| **Palatino en títulos + sans en cuerpo** | Dos familias añaden complejidad de mantenimiento sin necesidad: el sitio tiene un bloque de contenido corto y homogéneo. |
| **Google Fonts (Lora, Source Serif, etc.)** | Dependencia externa de terceros: requiere justificación y aprobación escrita (constitución #1) y rompe el funcionamiento sin red. |
| **Justificar todos los párrafos** | Genera espacios irregulares en móvil y en las tarjetas de servicio, de ancho reducido. **— Anulada el 2026-10-07:** el usuario decretó la justificación general; ver «Justificación generalizada de párrafos». |

## Consecuencias

- Cambia únicamente la presentación; **ningún texto literal ni RF** de la Spec 001 se
  ve afectado.
- La revisión de regresión debe comprobar RNF-1 (legibilidad en 1280 y 375) y RNF-2
  (coherencia institucional), y volver a emitir la evidencia visual.
