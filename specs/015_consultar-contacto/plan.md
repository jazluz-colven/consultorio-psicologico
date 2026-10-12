# Plan 015 — Consultar información de contacto (ampliación: cajón + iconos + mapa)

> Trazabilidad: **HU-015 → Spec 015 (`specs/015_consultar-contacto/spec.md`, enmendada 2026-10-12 con RF-7) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs` (Q5).
> Etapa actual: **PLAN DE AMPLIACIÓN APROBADO** (2026-10-12) por la usuaria (Q13).
> **Estado real verificado tras sincronizar `main` con `origin/main` (fast-forward a
> `f99490b`)**: HU-015 **v1 ya implementada, evidenciada y ACEPTADA/CERRADA** el
> 2026-10-12 (rama `feature/hu-015`, mergeada a `main`) con el **diseño por
> secciones/canales** (`templates/contact/index.html`, `test_contact_*`, QA PASS en
> `docs/evidencias/hu-015/qa-hu-015.md`). El remoto añade además despliegue en **Render**
> y `MEMORY.md` actualizado.
> Esta HU se **amplía** (decisión de la usuaria 2026-10-12, Q13) con: **RF-7 mapa** y
> **rediseño de presentación** — un **único cajón** con filas `icono + etiqueta + valor`
> (Q8/Q9). HU-015 no se reabre como historia nueva: se refactorea sobre la base ya
> mergeada, se enmienda la spec 015 y se regenera la evidencia.
> Rama: **`feature/hu-015-diseno`** desde `main` (`f99490b`). Baseline: **179 PASS / 0
> FAIL** (163 de HU-001..008/016 + 16 de HU-015 v1).

---

## 0. Alcance y cobertura

Implementa la **ampliación aprobada** de Spec 015 sobre `/contacto`: conservar los datos
de contacto ya funcionales (dirección, WhatsApp, correo, horarios, redes) y cambiar su
**presentación** a un **único cajón** (una fila por canal: icono SVG + etiqueta +
valor/enlaces), más el **mapa con la ubicación** (RF-7, enmienda §8.1) y el enlace de
respaldo «Abrir en Google Maps».

**Fuera de alcance** (igual que en v1 + D20): formulario de contacto, chat, gestión de
mensajes, administración de redes, envíos (specs 008/009), reservas desde contacto y
entrada de `/contacto` en el índice del buscador (HU-016).

**Sin modelo de datos SQLite**: el contenido estático de v1 (`content/contact_content.py`)
se **amplía** con los literales del mapa; no se crea ni se toca
`consultorio/persistence/` (constitución #5 no aplica).

**Sin dependencias nuevas** (constitución #1): Flask + Jinja + CSS propio + SVG inline
de autor; el `<iframe>` de Google Maps es contenido incrustado, no una dependencia.

**Dudas de la spec cerradas** (§7.1): Q1–Q3 (datos, redes, horarios) ya fijados y
vigentes en v1; Q8–Q12 (mapa, cajón, etiquetas, enmienda, descarte del plan previo) y
Q13 (ruta de trazabilidad tras descubrir el remoto). RF-3/RF-5/RF-7 son condicionales:
teléfono sin dato ⇒ sin fila (D16); sin dirección o sin consulta ⇒ sin mapa (CL-1/CL-5).

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Mostrar los datos de contacto disponibles | v1 intacta: §1 `contact_content`/`contact_service`/plantilla; §4 `GET /contacto`; §6 TC-015-009 (adaptado) |
| RF-2 | Mostrar la dirección cuando exista | v1 intacta + fila «Dirección» en el cajón; §5 D4; §6 TC-015-010 |
| RF-3 | Mostrar teléfono, WhatsApp y correo | v1 intacta: filas WhatsApp/Correo con `wa.me`/`mailto:`; sin «Teléfono» (D16); §6 TC-015-010 |
| RF-4 | Mostrar los horarios de atención | v1 intacta: fila «Horarios de atención»; §6 TC-015-011 |
| RF-5 | Mostrar enlaces a redes sociales oficiales | v1 intacta: fila «Redes sociales» con `target="_blank" rel="noopener"`; §6 TC-015-011 |
| RF-6 | Diferenciar los canales de contacto y sus datos | §3 filas diferenciadas; §4 «una `<li class="contact__row">` por canal con icono + etiqueta»; §5 D4/D18; §6 TC-015-012 (adaptado) + evidencia |
| RF-7 | Mostrar un mapa con la ubicación (enmienda §8.1) | §2 `MAP_*`; §3 `ContactMap`; §4 `<iframe>` + enlace; §5 D17/D19/D21; §6 TC-015-017/018/019 |
| RNF-1 | Legible en escritorio y móvil | §1 CSS `.contact-*` rework; §5 D10/D19; §6 TC-015-015 (adaptado) y evidencia |
| RNF-2 | Presentación clara y fácil de localizar | §4 orden fijo de filas + medida CSS; §5 D4/D10; §6 TC-015-012/015 |
| CL-1 | Dirección no aplicable | v1 (omisión de fila) + §3 omisión del mapa; §6 TC-015-018 |
| CL-2 | Algún canal de contacto no disponible | v1 intacta (omisión por campo); §6 TC-015-007 |
| CL-3 | Horarios no definidos | v1 intacta (`DEFAULT_OFFICE_HOURS`); §6 TC-015-006 |
| CL-4 | Enlace a una red social no disponible | v1 intacta (descarte de URL); §6 TC-015-008 |
| CL-5 | Mapa no disponible | §3 omisión del mapa sin ocultar la dirección; §5 D17/D21; §6 TC-015-018/019 |
| Finalización | Tests en verde + demo manual | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-7][CL-1..CL-5][RNF-1][RNF-2]` — Constitución #3 intacta. **No se crean
módulos nuevos**: se amplían los existentes de HU-015 v1 (constitución: no reescribas
lo que ya funciona; el blueprint, la ruta, `placeholders.py` y `create_app()` no se
tocan).

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   └── contact_content.py      # + MAP_QUERY, MAP_EMBED_URL, MAP_LINK_URL,
│   │                               #   MAP_LINK_LABEL, MAP_FRAME_TITLE, DEFAULT_MAP_QUERY
│   │                               #   [RF-7][CL-1][CL-5]
│   ├── services/
│   │   └── contact_service.py      # + ContactMap; ContactView.map;
│   │                               #   resolución del mapa en validate_contact()   [RF-7][CL-1][CL-5]
│   └── web/
│       └── contact.py              # SIN CAMBIOS (GET /contacto)         [RF-1..RF-7]
├── templates/
│   └── contact/
│       └── index.html              # REFACTORIZA: cajón .contact__panel con <ul> de
│                                   # filas (icono SVG + etiqueta + valor/enlaces) +
│                                   # bloque .contact__map (iframe + enlace)         [RF-6][RF-7][RNF-*]
├── static/
│   └── css/main.css                # REFACTORIZA .contact-*: grid 2 col ≥900 px,
│                                   # panel, filas, iconos, mapa                     [RNF-1][RNF-2]
└── tests/
    ├── expected_content.py         # + CONTACT_MAP_* (espejo de los MAP_* de la spec)
    │                               #   [RF-7]
    ├── test_contact_content.py     # + TC-015-017 (literales del mapa)     [RF-7]
    ├── test_contact_service.py     # + TC-015-018 (ContactMap y CL-1/CL-5)  [RF-7][CL-1][CL-5]
    ├── test_contact_routes.py      # TC-015-009/012 adaptados + TC-015-019  [RF-1][RF-6][RF-7]
    └── test_hu_015.py              # TC-015-015 adaptado (grid 2 col)       [RNF-1][RNF-2]
