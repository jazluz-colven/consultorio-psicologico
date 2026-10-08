# Plan 016 — Buscar contenido del sitio

> Trazabilidad: **HU-016 → Spec 016 (`specs/016_buscar-contenido/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs` (Q5).
> Etapa actual: **PLAN APROBADO** (2026-10-08): alcance y literales aprobados por la
> usuaria en la misma sesión en que se aprobó el rediseño de identidad.
> Rama: **`feature/identidad-buscador`** (incluye además la enmienda de identidad de la
> Spec 001 — ver `docs/design-identity.md` — y el cambio de tipografía a Open Sans —
> ver `docs/design-typography.md`).

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 016: un formulario de búsqueda en la
cabecera (bajo el menú) y una página de resultados `GET /buscar?q=…` sobre el
contenido estático actual del sitio.

**Fuera de alcance**: blog (Spec 013), filtrado en vivo con JavaScript, historial y
sugerencias, base de datos o índice persistente, administración de contenidos.

**Sin modelo de datos SQLite**: el índice se construye en memoria desde los módulos
`content/` existentes (mismo criterio D2 del plan 001; la constitución #5 se activa con
la primera HU que use base de datos). No existe capa `persistence/`.

**Decisión de alcance (2026-10-08, usuaria)**: buscador **funcional sobre el contenido
actual** (portada, Nosotros, Servicios y enlaces de navegación).

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Página de resultados con título, extracto y enlace | §1 `search_service` + `web/search.py` + `templates/search/index.html`; §3 `search()`; §4 `GET /buscar`; §5 D1/D4; §6 TC-016-001/002/007 |
| RF-2 | Mensaje cuando no hay coincidencias | §3 `search()` devuelve lista vacía; §4 contrato semántico; §5 D5; §6 TC-016-003 |
| RF-3 | Consulta vacía → mensaje con 200 | §4 validación de `q` en el blueprint; §5 D3; §6 TC-016-004 |
| RF-4 | Formulario en la cabecera de `base.html` | §1 `base.html` (fuera del `<nav>`); §5 D2; §6 TC-016-005 |
| RF-5 | Insensible a mayúsculas y acentos | §3 `_normalize()` con `unicodedata`; §5 D6; §6 TC-016-006 |
| RNF-1 | Legible en escritorio y móvil, paleta y tipografía vigentes | §1 `.site-search`/`.search-*` mobile-first; §5 D7; §6 TC-016-008 y validación visual |
| RNF-2 | Sin dependencias nuevas (constitución #1) | §3 librería estándar `unicodedata`; §5 D6; §6 revisión de código |
| Finalización | Tests en verde + demo manual | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-5][RNF-1][RNF-2]` — Constitución #3: contenido, lógica y presentación
separadas. Se conserva la estructura por capas (D1/Q2 del plan 001) y el patrón de
blueprint validado en HU-002/003.

```text
Consultorio_Carolina/
├── consultorio/
│   ├── services/
│   │   └── search_service.py       # build_index(), search(query), _normalize()
│   │                             #   [RF-1][RF-2][RF-5][RNF-2]
│   └── web/
│       └── search.py               # blueprint "search": GET /buscar
│                                 #   [RF-1][RF-2][RF-3]
├── templates/
│   ├── base.html                   # + <form class="site-search"> bajo </nav>,
│   │                             #   FUERA del <nav>               [RF-4]
│   └── search/index.html           # h1 «Resultados de búsqueda» +
│                                 # lista de resultados o mensajes  [RF-1][RF-2][RF-3]
├── static/
│   └── css/main.css              # .site-search + .search-* mobile-first;
│                                 #   paleta y tipografía intactas   [RNF-1]
└── tests/
    ├── expected_content.py       # + SEARCH_* (espejo de literales)  [RF-1..RF-3]
    ├── test_search_service.py    # índice, coincidencias, acentos    [RF-1][RF-2][RF-5]
    ├── test_search_routes.py     # contrato HTTP /buscar + presencia
    │                             # del formulario en la cabecera     [RF-1..RF-4]
    └── test_hu_016.py            # RNF + fuera de alcance            [todos]
```

Responsabilidades (sin solaparse):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `services/search_service.py` | Construir el índice desde `content/`, normalizar y buscar, devolver resultados con título/extracto/URL | Escribir HTML, manejar request/response |
| `web/search.py` | Método/ruta, validar `q`, status code, `render_template` | Consultar contenido directamente ni normalizar texto |
| `templates/search/index.html` | Marco semántico de resultados y mensajes | Contener lógica de búsqueda |
| `templates/base.html` | Emitir el formulario GET bajo el menú | Lógica de negocio |

`create_app()` registra `search_bp` junto a `about_bp`, `home_bp`, `sections_bp` y
`services_bp`.

---

## 2. Índice de contenido buscable

`[RF-1]` — Contenido **estático versionado en el repositorio**, reutilizado desde los
módulos existentes (sin duplicar literales):

| Fuente | Campos indexados | URL de resultado |
|---|---|---|
| `content/home_content.py` | `tagline`, `intro` | `/` |
| `content/services_highlights.py` | `name`, `summary` de cada servicio | `/servicios` |
| `content/home_content.py` | `TRUST_LINE` | `/` |
| `content/about_content.py` | `mission`, `vision`, `experience`, `values` (+ títulos) | `/nosotros` |
| `content/services_catalog.py` | `name`, `description`, `benefits` | `/servicios` |
| `content/nav_links.py` | `label` de cada enlace | su `url` |

Cada entrada del índice: `{"title": …, "text": …, "url": …}`. El **título** es el
encabezado humano del resultado (nombre de sección, servicio o bloque); el **text** es
el cuerpo contra el que se busca y del que se recorta el extracto.

---

## 3. Algoritmo en pseudocódigo

`[RF-1][RF-2][RF-5][RNF-2]`

```text
FUNCTION _normalize(s):
    # insensible a mayúsculas y acentos (unicodedata, stdlib)
    flat = unicodedata.normalize("NFKD", s)
    RETURN "".join(c FOR c IN flat IF not unicodedata.combining(c)).lower()

FUNCTION build_index():
    entries = []
    entries.ADD(title="Presentación", text=tagline + " " + intro, url="/")
    FOR s IN services_highlights: entries.ADD(title=s.name, text=s.summary, url=s.url)
    entries.ADD(title="Frase de valores", text=TRUST_LINE, url="/")
    FOR block IN about_content: entries.ADD(title=block.title, text=block.text, url="/nosotros")
    FOR s IN services_catalog: entries.ADD(title=s.name,
                                           text=description + benefits, url="/servicios")
    FOR link IN nav_links: entries.ADD(title=link.label, text=link.label, url=link.url)
    RETURN entries

FUNCTION search(query):
    q = _normalize(query.strip())
    IF q == "": RETURN (EMPTY, "empty")
    hits = []
    FOR e IN build_index():
        IF q IN _normalize(e.text) OR q IN _normalize(e.title):
            hits.ADD(SearchResult(title=e.title, url=e.url,
                                  snippet=_snippet(e.text, q)))
    RETURN hits, "ok"

FUNCTION _snippet(text, q, width=120):
    # ventana de ~width caracteres centrada en la primera coincidencia
```

```text
# --- capa web -------------------------------------------------------------
FUNCTION handle_search(request):
    q = (request.args.get("q") or "").strip()
    IF q == "": RETURN render(search/index, status="empty", q="")   # RF-3, 200
    hits, _ = SearchService.search(q)
    IF hits VACÍO: RETURN render(search/index, status="no_results", q=q)  # RF-2, 200
    RETURN render(search/index, status="results", hits=hits, q=q)   # RF-1, 200

FUNCTION handle_search_wrong_method(): RETURN error_405()           # solo GET
```

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF-ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C |
| `python -m pytest -q` | Suite completa | `N passed` | `0` / `1` |
| `python -m pytest tests/test_hu_016.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-1..RF-4]`

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `GET` | `/buscar?q=<término>` | `search/index.html` con lista de resultados (título, extracto, enlace) | **200** |
| `GET` | `/buscar?q=` (vacío o ausente) | mensaje `Escribe un término para buscar en el sitio.` | **200** |
| `GET` | `/buscar?q=<sin coincidencias>` | mensaje `No se encontraron resultados para «…».` | **200** |
| `POST/PUT/DELETE` | `/buscar` | `errors/405.html` | **405** |
| `GET` | otras rutas | sin cambios (regresión) | 200/404/405 como hasta ahora |

**Contrato semántico (lo que verifican los tests):**

```text
[RF-4] en TODAS las páginas con base.html: <form action="/buscar" method="get">
       con <input name="q"> y <button>Buscar</button>, FUERA del <nav>
                                                       → absent ⇒ FAIL
