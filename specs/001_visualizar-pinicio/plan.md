# Plan 001 — Visualizar la página de inicio

> Trazabilidad: **HU-001 → Spec 001 (`specs/001_visualizar-pinicio/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs` (Q5).
> Etapa actual: **PLANEACIÓN**. No se ha escrito código.

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 001. **Fuera de alcance**: gestión de
citas, notificaciones, administración del blog.

**Sin modelo de datos SQLite**: esta spec no gestiona datos persistentes, así que **no
existe capa `persistence/` ni esquema** (nada por conveniencia; se crea junto con la
primera HU que use base de datos, donde se activa la constitución #5). El contenido de
la portada vive en módulos de contenido versionados en código (§2).

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Presentación clara del consultorio | §1 `home_content.py` + `home_service` + `home/index.html`; §2 `HOME_CONTENT`; §3 `get_home_view()`/`validate_content()`; §4 `GET /`; §5 D2/D3/D4; §6 TC-001-001/002/012/014 |
| RF-2 | Imagen representativa | §1 `resolve_hero_image` + `static/img/hero-contenidas.png`; §2 `HERO_IMAGE`; §3 `resolve_hero_image()`; §4 `GET /`; §5 D5/D14; §6 TC-001-003/004/009/019 |
| RF-3 | Accesos claros a las principales secciones | §1 `nav_links.py` + `web/placeholders.py` + `base.html`; §2 `NAV_LINKS`; §3 `build_navigation()`; §4 contrato de rutas; §5 D6/D11; §6 TC-001-005/006/016/017/018 |
| RF-4 | Portada orientada a presentación institucional y navegación inicial | §1 blueprint `home` sin mutaciones; §3 `validate_content()`; §4 `GET /` (405 en mutaciones); §5 D1/D2/D8; §6 TC-001-007/008/014 |
| RF-5 | Resumen de servicios (Psicología Integral + Psiconutrición) con acceso a Servicios | §1 `services_highlights.py`; §2 `SERVICES_HIGHLIGHT`; §3 `validate_services()`; §4 aserciones semánticas; §6 TC-001-010/015/020 |
| RF-6 | Frase institucional de valores | §1 `home_content.py` (`TRUST_LINE`); §2 `TRUST_LINE`; §3 `validate_content()`; §4 aserciones semánticas; §6 TC-001-011/021 |
| RF-7 | Marca secundaria «Contenidas» visible | §1 `home_content.py` (`SECONDARY_BRAND`); §2 `SECONDARY_BRAND`; §3 `validate_content()`; §4 aserción `<h1>` precedido de «Contenidas»; §6 TC-001-013/022 |
| RNF-1 | Legible en escritorio y móvil; sin desplazamiento por la imagen | §1 `base.html` + `main.css` mobile-first, `<img>` con `width/height`; §5 D10/D14; §6 TC-001-008/023 y validación visual |
| RNF-2 | Presentación institucional coherente | §1 `base.html` (paleta Serenidad Natural); §5 D10/D15; §6 TC-001-024 y evidencia visual |
| CL-1 | Imagen representativa no disponible | §3 `resolve_hero_image()`; §5 D5; §6 TC-001-009 |
| CL-2 | Contenido institucional incompleto | §2 `DEFAULT_*` (literales de la spec) + §3 `validate_content()`/`validate_services()`; §5 D4; §6 TC-001-012/014/020/021 |
| CL-3 | Acceso a una sección no disponible | §1 `web/placeholders.py`; §4 contrato de rutas; §5 D6; §6 TC-001-016/017 |

---

## 1. Estructura de módulos

`[RF-1..RF-7]` — Constitución #3: contenido, lógica y presentación separadas; la
plantilla no contiene reglas de negocio. **Estructura por capas (Q2).**

```text
Consultorio_Carolina/
├── app.py                        # python app.py → create_app() + run()          [RNF ops]
├── consultorio/
│   ├── __init__.py               # create_app(config=None) → Flask app
│   ├── config.py                 # rutas base, DEBUG, carpeta static              [RF-4]
│   ├── errors.py                 # handlers 404/405/500                           [CL-3]
│   ├── content/                  # CAPA DE DATOS (contenido estático versionado)
│   │   ├── __init__.py
│   │   ├── home_content.py       # SECONDARY_BRAND, HOME_CONTENT,
│   │   │                         # TRUST_LINE + sus DEFAULT_* (literales spec)    [RF-1][RF-6][RF-7]
│   │   ├── services_highlights.py# SERVICES_HIGHLIGHT + DEFAULT_*               [RF-5]
│   │   ├── hero_image.py         # HERO_IMAGE (path, alt) + DEFAULT_*           [RF-2]
│   │   └── nav_links.py          # NAV_LINKS (secciones y orden)                [RF-3]
│   ├── services/                 # CAPA DE LÓGICA
│   │   ├── __init__.py
│   │   └── home_service.py       # get_home_view(), validate_content(),
│   │                             # validate_services(), resolve_hero_image(),
│   │                             # build_navigation(), find_nav_item()           [RF-1..RF-7]
│   └── web/                      # CAPA DE PRESENTACIÓN (HTTP)
│       ├── __init__.py
│       ├── home.py               # blueprint "home": GET /                      [RF-1]
│       └── placeholders.py       # blueprint "sections": GET /nosotros, /servicios,
│                                 # /articulos, /contacto, /citas                 [RF-3][CL-3]
├── templates/
│   ├── base.html                 # <nav> desde view + footer + viewport          [RF-3][RNF-1]
│   ├── home/index.html           # hero (marca secundaria, nombre, lema, intro,
│   │                             # imagen), bloque servicios, frase de valores    [RF-1][RF-2][RF-5][RF-6][RF-7]
│   ├── sections/under_construction.html                                          [RF-3][CL-3]
│   └── errors/404.html, 405.html, 500.html
├── static/
│   ├── css/main.css              # mobile-first + paleta Serenidad Natural       [RNF-1][RNF-2]
│   ├── js/nav.js                 # menú hamburguesa (sin lógica de negocio)
│   └── img/
│       ├── hero-contenidas.png   # imagen representativa (asset suministrado)    [RF-2]
│       └── placeholder.svg       # sustituto cuando la imagen no existe         [CL-1]
└── tests/
    ├── conftest.py               # app factory con config de test + client HTTP  [§6]
    ├── expected_content.py       # espejo de los literales de la spec 001        [RF-1..RF-7]
    ├── test_home_content.py      # integridad de la capa de contenido            [RF-1][RF-3][RF-5]
    ├── test_home_service.py      # reglas de la portada                          [RF-1][RF-2][RF-4]
    ├── test_home_routes.py       # contrato HTTP / y secciones placeholder      [RF-1][RF-3][RF-7]
    └── test_hu_001.py            # criterios de finalización de la HU           [todos]
```

Responsabilidades (sin solaparse):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/*` | Declarar literales institucionales y valores por defecto | Contener lógica ni generar HTML |
| `services/home_service.py` | Validar completitud, resolver imagen, construir navegación | Escribir HTML, manejar request/response |
| `web/*` | Método/ruta, status code, `render_template` | Consultar contenido directamente ni decidir fallbacks |
| `templates/` | Marcar semántico + estilos | Condicionales de negocio |

**No se crea `persistence/` en HU-001**: no hay datos persistentes que proteger.

---

## 2. Fuente de contenido de la portada

`[RF-1][RF-2][RF-5][RF-6][RF-7][CL-2]` — No es un modelo de datos: es contenido
institucional **estático versionado en el repositorio**, cuyos literales coinciden con
la spec 001 (Q8).

### 2.1 `consultorio/content/home_content.py`

```python
SECONDARY_BRAND = "Contenidas"

HOME_CONTENT = {
    "brand_name": "Consultorio Psicológico Carolina Gómez",
    "tagline": "Acompañamiento psicológico y nutricional con calidez profesional",
    "intro": "Un espacio de atención personalizada donde la salud mental y el "
             "bienestar alimentario se abordan con evidencia, escucha y respeto. "
             "Te acompañamos en cada etapa con un trato cercano, profesional y "
             "confidencial.",
    "services_title": "Nuestros servicios",
    "services_link_label": "Ver todos los servicios",
    "services_link_url": "/servicios",
}

TRUST_LINE = ("Acompañamos con profesionalismo, empatía y confidencialidad. "
              "Nuestro compromiso es tu bienestar en un espacio seguro y sin juicios.")

DEFAULT_SECONDARY_BRAND = SECONDARY_BRAND
DEFAULT_HOME_CONTENT = {**HOME_CONTENT}      # literales de respaldo (spec 001)
DEFAULT_TRUST_LINE = TRUST_LINE
```

### 2.2 `consultorio/content/services_highlights.py`

```python
SERVICES_HIGHLIGHT = [
    {"name": "Psicología Integral",
     "summary": "Acompañamiento terapéutico para personas, parejas y familias, "
                "con un enfoque integral y basado en evidencia.",
     "url": "/servicios"},
    {"name": "Psiconutrición",
     "summary": "Integración de salud mental y alimentación para construir hábitos "
                "sostenibles y una relación saludable con la comida.",
     "url": "/servicios"},
]
DEFAULT_SERVICES_HIGHLIGHT = [*SERVICES_HIGHLIGHT]
```

### 2.3 `consultorio/content/hero_image.py`

```python
HERO_IMAGE = {
    "path": "img/hero-contenidas.png",
    "alt": "Retrato ilustrado con flores y una cinta rosa que dice «Contenidas»",
}
DEFAULT_HERO_IMAGE = {**HERO_IMAGE}
```

### 2.4 `consultorio/content/nav_links.py`

```python
NAV_LINKS = [
    {"label": "Inicio",       "url": "/"},
    {"label": "Nosotros",     "url": "/nosotros"},    # placeholder; HU-002
    {"label": "Servicios",    "url": "/servicios"},   # placeholder; HU-003
    {"label": "Blog",         "url": "/articulos"},   # placeholder; HU-013
    {"label": "Contacto",     "url": "/contacto"},    # placeholder; HU-015
    {"label": "Agendar cita", "url": "/citas"},       # placeholder; HU-004
]
```

**Reglas**: `label`/`url` no vacíos ni duplicados; toda `url` tiene ruta registrada
en `web/placeholders.py` → **la portada nunca enlaza a un 404** (Q1, CL-3).

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-7][CL-1][CL-2][CL-3]`

```text
# --- capa web -------------------------------------------------------------
FUNCTION handle_home(request):
    IF request.method != "GET": RETURN error_405()          # RF-4: sin mutaciones
    TRY:
        view = HomeService.get_home_view()
        RETURN render("home/index.html", view=view)         # HTTP 200
    CATCH ContentError:
        RETURN render("errors/500.html")                    # HTTP 500

FUNCTION handle_section_placeholder(request, slug):          # RF-3, CL-3
    IF request.method != "GET": RETURN error_405()
    item = HomeService.find_nav_item(slug)
    IF item IS NULL: RETURN error_404()
    RETURN render("sections/under_construction.html",
                  section=item.label,
                  nav=HomeService.get_home_view().nav)      # HTTP 200


# --- capa de servicio -----------------------------------------------------
FUNCTION HomeService.get_home_view():
    base   = validate_content()                             # RF-1, RF-6, RF-7, CL-2
    items  = validate_services(SERVICES_HIGHLIGHT)          # RF-5, CL-2
    hero   = resolve_hero_image(HERO_IMAGE)                 # RF-2, CL-1
    nav    = build_navigation(NAV_LINKS)                    # RF-3, CL-3
    RETURN HomeView(secondary_brand=base.secondary_brand,
                    brand_name=base.brand_name, tagline=base.tagline,
                    intro=base.intro, services_title=base.services_title,
                    services_link=base.services_link,
                    trust_line=base.trust_line,
                    services=items, hero=hero, nav=nav,
                    fallback_active=base.fallback_active OR items.fallback_active)

FUNCTION validate_content():                                 # RF-1, RF-6, RF-7
    merged = { "SECONDARY_BRAND": FIRST_NON_EMPTY(SECONDARY_BRAND, DEFAULT_...),
               "HOME_CONTENT":    MERGE(DEFAULT_HOME_CONTENT, HOME_CONTENT),
               "TRUST_LINE":      FIRST_NON_EMPTY(TRUST_LINE, DEFAULT_TRUST_LINE) }
    faltantes = claves con valor NULL o solo espacios
    IF faltantes NO está vacío: RETURN merged CON fallback_active = TRUE
    RETURN merged CON fallback_active = FALSE
    # Nunca se emite un literal vacío en la portada

FUNCTION validate_services(services):                        # RF-5
    validos = [ s FOR s IN services
                  IF s.name != "" AND s.summary != "" AND s.url != "" ]
    IF cuenta(validos) < 2:                                  # mínimo de la spec
        RETURN DEFAULT_SERVICES_HIGHLIGHT CON fallback_active = TRUE
    RETURN validos CON fallback_active = FALSE

FUNCTION resolve_hero_image(image):                          # RF-2, CL-1
    IF image.path IS NULL OR NOT static_file_exists(image.path):
        RETURN HeroImage(src="img/placeholder.svg", alt=image.alt, available=FALSE)
    RETURN HeroImage(src=image.path, alt=image.alt, available=TRUE)
    # alt procede siempre del literal de la spec (RF-2)

FUNCTION build_navigation(links):                            # RF-3
    items = [ {label, url} FOR l IN links
                ORDER por posición_declarada
                IF l.label != "" AND l.url != "" ]
    IF items VACÍO: RETURN Nav([ {label:"Inicio", url:"/"} ])
    RETURN Nav(items)
    # Toda url tiene ruta registrada → 0 enlaces rotos
```

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos de línea de comandos `[RNF-ops][RF-4]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor de desarrollo | `Serving Flask app 'app'` + `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla el arranque (puerto ocupado, error de plantilla) |
| `pytest -q` | Suite completa | `N passed in Xs` | `0` todo PASS; `1` FAIL/ERROR; `5` sin tests |
| `pytest tests/test_hu_001.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |
| `git status` · `git branch --show-current` | Trazabilidad | rama y cambios | `0` |

### 4.2 Contrato HTTP `[RF-1..RF-7]`

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `GET` | `/` | `text/html; charset=utf-8` con los literales de la spec | **200**; **200** con defaults si CL-2; **500** si el contenido es irrecuperable |
| `GET` | `/nosotros`, `/servicios`, `/articulos`, `/contacto`, `/citas` | `sections/under_construction.html`: título de sección, «Sección en construcción», retorno a `/`, mismo `<nav>` | **200** |
| `GET` | `/static/<ruta>` | CSS/JS/imágenes | **200** / **404** |
| `GET` | otra | `errors/404.html` | **404** |
| `POST/PUT/DELETE` | `/` o secciones | `errors/405.html` | **405** |

**Contrato semántico de `GET /` (lo que verifican los tests):**

```text
[RF-7] «Contenidas» visible, precediendo al <h1>            → absent ⇒ FAIL
[RF-1] <title> y <h1> = nombre del consultorio; <p> = intro → absent ⇒ FAIL
[RF-2] <img src resuelto alt="Retrato ilustrado…«Contenidas»"> → absent ⇒ FAIL
[RF-5] bloque con «Nuestros servicios», «Psicología Integral»,
       «Psiconutrición» y enlace «Ver todos los servicios» → /servicios  → absent ⇒ FAIL
[RF-6] frase de valores literal presente                    → absent ⇒ FAIL
[RF-3] <nav> con 6 <a href> visibles; cada href → 200       → <6 o 404 ⇒ FAIL
[RF-4] sin formularios de reserva, panel admin ni scripts
       de notificación; POST/PUT/DELETE → 405               → presente/2xx ⇒ FAIL
[RNF-1] <meta name="viewport">; <img> con width y height    → absent ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Paquete por capas** `consultorio/{content,services,web}` + `create_app()` **(Q2)** | Constitución #3 y #1. Fronteras claras que escalan a las 15 specs. | *`app.py` + módulos sueltos en raíz*: sin fronteras, la separación se erosiona al llegar citas y blog. | RF-4 |
| D2 | **Sin modelo de datos ni capa `persistence/` en HU-001** | La spec no escribe datos: no hay integridad que proteger ni consultas. Añadir SQLite obligaría a esquema/seed/migración sin requisito (AGENTS: nada por conveniencia). | *Tabla `home_content` + seed*: esquema y BD para un dato de solo lectura que cambia por revisión de código. | RF-1, RF-4 |
| D3 | **App factory en lugar de app global** | Cada test crea su app con config de prueba → aislamiento y determinismo (pytest-qa §6, §12). | *`app = Flask(__name__)` a nivel de módulo*: estado compartido; resultados dependen del orden. | RF-4, tests |
| D4 | **`DEFAULT_*` = literales de la spec + `validate_content()`/`validate_services()` en la capa de servicio (CL-2)** | Si falta contenido, el servicio completa desde los defaults y marca `fallback_active`; la plantilla recibe un `view` saneado (constitución #3). | *Condicionales Jinja `{% if not intro %}`*: regla duplicada en la presentación, no testeable unitariamente. *500*: caso límite convertido en caída. | RF-1, RF-4, CL-2 |
| D5 | **Imagen con verificación de existencia y fallback a `placeholder.svg`** | RF-2 exige mostrar imagen representativa y CL-1 contempla su indisponibilidad: degrada en vez de romper el layout. `alt` literal además cumple accesibilidad. | *Asumir que existe*: incumple RF-2 bajo CL-1. *500 si falta*: caída total. *Placeholder en CSS*: oculta el estado y no es testeable. | RF-2, CL-1 |
| D6 | **Navegación en `content/nav_links.py` + rutas placeholder creadas en HU-001 (Q1)** | RF-3 pide accesos claros y CL-3 contempla el enlace no disponible. Las rutas «en construcción» mantienen los 6 enlaces vivos (200) sin salir del alcance; cada HU posterior reemplaza el placeholder. | *Ocultar enlaces hasta su HU*: RF-3 débil, la portada no orienta. *Enlaces a 404*: navegación rota. *Stub con contenido ficticio*: inventaría datos de specs ajenas. | RF-3, CL-3 |
| D7 | **Contenido en `dict` con claves fijas** | Permite validar completitud de forma genérica y absorber literales nuevos añadiendo clave + default, sin tocar la lógica. | *Clases/ORM*: peso innecesario para contenido de solo lectura (constitución #1). | RF-1, CL-2 |
| D8 | **Degradación en `home_service`, no en la plantilla** | La regla vive en la capa de lógica; la plantilla solo recibe datos. | *Lógica Jinja*: ver D4. | RF-1, RF-4 |
| D9 | **Identificadores en inglés, mensajes y documentación en español** | Constitución #6: `home_service`, `nav_links` en inglés; literales y mensajes en español. | *Todo en español* / *todo en inglés*: ambos rompen la regla. | RF-1, RF-4 |
| D10 | **CSS mobile-first propio con la paleta Serenidad Natural (AGENTS.md)** | RNF-1 y RNF-2. `#789B8A` acciones/navegación, `#F7F3EA` fondo, `#30454B` texto, `#B8D8CE`/`#E8D5B5` apoyo, `#D99A7A` acento. Sin frameworks CSS (constitución #1). | *Bootstrap/Tailwind*: dependencia sin aprobación y rompe la restricción de paleta. *Sin media queries*: incumple RNF-1. | RNF-1, RNF-2 |
| D11 | **Dos blueprints: `home` y `sections`** | Contrato pequeño por HU; `create_app()` es el punto único de extensión para HU-002/003/004/013/015. | *Blueprint por sección desde ya*: módulos que otras HU reescribirán. | RF-3, RF-4 |
| D12 | **Spec 001 con textos literales exactos (Q8)** | La spec es la fuente de verdad del copy; trazabilidad directa spec → `expected_content.py` → HTML. | *Spec solo con campos*: el copy se decidiría en código, rompiendo SDD. **Consecuencia asumida**: cambiar un texto obliga a PR de spec primero y a refrescar los tests. | RF-1..RF-7 |
| D13 | **Sin botón CTA en el hero** | No aprobado como obligatorio en Q3; «Agendar cita» sigue siendo acceso claro vía menú (RF-3). | *Botón de acción destacado en el hero*: añade un elemento no requerido por la spec. | RF-3 |
| D14 | **Asset de imagen versionado en el repositorio (`static/img/hero-contenidas.png`)** | RF-2 deja de depender de terceros; el test TC-001-009 detecta su pérdida. `width`/`height` en el `<img>` evitan saltos de layout (RNF-1). | *URL externa/CDN*: dependencia de terceros, rompe disponibilidad de RF-2 y el modo offline. | RF-2, RNF-1 |
| D15 | **Los colores de la ilustración no alteran la paleta de UI** | El rosa/verde del recurso son contenido gráfico, no colores de interfaz. AGENTS.md prohíbe introducir colores de marca sin decisión de diseño documentada. | *Incorporar el rosa de la cinta como acento de la UI*: cambiaría la identidad sin decisión formal. | RNF-2 |

---

## 6. Estrategia de tests

Ejecución: `pytest -q` (suite) · `pytest tests/test_hu_001.py -v` (HU).
Fixtures en `conftest.py`: `app` con `TESTING=True` y config de prueba; `client` =
`app.test_client()`. Arrange/Act/Assert, sin dependencia del orden.
`tests/expected_content.py` concentra los literales de la spec 001 (espejo único, se
actualiza junto con la spec — D12).

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-001-001 | `test_home_service.py` | `get_home_view()` devuelve identidad completa y `fallback_active=False` | RF-1 |
| TC-001-002 | `test_home_routes.py` | `GET /` → **200**, `<h1>` = nombre del consultorio, `<p>` = intro | RF-1 |
| TC-001-003 | `test_home_service.py` | Archivo del hero existe → `available=True`, `src` = `img/hero-contenidas.png` | RF-2 |
| TC-001-004 | `test_home_routes.py` | `GET /` → `<img>` con `alt` = literal de la spec y `src` resuelto | RF-2 |
| TC-001-005 | `test_home_content.py` | `NAV_LINKS`: sin duplicados, sin `label`/`url` vacíos, orden estable, 6 items | RF-3 |
| TC-001-006 | `test_home_routes.py` | `GET /` → `<nav>` con 6 `<a href>` visibles | RF-3 |
| TC-001-007 | `test_home_routes.py` | `POST /` → **405**; sin efectos secundarios | RF-4 |
| TC-001-008 | `test_home_routes.py` | Respuesta sin formularios de reserva, panel admin ni scripts de notificación | RF-4 |
| TC-001-009 | `test_home_content.py` | **CL-1:** `static/img/hero-contenidas.png` existe y no está vacío | RF-2 |
| TC-001-010 | `test_home_content.py` | `SERVICES_HIGHLIGHT` ≥2 items con `name`, `summary`, `url` no vacíos | RF-5 |
| TC-001-011 | `test_home_content.py` | `TRUST_LINE` y `SECONDARY_BRAND` = literales de `expected_content.py` | RF-6, RF-7 |
| TC-001-012 | `test_home_service.py` | **CL-2:** `HOME_CONTENT` con claves vacías (monkeypatch) → `fallback_active=True` y view completo | RF-1, CL-2 |
| TC-001-013 | `test_home_routes.py` | `GET /` → «Contenidas» visible y precede al `<h1>` | RF-7 |
| TC-001-014 | `test_home_service.py` | **CL-2:** tras `validate_content()` ningún literal del view está vacío ni es `whitespace` | RF-1, RF-4, CL-2 |
| TC-001-015 | `test_home_routes.py` | Bloque de servicios completo y enlace «Ver todos los servicios» → `/servicios` responde **200** | RF-5 |
| TC-001-016 | `test_home_routes.py` | **CL-3:** cada sección sin implementar → **200** con «en construcción», nunca 404 | RF-3, CL-3 |
| TC-001-017 | `test_home_routes.py` | Cada ruta de `NAV_LINKS` → **200** + retorno a `/` + mismo `<nav>` | RF-3, CL-3 |
| TC-001-018 | `test_home_routes.py` | `GET /ruta-inexistente` → **404** con plantilla de error | RF-4 |
| TC-001-019 | `test_home_service.py` | **CL-1:** `HERO_IMAGE.path` inexistente (monkeypatch) → `available=False`, `src=placeholder.svg`, `alt` literal conservado | RF-2, CL-1 |
| TC-001-020 | `test_home_service.py` | **CL-2:** `SERVICES_HIGHLIGHT` con items incompletos → fallback al default (≥2 items válidos) | RF-5, CL-2 |
| TC-001-021 | `test_home_service.py` | **CL-2:** `TRUST_LINE` vacío → se completa con el literal default | RF-6, CL-2 |
| TC-001-022 | `test_home_service.py` | **CL-2:** `SECONDARY_BRAND` vacío → se completa con «Contenidas» | RF-7, CL-2 |
| TC-001-023 | `test_hu_001.py` | `<meta name="viewport">`, `main.css` con ≥1 `@media (max-width…)`, `<img>` con `width`/`height` | RNF-1 |
| TC-001-024 | `test_hu_001.py` | Colores declarados en `main.css` ⊆ paleta aprobada (sin colores nuevos) | RNF-2 |
| TC-001-025 | `test_hu_001.py` | **E2E:** desde `GET /`, seguir cada `<a href>` del nav → todos **200** | RF-3, criterios de finalización |

### 6.2 Pirámide

1. **Unitarias** — `content/` y `home_service` sin HTTP. `[RF-1][RF-2][RF-5][RF-6][RF-7]`
2. **Integración HTTP** — `test_client` sobre `/` y secciones. `[RF-1..RF-7]`
3. **Regresión** — `pytest -q` completo. `[todos]`
4. **Visual/manual** — capturas 1280×800 y 375×812 + recorrido de navegación en
   navegador (exigido por los criterios de finalización). `[RNF-1][RNF-2]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar (pytest-qa §1.2).
- Pruebas deterministas: sin fechas, sin estado compartido, sin orden accidental.

```text
HU: HU-001
Caso: TC-001-002
Comando: pytest tests/test_hu_001.py -v
Resultado: PASS
Rama: feature/hu-001
Commit: <hash>
Evidencia visual: docs/evidencias/hu-001/escritorio-1280.png, movil-375.png
```

- Veredicto QA: `PASS` / `PARCIAL` / `FAIL` (skill `pytest-qa`, §20).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Enlaces a secciones sin ruta | **Crear las rutas en HU-001** con mensaje «en construcción» (no fuera de alcance). Todas responden 200. |
| Q2 | Estructura de módulos | **Por capas**: `consultorio/{content,services,web}`. |
| Q3 | Contenido institucional | **Sí existe**: resumen de servicios + frase de valores + marca secundaria «Contenidas» (RF-5, RF-6, RF-7). |
| Q4 | Copy de la portada | No aplica: los literales se fijan en la spec (Q8). |
| Q5 | Ruta canónica de specs | **`/specs`**. No se modifica la constitución sin petición explícita. |
| Q6 | Git | `git init` + `.gitignore` + rama `feature/hu-001` = **paso 0**. Sin confirmación pendiente. |
| Q7 | Ruta/título de la sección de citas | No aplica; las rutas placeholder se fijan en §2.4 y las sustituye su HU. |
| Q8 | Contenido por defecto | **Promovido a la spec**: los `DEFAULT_*` son sus literales; la spec fija textos literales exactos (D12). |
| Q9 | Imagen representativa | Asset suministrado → `static/img/hero-contenidas.png`, alt literal en la spec (RF-2). |
| Q10 | «Contenidas» | **Marca secundaria visible** en la portada → RF-7 (D13: sin botón CTA en el hero). |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [ ] Escribir la spec 001 actualizada y este plan (aprobado).
- [ ] Guardar el asset suministrado en `static/img/hero-contenidas.png` y comprobar que
      el PNG lleva **fondo transparente** (si es blanco, se verá una caja sobre `#F7F3EA`
      → pedir versión transparente o recortarla).
- [ ] Evidencia QA (PASS/FAIL por TC), evidencia visual escritorio/móvil y demo manual.
- [ ] Actualizar `MEMORY.md` al cerrar.

---

## 8. Secuencia de implementación

0. **Git**: `git init`, `.gitignore` (`.venv/`, `__pycache__/`, `*.pyc`), commit inicial,
   rama `feature/hu-001`.
1. **Spec primero**: escribir `specs/001_visualizar-pinicio/spec.md` (versión aprobada).
2. **Plan**: escribir este `plan.md`.
3. Asset: `static/img/hero-contenidas.png` (verificar fondo transparente).
4. Esqueleto: `app.py`, `consultorio/__init__.py` (`create_app`), `config.py`, `errors.py`.
5. Capa de contenido: `home_content.py`, `services_highlights.py`, `hero_image.py`,
   `nav_links.py`.
6. Capa de servicio: `services/home_service.py`.
7. Capa web: `web/home.py`, `web/placeholders.py`.
8. Plantillas: `base.html`, `home/index.html`, `sections/under_construction.html`, `errors/`.
9. `static/css/main.css` (paleta + media queries), `static/js/nav.js`.
10. Tests: `conftest.py`, `expected_content.py` → `content` → `service` → `routes` →
    `test_hu_001.py`.
11. `pytest -q` → evidencia → demo manual (1280 y 375) → `MEMORY.md`.