```

Responsabilidades: **las mismas de v1** (§ del plan original de HU-015), con el único
cambio de que la plantilla pasa de «un `<section>` por canal» a «un cajón con una fila
por canal» (presentación; sin condicionales de negocio) y el servicio gana el campo
`map`.

---

## 2. Fuente de contenido (ampliación)

`[RF-7][CL-1][CL-5]` — Se conservan **sin cambio** todos los literales vigentes de la
spec 015 (`CONTACT_PAGE_TITLE`, `ADDRESS_LINES`, `PHONE`, `WHATSAPP`, `EMAIL`,
`OFFICE_HOURS`, `SOCIAL_LINKS`, `CONTACT_BLOCK_LABELS` y sus `DEFAULT_*`). Se añade:

```python
# --- RF-7 (enmienda §8.1; aprobado 2026-10-12) ------------------------------
MAP_QUERY: str = "Calle 34 #29-18, Mejoras Públicas, Bucaramanga, Colombia"
MAP_EMBED_URL: str = (
    "https://www.google.com/maps?q=" + quote(MAP_QUERY, safe="") + "&output=embed"
)
MAP_LINK_URL: str = (
    "https://www.google.com/maps/search/?api=1&query=" + quote(MAP_QUERY, safe="")
)
MAP_LINK_LABEL: str = "Abrir en Google Maps"
MAP_FRAME_TITLE: str = "Ubicación del consultorio en Google Maps"
DEFAULT_MAP_QUERY: str = MAP_QUERY
```

Reglas: `MAP_QUERY` sobre `.strip()`; vacío (vivo y default) ⇒ **sin mapa** (CL-5);
`quote` de `urllib.parse` (stdlib). Los literales están fijados en la spec 015 (§8.1) y
su espejo en `tests/expected_content.py` (prefijo `CONTACT_MAP_*`, para no romper los
nombres ya usados por v1).

---

## 3. Algoritmo en pseudocódigo (delta sobre v1)

`[RF-7][CL-1][CL-5]` — `validate_contact()` y helpers de v1 se conservan; se añade:

```text
@dataclass ContactMap: embed_url, link_url, link_label, title
ContactView + map: ContactMap | None