[RF-1] GET /buscar?q=psicología → «Resultados de búsqueda» + ≥1 resultado
       con <a href="/servicios»                      → absent ⇒ FAIL
[RF-3] GET /buscar?q= → 200 con «Escribe un término para buscar en el sitio.»
                                                       → absent ⇒ FAIL
[RF-2] GET /buscar?q=zzzzz → 200 con «No se encontraron resultados para «zzzzz».»
                                                       → absent ⇒ FAIL
[RF-5] GET /buscar?q=Psiconutricion (sin acento) → encuentra «Psiconutrición»
                                                       → absent ⇒ FAIL
[RNF-1] vista móvil 375 sin desbordes; colores ⊆ paleta; Open Sans activa
                                                       → absent ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Ruta `GET /buscar` con resultados en servidor** | Testeable con el `test_client` existente, sin JS, funciona con teclado y lectores de pantalla (RNF accesibilidad implícito) y encaja con la constitución #3 (lógica en `services/`) | *Filtrado en vivo con JS*: requiere tests E2E que el proyecto aún no tiene; *endpoint JSON + SPA*: peso innecesario para 4 páginas | RF-1, RF-5 |
| D2 | **Formulario en `base.html`, bajo `</nav>` y fuera de `<nav>`** | Cobertura automática de todas las páginas; los tests de navegación (TC-001-006/013, TC-003-015) cuentan/aislan el `<nav>`, así que no se rompen | *Dentro del `<nav>`*: cambiaría el recuento de enlaces de los tests de HU-001/003; *solo en la portada*: RF-4 exige cabecera en todas las páginas | RF-4 |
| D3 | **Consulta vacía responde 200 con mensaje** | RF-3 explícita: la falta de término es un estado normal de usuario, no un error HTTP | *400 Bad Request*: rompe el patrón de la casa (las secciones sin implementar responden 200) | RF-3 |
| D4 | **Índice construido en memoria desde `content/`** | Sin duplicar literales: los textos son los mismos que ya validan los tests de HU-001/002/003; sin BD (constitución #5 fuera de alcance) | *Fichero JSON aparte*: literales duplicados que se desincronizan; *SQLite*: esquema sin requisito (AGENTS: nada por conveniencia) | RF-1 |
| D5 | **Un único mensaje de «sin resultados» con el término entrecomillado** | Literal único de la spec, testeable y claro para el visitante | *Mensajes por sección*: complejidad sin requisito | RF-2 |
| D6 | **Normalización con `unicodedata` (librería estándar)** | RF-5 sin dependencias nuevas (constitución #1); «psiconutricion» encuentra «Psiconutrición» | *Librería `unidecode`*: dependencia externa sin justificación; *búsqueda literal*: incumple RF-5 | RF-5, RNF-2 |
| D7 | **`.site-search`/`.search-*` mobile-first en `main.css`, con la paleta y tipografía vigentes** | Mismo criterio que `.about-*`/`.services-page-*` (D9/D10 de las specs 002/003); sin archivos CSS nuevos que fragmenten la hoja | *CSS nuevo por HU*: fragmenta la hoja (descartado en specs 002/003); *framework CSS*: dependencia sin aprobación | RNF-1 |
| D8 | **TC-001-008 acotado a formularios de reserva/administración** | El RF-4 enmendado de la Spec 001 admite explícitamente el formulario de la Spec 016; la aserción positiva `action="/buscar"` presente refuerza el test | *Dejar la aserción literal `"<form" not in html`*: impediría RF-4 y haría FAIL toda portada | RF-4 (001) |
| D9 | **La etiqueta `Buscar en el sitio` va en el marcado pero visualmente oculta** (`.site-search__label` con técnica *visually-hidden*) | Satisface el literal de contrato y la accesibilidad (lectores de pantalla) sin duplicar visualmente el placeholder en la cabecera, que ya muestra el mismo texto | *Etiqueta visible*: repite el placeholder y ensancha la cabecera, forzando el partido de la navegación en escritorio | RF-4, textos literales |
| D10 | **Cabecera responsive: entre 768–1199 px el formulario pasa a su propia fila, alineado a la derecha** (`flex-basis: 100%` + `max-width: 30rem`) | Evita que marca + menú + formulario compitan en una sola fila y partan el menú; en ≥1200 px todo cabe en una fila y en <768 px actúa el menú Hamburguesa | *Sin regla intermedia*: a 900–1100 px el formulario se comprime y los enlaces del menú se parten de forma desordenada | RNF-1 |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` (suite) · `python -m pytest tests/test_hu_016.py -v`
(HU). Fixtures en `conftest.py` (`app`, `client`) sin cambios.
`tests/expected_content.py` concentra los literales de la spec 016 (espejo único,
se actualiza junto con la spec — D12 del plan 001).

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-016-001 | `test_search_service.py` | `search("psicología")` → ≥1 resultado con título, snippet y URL `/servicios` | RF-1 |
| TC-016-002 | `test_search_service.py` | El índice incluye portada, Nosotros, Servicios y navegación (URLs esperadas) | RF-1 |
| TC-016-003 | `test_search_service.py` | `search("zzzzz")` → lista vacía | RF-2 |
| TC-016-004 | `test_search_service.py` | `search("")` y `search("   ")` → estado «vacío», sin resultados | RF-3, RF-5 |
| TC-016-005 | `test_search_routes.py` | `GET /buscar?q=…` → **200** con «Resultados de búsqueda» y enlaces `<a href>` | RF-1 |
| TC-016-006 | `test_search_routes.py` | `GET /buscar?q=psiconutricion` (sin acento) → encuentra «Psiconutrición» | RF-5 |
| TC-016-007 | `test_search_routes.py` | `GET /buscar?q=` → **200** con literal de consulta vacía; `q=zzzzz` → **200** con literal sin resultados | RF-2, RF-3 |
| TC-016-008 | `test_search_routes.py` | El formulario `action="/buscar"` está presente en `/`, `/nosotros`, `/servicios` y **fuera del `<nav>`**; `POST /buscar` → **405** | RF-4 |
| TC-016-009 | `test_hu_016.py` | `main.css`: `.site-search` con `@media (max-width…)`, colores ⊆ paleta, sin `<form>` dentro de `<nav>` | RNF-1, RNF-2 |
| TC-016-010 | `test_hu_016.py` | Regresión: `/`, `/nosotros`, `/servicios`, 404 y navegación siguen en verde con el formulario presente | finalización |
| TC-016-011 | `test_search_service.py` | Consulta muy larga/caracteres especiales → sin excepción, respuesta normalizada | casos límite |

### 6.2 Pirámide

1. **Unitarias** — `search_service` sin HTTP (índice, normalización, snippets). `[RF-1][RF-2][RF-5]`
2. **Integración HTTP** — `test_client` sobre `/buscar` y presencia del formulario. `[RF-1..RF-4]`
3. **Regresión** — `python -m pytest -q` completo (incluye HU-001/002/003 con sus tests enmendados). `[todos]`
4. **Visual/manual** — escritorio 1280 y móvil 375 de `/buscar` + recorrido de las 3 queries
   (con resultados, sin resultados, vacía) en navegador. `[RNF-1]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar (pytest-qa §1.2).
- Pruebas deterministas: sin fechas, sin estado compartido, sin orden accidental.

```text
HU: HU-016
Caso: TC-016-005
Comando: python -m pytest tests/test_search_routes.py -v
Resultado: PASS
Rama: feature/identidad-buscador
Commit: f53282d (tests); d0e2d4c (docs) y ed36013 (feat)
Evidencia visual: documentada en docs/evidencias/hu-016/qa-hu-016.md
(decisión de la usuaria de no regenerar PNG — Q6)
```

- Veredicto QA: `PASS` / `PARCIAL` / `FAIL` (skill `pytest-qa`, §20).

---

## 7. Decisiones registradas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | ¿Qué busca el buscador? | **Contenido actual**: portada, Nosotros, Servicios y menú (usuaria, 2026-10-08). Blog queda fuera (Spec 013). |
| Q2 | ¿JS o ruta del servidor? | **Ruta `GET /buscar`** con página de resultados (usuaria, 2026-10-08). |
| Q3 | ¿Dónde se coloca el formulario? | **Cabecera, debajo del menú y fuera del `<nav>`** (RF-4). |
| Q4 | ¿Literales? | Fijados en la Spec 016 (etiqueta, placeholder, botón, mensajes) — contrato. |
| Q5 | ¿Nueva rama? | No: rama única `feature/identidad-buscador` con toda la sesión (usuaria, 2026-10-08). |
| Q6 | ¿Evidencia visual? | **Solo documentar**; no se regeneran PNG de HU-001/002/003 (usuaria, 2026-10-08). |

---

## 8. Secuencia de implementación

0. **Git**: merge `feature/hu-003` → `main`, rama `feature/identidad-buscador` (hecho).
1. **Docs de diseño primero**: `docs/design-identity.md`, `docs/design-typography.md`.
2. **Spec 016** (literales) y este plan; enmiendas de Spec 001/002/003.
3. **Identidad** (Spec 001): `home_content.py`, `config.py`, `hero_image.py`,
   `base.html`, `home/index.html`, `main.css` (cabecera), `placeholder.svg`.
4. **Tipografía**: `@import` Open Sans + `font-family` en `main.css`.
5. **Buscador**: `services/search_service.py` → `web/search.py` →
   `templates/search/index.html` → formulario en `base.html` → CSS → registro en
   `create_app()`.
6. **Tests**: `expected_content.py` → enmiendas (`test_home_routes.py`) →
   `test_search_service.py` → `test_search_routes.py` → `test_hu_016.py`.
7. `python -m pytest -q` → demo manual (3 queries + móvil) → `MEMORY.md` → commits
   separados por fase → push.