FUNCTION _resolve_map(address_lines) -> (ContactMap | None, used_default):
    mq, used = _resolve(MAP_QUERY, DEFAULT_MAP_QUERY)      # patrón vivo → default
    IF NOT address_lines OR NOT mq: RETURN None, used      # CL-1 / CL-5
    RETURN ContactMap(embed_url=MAP_EMBED_URL, link_url=MAP_LINK_URL,
                      link_label=MAP_LINK_LABEL, title=MAP_FRAME_TITLE), used

FUNCTION validate_contact():                                # v1 + una línea
    ...                                                     # v1 sin cambios
    map_block, map_used = _resolve_map(addr)
    fallback |= map_used
    RETURN channels, hours, socials, map_block, fallback

FUNCTION get_contact_view():
    channels, hours, socials, map_block, fallback = validate_contact()
    RETURN ContactView(title, channels, hours, socials, titles,
                       map=map_block, fallback_active=fallback)

# --- presentación (plantilla; sin lógica) ----------------------------------
RENDER cajón .contact__panel:
    FOR channel IN channels:  fila(icono(channel.key), titles[key],
                                   lineas | enlace(value, href))
    IF hours:                 fila(icono("hours"), titles["hours"], lista de horarios)
    IF socials:               fila(icono("social"), titles["social"], enlaces externos)
RENDER .contact__map SI contact.map:
    iframe[src=embed_url, title=contact.map.title, loading="lazy"] +
    a[href=link_url, target=_blank, rel=noopener] = link_label
```

Orden fijo de filas (heredado de v1): address → phone(omitido) → whatsapp → email →
hours → social. Nunca una fila sin contenido (RF-6).

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF-ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Servidor de revisión | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C |
| `python -m pytest -q` | Suite completa (179 actuales + 3 nuevos) | `N passed` | `0` / `1` |
| `python -m pytest tests/test_hu_015.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-1..RF-7]`

Sin cambios respecto de v1: `GET /contacto` → **200**; métodos escritores → **405**;
`GET /contacto/<recurso>` → **404**; `/articulos` sigue placeholder; resto intacto.

**Contrato semántico de `GET /contacto` (ampliado; lo que verifican los tests):**

```text
[RF-1] <h1 class="contact__title">Contacto</h1> y el cajón .contact__panel
       con ≥1 fila dentro de <main>                            → absent ⇒ FAIL
[RF-2] fila «Dirección» con las 3 líneas de la spec            → ausente ⇒ FAIL
[RF-3] fila WhatsApp (a[href="https://wa.me/573168756020"]) y
       fila Correo (a[href^="mailto:"]); sin fila «Teléfono»
       ni `tel:` (D16)                                          → ausente ⇒ FAIL
[RF-4] fila «Horarios de atención» con Mañana y Tarde          → ausente ⇒ FAIL
[RF-5] fila «Redes sociales» con <a target="_blank" rel="noopener"> → ausente ⇒ FAIL
[RF-6] ≥5 <li class="contact__row">; cada una con su <svg
       aria-hidden="true"> y su etiqueta; sin datos de una
       fila dentro de otra                                      → ausente/mixto ⇒ FAIL
[RF-7] <iframe src*="www.google.com/maps" title no vacío
       loading="lazy"> + <a href*="www.google.com/maps"
       target="_blank" rel="noopener">Abrir en Google Maps</a>;
       la dirección escrita visible fuera del iframe           → ausente ⇒ FAIL
[RNF-1] viewport, .contact con max-width, @media (min-width: 900px) con
        grid-template-columns de 2 columnas, paleta ⊆ 6 hex,
        justify + hyphens:none en filas y enlaces              → absent ⇒ FAIL
[RNF-2] orden fijo Dirección → WhatsApp → Correo → Horarios → Redes → Mapa
                                                                        ⇒ FAIL
[CL-1] sin dirección y default → sin mapa                       → mapa sin datos ⇒ FAIL
[CL-5] MAP_QUERY vacío → sin mapa y dirección visible           → dirección oculta ⇒ FAIL
[alcance] <main> sin <form>/<input>, sin chat                   → presente ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Sin cambios de capa web**: `web/contact.py`, `placeholders.py` y `create_app()` quedan como en v1 | HU-015 v1 aceptada y mergeada; la ampliación es de presentación + contenido | *Rehacer el blueprint*: reescribir lo que ya funciona (regla de oro del AGENTS) | RF-1..7 |
| D2 | **Se amplía `content/contact_content.py`** con `MAP_*` (no se crea módulo nuevo) | Mismo criterio de v1 (contenido estático versionado, D2 del plan original); los literales v1 se conservan idénticos | *Módulo `map_content.py`:* fragmenta el contenido de una misma spec | RF-7 |
| D3 | **`validate_contact()` de v1 se conserva y gana `_resolve_map()`** (patrón vivo → default → omisión) | Mínimo churn sobre código aceptado y testeado; misma semántica de `fallback` (D15 de v1) | *Reescribir el servicio como `rows` uniformes*: cambio grande sin requisito, reescribiría 16 tests verdes sin necesidad | RF-7, CL-1, CL-5 |
| D4 | **Un único cajón `.contact__panel` con una fila por canal (`<li class="contact__row">`: icono SVG + etiqueta + valor)**; sustituye al «un `<section class="contact__block">` por canal» de v1 | Decisión de la usuaria (Q9, 2026-10-12): «en un solo cajón los datos». RF-6 se satisface con filas **diferenciadas y localizables**; el cajón es más escaneable y libera el mapa como companion visual | *Mantener las secciones de v1*: contradice la decisión de diseño aprobada. *Párrafo único mezclado*: impide verificar RF por canal | RF-6, RNF-2 |
| D5 | **Los enlaces de fila conservan el marcado exacto de v1** (`<a href="…">valor</a>`, redes con `target="_blank" rel="noopener"`) | Minimiza el churn de TC-015-010/011 (siguen pasando) y mantiene la accesibilidad ya validada | *Envolver todo en botones/JS*: dependencia innecesaria | RF-3, RF-5 |
| D6 | **Los literales del mapa están fijados en la spec 015 (§8.1) antes de codificar** y su espejo usa el prefijo `CONTACT_MAP_*` | Spec primero (constitución #2); el prefijo evita romper los nombres `CONTACT_*` ya usados por los tests de v1 | *Espejo con los nombres `MAP_*` crudos*: colisión de semántica con el contenido de v1 y con el historial de la rama | RF-7 |
| D7 | **Los TC de v1 que afirman el marcado por secciones se adaptan al nuevo contrato** (TC-015-009 y TC-015-012) | El contrato de marcado cambia por decisión de diseño aprobada; las aserciones se **ajustan, no se relajan**: siguen exigiendo datos por canal, etiquetas, ausencia de «Teléfono» y sin mezclas | *Borrar los tests*: pierde la cobertura de RF-2..RF-6. *Dejarlos rojos*: no se puede declarar la HU | RF-1, RF-6 |
| D8 | **Iconos SVG inline propios** (pin, chat, sobre, reloj, Instagram) como markup en la plantilla, con `aria-hidden="true"` y `currentColor` | RF-6 y la imagen de referencia de la usuaria; nítidos en cualquier DPI, cero peticiones, paleta vigente | *Font Awesome/Lucide por CDN*: dependencia externa (constitución #1). *PNG por icono*: pesados y escalan mal | RF-6, RNF-1 |
| D9 | **Mapa = `<iframe>` de Google Maps sin API key** (`…/maps?q=<consulta>&output=embed`) + enlace de respaldo `maps/search/?api=1&query=`; emisión condicionada a dirección | Decisión de la usuaria (Q8); sin API key no hay secreto ni cuota (lección HU-007) y los tests no hacen red | *API key*: secreto+cuota. *Imagen estática*: no navegable. *Librería JS de mapas*: dependencia | RF-7, CL-1, CL-5 |
| D10 | **Layout en 2 columnas ≥900 px (cajón ‖ mapa) y una columna <900 px (cajón primero, mapa debajo)**; `.contact` pasa de `max-width: 65ch` a grid responsivo | Decisión de la usuaria (Q9); dato primero en móvil, mapa con igual altura en escritorio | *Mapa superior a todo el ancho*: roba el foco al dato. *Dos columnas en móvil*: ilegible | RF-7, RNF-1, RNF-2 |
| D11 | **Sin formulario ni chat** (v1 intacta) | Fuera de alcance explícito de la spec | *Form con `mailto:`*: obsoleto y sin gestión | fuera de alcance |
| D12 | **«Volver al inicio» se conserva** al pie | Coherencia con v1 y con el resto de páginas | *Quitarlo*: callejón sin salida | RF-1 |
| D13 | **Horarios en bloques Mañana/Tarde coherentes con la agenda de la spec 004** (v1 intacta) | Una sola verdad operativa | *Texto libre*: imposible de validar | RF-4, CL-3 |
| D14 | **`SOCIAL_LINKS` con `platform`/`label`/`url`, solo `https://` y sin duplicados** (v1 intacta) | RF-5 condicional | *Redes fijas en la plantilla*: mostraría no aprobadas | RF-5, CL-4 |
| D15 | **`fallback_active` en `ContactView`** (v1 intacta) + `map_used` integrado | La degradación del mapa es observable en tests unitarios | *Ocultar la degradación*: CL-1/CL-5 no verificables | CL-1, CL-5 |
| D16 | **Sin fila «Teléfono»** (`PHONE = ""`, v1 intacta) | RF-3 condicional; el estado normal no es degradación | *Teléfono inventado*: dato falso | RF-3, CL-2 |
| D17 | **`ContactMap` dataclass congelada + campo `map: ContactMap | None` en `ContactView`** | Trazable y testeable sin inspeccionar HTML; `None` = CL-1/CL-5 | *URL suelta en el view*: no verificable ni estructurado | RF-7 |
| D18 | **La fila de horarios y la de redes usan los mismos `titles` de v1** (`resolve_block_titles()`) | Etiquetas de contrato sin duplicar literales | *Nuevos literales de fila*: duplicaría contrato y espejo | RF-6 |
| D19 | **El mapa es `loading="lazy"` con `title` accesible y la dirección escrita siempre visible fuera del iframe** | CL-5: iframe caído ⇒ el visitante sigue teniendo dirección y enlace (RF-2 independiente de RF-7) | *Mapa como única fuente de la dirección*: iframe caído deja la sección muda | RF-7, CL-5, RNF-2 |
| D20 | **`/contacto` sigue fuera del índice del buscador** (v1 intacta) | La spec 015 no lo pide | *Añadirlo por conveniencia*: funcionalidad no especificada | fuera de alcance |
| D21 | **Evidencia regenerada sobre la misma carpeta** `docs/evidencias/hu-015/` (capturas nuevas + sección «Ampliación 2026-10-12» en `qa-hu-015.md`) | La HU no se cierra dos veces: la ampliación deja constancia en el informe QA existente y con nuevas capturas | *Carpeta hu-015-diseno*: parte la evidencia de una misma HU en dos sitios | finalización |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` · `python -m pytest tests/test_hu_015.py -v`.
Baseline: **179 PASS / 0 FAIL** (v1 intacta). Se **amplían 3 tests** y **se añaden 3**;
total previsto **182**.

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-015-001..008 | `test_contact_content.py` / `test_contact_service.py` | **V1 intacta** (números de la v1): contenido, formatos, socials y CL-1..CL-4 siguen en verde sin tocarlos | RF-1..RF-5, CL-1..CL-4 |
| TC-015-009 *(adaptado)* | `test_contact_routes.py` | `<h1 class="contact__title">Contacto</h1>` + cajón `.contact__panel` con ≥1 `.contact__row` | RF-1 |
| TC-015-010 | `test_contact_routes.py` | Dirección + `wa.me` + `mailto:`; sin «Teléfono» ni `tel:` (marcado de enlace idéntico a v1 ⇒ sin cambios) | RF-2, RF-3 |
| TC-015-011 | `test_contact_routes.py` | Horarios (Mañana/Tarde) y redes con `target="_blank" rel="noopener"` | RF-4, RF-5 |
| TC-015-012 *(adaptado)* | `test_contact_routes.py` | **RF-6:** ≥5 `<li class="contact__row">`, cada una con `<svg` `aria-hidden="true"` y etiqueta visible; sin datos de una fila dentro de otra (sustituye a las 5 `<section>` con `<h2>`) | RF-6, RNF-2 |
| TC-015-013 | `test_contact_routes.py` | POST/PUT/DELETE → **405**; `GET /contacto/<recurso>` → **404** | página única |
| TC-015-014 | `test_contact_routes.py` | Regresión: placeholders `["/articulos"]`, nav de 6 hrefs, buscador presente | regresión |
| TC-015-015 *(adaptado)* | `test_hu_015.py` | RNF: viewport, `.contact` con `max-width`, **`@media (min-width: 900px)` con `grid-template-columns` de 2 columnas**, `@media (max-width…)`, paleta ⊆ 6 hex, `justify`+`hyphens: none` en `.contact__row` y enlaces del mapa | RNF-1, RNF-2 |
| TC-015-016 | `test_hu_015.py` | E2E portada → Contacto → Volver; `<main>` sin `<form>`/`<input>` | fuera de alcance |
| **TC-015-017** *(nuevo)* | `test_contact_content.py` | `CONTACT_MAP_EMBED_URL` empieza por `https://www.google.com/maps?q=` y termina en `&output=embed` con la consulta de `CONTACT_MAP_QUERY` URL-encoded; `CONTACT_MAP_LINK_URL` contiene `query=`; `CONTACT_MAP_LINK_LABEL` = «Abrir en Google Maps»; `CONTACT_MAP_FRAME_TITLE` no vacío | RF-7 |
| **TC-015-018** *(nuevo)* | `test_contact_service.py` | `get_contact_view().map` con `embed_url`/`link_url`/`link_label`/`title` y `fallback_active=False`; **CL-1:** dirección y default vacíos (monkeypatch) → `map is None`; **CL-5:** `MAP_QUERY` vacío (monkeypatch) → `map is None` con dirección intacta y `fallback_active=True` | RF-7, CL-1, CL-5 |
| **TC-015-019** *(nuevo)* | `test_contact_routes.py` | `<iframe src` con `www.google.com/maps`, `title` no vacío y `loading="lazy"` + `<a>` «Abrir en Google Maps» con `target="_blank" rel="noopener"`; la dirección escrita aparece **fuera** del iframe | RF-7, CL-5 |

### 6.2 Pirámide

1. **Unitarias** — `contact_content` y `contact_service` (v1 + mapa). `[RF-7][CL-1][CL-5]`
2. **Integración HTTP** — `test_client` sobre `/contacto` y regresión. `[RF-1..RF-7]`
3. **Regresión** — suite completa: los **179** tests actuales (incluidos los 16 de v1,
   con 3 adaptados) + **3** nuevos = **182**. `[todos]`
4. **Visual/manual** — capturas CDP 1280 (cajón ‖ mapa) y 375 (cajón sobre mapa) +
   comprobación en vivo del embebido. `[RF-6][RF-7][RNF-1]`

### 6.3 Ejecución y evidencia

- Las 3 adaptaciones (TC-009/012/015) **ajustan el selector al nuevo contrato**; no se
  elimina ninguna aserción de dato, etiqueta, enlace o paleta (skill `pytest-qa`).
- Sin red en los tests: el iframe se verifica por atributos del HTML.
- Evidencia en `docs/evidencias/hu-015/`: capturas regeneradas
  (`escritorio-1280.png`, `movil-375.png`) y sección «Ampliación 2026-10-12» en
  `qa-hu-015.md` con PASS/FAIL por TC y checkbox (D21).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1–Q3 | Datos, redes y horarios | **Vigentes desde v1** (2026-10-12); no se tocan. |
| Q4 | Rama | **`feature/hu-015-diseno` desde `main` (`f99490b`)** — nombre nuevo porque `feature/hu-015` ya existe con la v1 mergeada. |
| Q5 | Persistencia | **Sin SQLite** (contenido estático, D2). |
| Q6 | ¿Formulario? | **No** (fuera de alcance). |
| Q7 | Estructura | **Página única `/contacto`** (v1 intacta). |
| Q8 | Tipo de mapa (usuaria 2026-10-12) | **Iframe interactivo de Google Maps sin API key** + enlace de respaldo (D9). |
| Q9 | Presentación (usuaria 2026-10-12) | **Un solo cajón** con filas `icono SVG + etiqueta + valor` (D4/D8); **2 columnas ≥900 px, apilado <900 px** (D10). |
| Q10 | Etiquetas | Se **conserva «Dirección»**; el mapa usa `MAP_FRAME_TITLE`. |
| Q11 | Enmienda de la spec | **Autorizada y ejecutada el 2026-10-12**: RF-7 + literales `MAP_*` + caso límite del mapa en la spec 015. |
| Q12 | Plan/task de la primera sesión | **Descartados**: describían «desde cero» y el remoto ya tenía la v1. |
| Q13 | Trazadera tras sincronizar (2026-10-12) | **Ampliar la HU-015 existente** (decisión de la usuaria): refactor sobre la base mergeada, enmienda de la spec 015 y regeneración de evidencia; no se crea una HU nueva. `main` sincronizado por fast-forward y `Campos_n8n.xlsx` queda sin versionar. |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Aprobación de este plan de ampliación por la usuaria (2026-10-12, Q13).
- [x] Sincronizar `main` con `origin/main` (fast-forward `f99490b`) y crear
      `feature/hu-015-diseno`.
- [x] Enmienda de la spec 015 con §8.1 (RF-7 + `MAP_*` + caso límite) sobre la rama.
- [ ] Reescribir `task.md` alineado con este plan (ampliación).
- [ ] Commit inicial de spec + plan + task en la rama.
- [ ] Confirmar baseline `python -m pytest -q` → **179 PASS / 0 FAIL**.
- [ ] Ampliar contenido, servicio, plantilla y CSS (§1–§4).
- [ ] Tests: TC-015-009/012/015 adaptados + TC-015-017/018/019 nuevos → suite
      **182 PASS / 0 FAIL**.
- [ ] Evidencia: capturas regeneradas 1280/375 + sección de ampliación en
      `qa-hu-015.md` (veredicto) con demo sobre el servidor.
- [ ] Commits por fase, push, actualización de `MEMORY.md`.
- [ ] Aceptación de la ampliación por la usuaria (checkbox en `qa-hu-015.md`).
- [ ] Dejar el servidor de revisión en marcha y comunicar la URL (AGENTS.md).

---

## 8. Secuencia de implementación

0. ~~Sincronización~~ (hecha): `main` → `f99490b`; rama `feature/hu-015-diseno`.
1. ~~Spec primero~~ (hecha): enmienda RF-7 + `MAP_*` en la spec 015.
2. **Plan**: este `plan.md` (aprobado por la usuaria).
3. **task.md**: desglose de la ampliación (< 30 min por tarea).
4. Espejo: `CONTACT_MAP_*` en `tests/expected_content.py`.
5. Contenido: `MAP_*` en `consultorio/content/contact_content.py`.
6. Servicio: `ContactMap` + campo `map` + `_resolve_map()` en
   `consultorio/services/contact_service.py`.
7. Plantilla: refactor de `templates/contact/index.html` a cajón + filas con iconos +
   bloque mapa (D4/D8/D19).
8. CSS: refactor de `.contact-*` en `static/css/main.css` (grid 2 col, panel, filas,
   iconos, mapa; paleta intacta; párrafos justificados sin guiones).
9. Tests: adaptar TC-015-009/012/015 → añadir TC-015-017/018/019 → `python -m pytest -q`
   en verde (182).
10. Evidencia: demo manual + capturas CDP 1280/375 + sección de ampliación en
    `qa-hu-015.md` → `MEMORY.md` → commits por fase → push.
