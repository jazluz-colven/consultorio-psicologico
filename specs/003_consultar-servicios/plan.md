# Plan 003 — Consultar los servicios

> Trazabilidad: **HU-003 → Spec 003 (`specs/003_consultar-servicios/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs` (Q5).
> Etapa actual: **PLAN APROBADO** (2026-10-07): aprobado por la usuaria, incluidos los
> literales RF-3 (Q3). Pendiente fijar esos literales y cerrar la duda abierta en la
> spec 003 (§8.1) antes de codificar.
> Ramas: **`main` tras integrar `feature/hu-002`** (HU-002 aceptada) y **`feature/hu-003`**
> nacida de `main` (Q4).

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 003: presentar los servicios ofrecidos
(Psicología Integral y Psiconutrición) con descripción y beneficios, en una
**página única** `/servicios` (decisión Q2).

**Fuera de alcance**: reserva/agendamiento desde la descripción del servicio (spec 003),
administración de servicios por usuarios públicos, registro de pacientes, cancelación
de citas, blog y contacto.

**Sin modelo de datos SQLite**: contenido estático versionado en código (D2 del plan 001;
la constitución #5 se activa con la primera HU que use base de datos). No existe capa
`persistence/`.

**Dudas de la spec resueltas** (2026-10-07):
- **Q1 — servicios adicionales**: no hay; solo los 2 mínimos. La duda abierta se cierra
  en la spec 003 en el paso 1 de la secuencia (§8).
- **Q2 — estructura**: página única; no existen rutas de detalle por servicio.
- **Q3 — copy RF-3**: literales de §2 **aprobados por la usuaria el 2026-10-07**; se
  fijan como contrato en la spec 003 **antes** de codificar (Q8/D12 del plan 001).

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Mostrar los servicios ofrecidos | §1 `services_catalog.py` + `services_service` + `templates/services/index.html`; §2 `SERVICES_CATALOG`; §3 `get_services_view()`; §4 `GET /servicios`; §5 D1/D2; §6 TC-003-005/008/014 |
| RF-2 | Mínimo Psicología Integral y Psiconutrición | §2 claves aprobadas del catálogo; §5 D7; §6 TC-003-002/003/008/014 |
| RF-3 | Descripción clara y beneficios | §2 `description`/`benefits` (literales de la spec); §3 fallback por campo; §4 contrato semántico; §5 D3/D5; §6 TC-003-002/004/007/009 |
| RF-4 | Información diferenciada por servicio | §1 bloques independientes en la plantilla; §4 «un bloque por servicio»; §5 D4; §6 TC-003-009 + evidencia visual |
| RNF-1 | Claridad y legibilidad en escritorio y móvil | §1 `services/index.html` + `.services-*` mobile-first en `main.css`; §5 D10; §6 TC-003-013 y evidencia |
| CL-1 | No existen servicios publicados | §2 `DEFAULT_SERVICES_CATALOG`; §3 `validate_services()`; §5 D3; §6 TC-003-006 |
| CL-2 | Servicio sin descripción o beneficios | §3 fallback por campo (nunca bloque vacío) + medida CSS sin truncar; §5 D3/D4; §6 TC-003-007 |
| CL-3 | Consulta de un servicio no disponible | §3/§4: subrutas de `/servicios/…` → **404** con `errors/404.html`; §5 D11; §6 TC-003-010/011 |
| Finalización | Tests en verde + demo manual | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-4][CL-1..CL-3][RNF-1]` — Constitución #3: contenido, lógica y presentación
separadas; la plantilla no contiene reglas de negocio. Se conserva la estructura por
capas (D1/Q2 del plan 001) y el patrón de blueprint ya validado en HU-002.

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   └── services_catalog.py   # SERVICES_CATALOG {psychology_integral, nutrition}
│   │                             # + DEFAULT_SERVICES_CATALOG + SERVICES_PAGE_TITLE
│   │                             #   [RF-1..RF-4][CL-1][CL-2]
│   ├── services/
│   │   └── services_service.py   # get_services_view(), validate_services()
│   │                             #   [RF-1..RF-4][CL-1][CL-2]
│   └── web/
│       ├── services.py           # blueprint "services": GET /servicios
│       │                         #   [RF-1..RF-4]
│       └── placeholders.py       # retira /servicios; conserva /articulos, /contacto, /citas
│                                 #   [CL-3][regresión HU-001/002]
├── templates/
│   └── services/index.html       # h1 «Servicios» + 1 <section> por servicio
│                                 # (banner <img>, h2 nombre, <p> descripción,
│                                 # <ul> beneficios) + «Volver al inicio»
│                                 #   [RF-1..RF-4][RNF-1]
├── static/
│   └── css/main.css              # .services-page-* mobile-first; paleta intacta
│                                 # [RNF-1]
└── tests/
    ├── expected_content.py       # + SERVICES_CATALOG (espejo) + SERVICES_PAGE_TITLE
    │                             # + PLACEHOLDER_SECTIONS sin /servicios [RF-1..RF-4]
    ├── test_services_content.py  # integridad del catálogo  [RF-1..RF-4][RF-3]
    ├── test_services_service.py  # fallback por campo       [RF-3][CL-1][CL-2]
    ├── test_services_routes.py   # contrato HTTP + 404 + regresión
    │                             # [RF-1..RF-4][CL-3]
    └── test_hu_003.py            # RNF + E2E + fuera de alcance  [todos]
```

Responsabilidades (sin solaparse):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/services_catalog.py` | Declarar los 2 servicios con nombre, descripción y beneficios + defaults + título de página | Contener lógica ni generar HTML |
| `services/services_service.py` | Validar completitud y aplicar fallback por campo/lista | Escribir HTML, manejar request/response |
| `web/services.py` | Método/ruta, status code, `render_template` | Consultar contenido directamente ni decidir fallbacks |
| `templates/services/index.html` | Marco semántico: un bloque por servicio | Condicionales de negocio |

`create_app()` registra `services_bp` junto a `about_bp`, `home_bp` y `sections_bp`.
`base.html` y `nav.js` no cambian: la navegación se sirve desde `get_home_view()`.

---

## 2. Fuente de contenido de los servicios

`[RF-1..RF-4][CL-1][CL-2]` — Contenido **estático versionado en el repositorio** cuyos
literales deben coincidir con la spec 003 (mismo criterio D12/Q8 del plan 001).

> **Texto aprobado (Q3)**: los literales de `description` y `benefits` de abajo fueron
> **aprobados por la usuaria el 2026-10-07**. Se fijan en la spec 003 (sección «Contenido
> de servicios» + cierre de la duda abierta) **antes** de codificar (§8.1).

### `consultorio/content/services_catalog.py`

```python
SERVICES_PAGE_TITLE = "Servicios"          # h1 literal (aprobado 2026-10-07)

SERVICES_CATALOG: dict[str, dict[str, object]] = {
    "psychology_integral": {
        "name": "Psicología Integral",
        "description": (                   # aprobado 2026-10-07
            "Un proceso terapéutico para personas, parejas y familias que "
            "busca comprender lo que estás viviendo, aliviar el malestar y "
            "construir herramientas concretas para el día a día, con un "
            "enfoque basado en evidencia y un trato cercano, respetuoso y "
            "confidencial."
        ),
        "benefits": [                      # aprobado 2026-10-07
            "Comprensión más clara de tus emociones, relaciones y patrones de conducta.",
            "Herramientas prácticas para manejar el estrés y el malestar cotidiano.",
            "Acompañamiento personalizado: individual, de pareja o familiar.",
            "Un espacio seguro, sin juicios y confidencial para hablar abiertamente.",
        ],
        "image": "img/servicios/psicologia-integral.webp",      # Q6, 2026-10-08
        "image_alt": (                      # aprobado 2026-10-08
            "Sesión de acompañamiento terapéutico en el consultorio"
        ),
    },
    "nutrition": {
        "name": "Psiconutrición",
        "description": (                   # aprobado 2026-10-07
            "Un acompañamiento que integra la salud mental con la alimentación "
            "para construir hábitos sostenibles y una relación más tranquila y "
            "consciente con la comida, sin dietas restrictivas ni culpa, "
            "respetando tu historia, tu ritmo y tus metas."
        ),
        "benefits": [                      # aprobado 2026-10-07
            "Hábitos alimentarios sostenibles, sin restricciones impuestas.",
            "Una relación más saludable y consciente con la comida.",
            "Vinculación entre lo emocional y lo alimentario en un mismo proceso.",
            "Planes personalizados adaptados a tu realidad y tus objetivos.",
        ],
        "image": "img/servicios/psiconutricion.webp",           # Q6, 2026-10-08
        "image_alt": (                      # aprobado 2026-10-08
            "Sesión de acompañamiento nutricional con plan alimentario personalizado"
        ),
    },
}
DEFAULT_SERVICES_CATALOG = copy.deepcopy(SERVICES_CATALOG)  # respaldo = spec
```

**Reglas**: exactamente las 2 claves aprobadas (`psychology_integral`, `nutrition`);
ningún `name`/`description`/`image`/`image_alt` vacío o solo espacios; `benefits` con
≥1 ítem no vacío y sin duplicados; cada `image` existe como fichero estático bajo
`static/`; orden de presentación = orden del diccionario. Añadir un servicio futuro
exige actualizar primero la spec (spec primero).

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-4][CL-1][CL-2][CL-3]`

```text
# --- capa web -------------------------------------------------------------
FUNCTION handle_services(request):
    IF request.method != "GET": RETURN error_405()              # solo lectura
    view     = get_home_view()                                  # nav idéntica al resto
    services = get_services_view()                              # RF-1..RF-4, CL-1, CL-2
    RETURN render("services/index.html", view=view, services=services)   # HTTP 200

# La página única NO declara subrutas: cualquier GET /servicios/<recurso>
# no existe → manejador 404 → errors/404.html                    # CL-3

# --- capa de servicio -----------------------------------------------------
FUNCTION get_services_view():
    items, fallback = validate_services()
    RETURN ServicesView(title=SERVICES_PAGE_TITLE, items=items,
                        fallback_active=fallback)

FUNCTION validate_services():
    resolved = []
    fallback = FALSE
    FOR key IN DEFAULT_SERVICES_CATALOG:                 # solo claves aprobadas
        d = DEFAULT_SERVICES_CATALOG[key]
        s = SERVICES_CATALOG.get(key, {})
        name = FIRST_NON_EMPTY(s.get("name"),        d["name"])
        desc = FIRST_NON_EMPTY(s.get("description"), d["description"])
        bens = FIRST_NON_BEMPTY_LIST(s.get("benefits"), d["benefits"])
        img  = FIRST_NON_EMPTY(s.get("image"),       d["image"])
        alt  = FIRST_NON_EMPTY(s.get("image_alt"),   d["image_alt"])
        resolved.append({key, name, desc, bens, img, alt})
        fallback = fallback OR (any field used default)
    RETURN resolved, fallback
    # Nunca se emite un servicio sin descripción ni sin beneficios;
    # CL-1 (catálogo vacío) → se resuelve con los 2 defaults.
```

**CL-2 (servicio sin descripción o beneficios)**: sin truncado automático —la
información no se oculta—; la lectura clara se garantiza con estructura (bloque propio
por servicio con `<h2>`) y medida CSS (`max-width` ≈ 65ch, base tipográfica de 18 px,
párrafos `justify` + `hyphens: none` según la regla permanente de `AGENTS.md`).

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor de desarrollo | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `pytest -q` | Suite completa (45 actuales + nuevos) | `N passed in Xs` | `0` / `1` / `5` |
| `pytest tests/test_hu_003.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-1..RF-4][CL-3]`

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `GET` | `/servicios` | HTML con h1 «Servicios», 2 bloques (nombre + descripción + beneficios) y `<nav>` de 6 accesos | **200**; **200** con defaults si CL-1/CL-2 |
| `POST/PUT/DELETE` | `/servicios` | `errors/405.html` | **405** |
| `GET` | `/servicios/<cualquier-recurso>` | `errors/404.html` | **404** (CL-3) |
| `GET` | `/articulos`, `/contacto`, `/citas` | siguen en `sections/under_construction.html` | **200** (regresión HU-001) |
| `GET` | `/`, `/nosotros` y resto | sin cambios | 200 / 404 |

**Contrato semántico de `GET /servicios` (lo que verifican los tests):**

```text
[RF-1] <h1>Servicios</h1> y ≥2 bloques con nombre dentro de <main>  → absent ⇒ FAIL
[RF-2] «Psicología Integral» y «Psiconutrición» presentes          → absent ⇒ FAIL
[RF-3] por cada servicio: <p> de descripción no vacío + <ul> con
       ≥1 <li> de beneficio                                        → absent ⇒ FAIL
[RF-4] cada servicio en su propio <section> con su <h2>; sin campos
       mezclados entre servicios                                   → ausente/mixto ⇒ FAIL
[imágenes] por cada servicio: <img> con src = fichero estático
       existente y alt no vacío (banner superior del bloque)       → ausente/roto ⇒ FAIL
[RNF-1] <meta viewport>, ≥1 @media (max-width…), paleta ⊆ 6 hex,
       medida CSS de la sección, párrafos justify + hyphens:none    → absent ⇒ FAIL
[CL-1] catálogo vacío → 2 servicios completos con defaults         → vacío ⇒ FAIL
[CL-2] descripción/beneficios vacíos → defaults por campo; ningún
       servicio emitido sin descripción ni beneficios              → bloque incompleto ⇒ FAIL
[CL-3] GET /servicios/<recurso> → 404 errors/404.html; POST → 405  → 2xx/5xx ⇒ FAIL
[alcance] <main> sin <form>/<input> y sin enlace a /citas (sin CTA
       de agendamiento; la nav conserva «Agendar cita»)            → presente ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Blueprint propio `services`**; la ruta `/servicios` sale de `placeholders.py` | Frontera por HU (patrón D1 del plan 002 / D11 del plan 001); `placeholders.py` queda solo para secciones no implementadas | *Dejar la ruta en `placeholders.py`*: mezcla sección implementada con placeholders y obliga a condicionar el módulo genérico | RF-1..4 |
| D2 | **Contenido estático en `content/services_catalog.py` versionado en git** | Misma arquitectura aceptada en HU-001/002; el contenido cambia por revisión de código | *Tabla SQLite + seed*: esquema sin requisito de persistencia (AGENTS: nada por conveniencia). *CMS*: fuera de alcance explícito | RF-1..4 |
| D3 | **`validate_services()` con fallback por campo y por lista** | CL-1 y CL-2 exigen degradar ante contenido faltante sin emitir bloques vacíos; la plantilla recibe un view saneado (constitución #3) | *Condicionales Jinja*: regla en la interfaz, no testeable unitariamente. *HTTP 500*: convertir un caso límite en caída total | RF-3, CL-1, CL-2 |
| D4 | **Página única con un `<section>` por servicio: `<h2>` + descripción + `<ul>` de beneficios; sin truncar** (Q2) | RF-4 pide información «diferenciada»: bloques independientes verificables; RF-3 (plural «beneficios») se materializa como lista | *Párrafo único mixto*: impide verificar RF por servicio. *Truncado con «…»*: oculta información (RF-3). *Acordeón/JS*: complejidad sin requisito (constitución #1) | RF-3, RF-4, CL-2, RNF-1 |
| D5 | **Copy literal fijado en la spec 003 antes de codificar** (Q8/D12; Q1/Q3) | La spec es la fuente de verdad del copy; traza spec → `expected_content.py` → HTML; cierra la duda abierta | *Redactar el copy en el plan o en código*: el requisito viviría fuera de la spec (rompe SDD) | RF-2, RF-3 |
| D6 | **Ajuste mínimo de regresión: `PLACEHOLDER_SECTIONS` pierde `/servicios`** | Patrón D11 del plan 002: la CL-3 de la spec 001 es genérica («aún no implementada»), no requiere cambiar la spec 001; los tests que iteran el espejo se ajustan solos | *Tocar la spec 001*: contradicción innecesaria. *Mantener `/servicios` en la lista*: test roto deliberadamente | regresión HU-001/002 |
| D7 | **Catálogo nuevo separado de `services_highlights.py`** | La portada de HU-001 está aceptada: `SERVICES_HIGHLIGHT` (name/summary/url) no se toca; el catálogo (name/description/benefits) responde a RF-3 con campos propios y mantiene RF-2 (los mismos 2 servicios) | *Ampliar `SERVICES_HIGHLIGHT` con description/benefits*: cambia un módulo aceptado y obliga a retrabajos en su test. *Duplicar literales de name*: se evita contrastando ambos en test de coherencia | RF-1, RF-2, regresión |
| D8 | **Nav y base desde `get_home_view()`** | Misma navegación en todas las páginas; sin duplicar lógica de presentación (patrón D7 del plan 002) | *Construir la nav propia*: doble mantenimiento y divergencia entre páginas | RF-1, regresión |
| D9 | **Identificadores en inglés, textos y mensajes en español** | Constitución #6 (`services_catalog`, `SERVICES_CATALOG`, `psychology_integral` en inglés; literales en español) | *Todo en español* / *todo en inglés*: ambos rompen la regla | RF-1..4 |
| D10 | **Extender `main.css` con `.services-page-*` mobile-first**, reutilizando el estilo de tarjeta de la portada, paleta y tipografía vigentes (Palatino, base 18 px, párrafos justify + `hyphens: none`) | RNF-1; sin dependencias externas (constitución #1); la justificación es regla permanente ya documentada en `AGENTS.md` y `docs/design-typography.md` | *Archivo CSS nuevo*: fragmenta la hoja. *Bootstrap/Tailwind*: dependencia sin aprobación. *Nuevos colores*: prohíbe AGENTS.md | RNF-1 |
| D11 | **CL-3 materializada como 404 de subrutas de `/servicios/…`** | Con página única (Q2) no existen rutas por servicio: cualquier recurso consultado bajo `/servicios/` responde 404 con la plantilla de errores ya registrada | *Fichas de detalle `/servicios/<slug>`*: descartada en Q2 (añadía ruta, plantilla y navegación sin un RF que los exija; la constitución #1 prioriza lo mínimo) | CL-3 |
| D12 | **Sin CTA de agendamiento en la sección de servicios** | Fuera de alcance explícito de la spec («reserva desde la descripción»); el acceso a citas ya existe en la nav | *Botón «Agendar cita» por servicio*: introduce conversión/comercio no pedido y tocaría el contrato semántico de la portada | fuera de alcance |
| D13 | **«Volver al inicio» al pie de la página** | Coherencia con `/nosotros` (D10 del plan 002) y E2E estable (TC-003-014) | *Sin enlace de retorno*: la sección queda como callejón sin salida | RF-1, finalización |
| D14 | **Banner de imagen por servicio: `<img>` al inicio de cada `<section>`, proporción fija (`aspect-ratio: 2/1`) con `object-fit: cover` y `border-radius`; rutas y `alt` literales en el catálogo (Q6)** | Ampliación pedida por la usuaria (2026-10-08) que enriquece RF-1 sin tocar RF-3/RF-4; el `alt` es contrato de accesibilidad y la ruta vive en el catálogo (espejo en `expected_content.py`); el PNG original (1 MB) se convierte a WebP (~55 KB) para no penalizar carga (RNF-1) | *Fondo CSS con `background-image`*: pierde `alt` y accesibilidad. *Dejar el PNG de 1 MB*: 20× más pesado que su versión WebP. *Imagen libre en la plantilla*: rompe el espejo spec → catálogo → test | RF-1, RNF-1 |

---

## 6. Estrategia de tests

Ejecución: `pytest -q` (suite) · `pytest tests/test_hu_003.py -v` (HU).
Fixtures existentes en `conftest.py` (`app`, `client`). Arrange/Act/Assert, sin
dependencia del orden. `tests/expected_content.py` concentra los literales de las specs
(espejo único, se actualiza junto con la spec — D5).

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-003-001 | `test_services_content.py` | `SERVICES_CATALOG` tiene exactamente las claves aprobadas, sin campos vacíos (incluidos `image`/`image_alt`) ni beneficios duplicados | RF-1, RF-4 |
| TC-003-002 | `test_services_content.py` | `DEFAULT_SERVICES_CATALOG` = literales de la spec (descripción, beneficios, imagen y alt) y `SERVICES_PAGE_TITLE` = «Servicios» | RF-2, RF-3, CL-1 |
| TC-003-003 | `test_services_content.py` | **RF-2 (unit):** el catálogo contiene «Psicología Integral» y «Psiconutrición»; coherencia de nombres con `SERVICES_HIGHLIGHT` de la portada | RF-2, regresión |
| TC-003-004 | `test_services_content.py` | **RF-3 (unit):** cada servicio tiene `description` no vacía y ≥1 `benefits` no vacío | RF-3, CL-2 |
| TC-003-016 | `test_services_content.py` | Cada `image` del catálogo existe como fichero estático bajo `static/` y su `image_alt` no está vacío | RF-1, imágenes |
| TC-003-005 | `test_services_service.py` | `get_services_view()` devuelve los 2 servicios completos y `fallback_active=False` | RF-1..4 |
| TC-003-006 | `test_services_service.py` | **CL-1:** catálogo vacío (monkeypatch) → defaults aplicados, `fallback_active=True`, ningún servicio sin bloques | RF-1, CL-1 |
| TC-003-007 | `test_services_service.py` | **CL-2:** `description` o `benefits` vacíos (monkeypatch) → default por campo/lista; ningún servicio emitido incompleto | RF-3, CL-2 |
| TC-003-008 | `test_services_routes.py` | `GET /servicios` → **200** con `<h1>Servicios</h1>` y los 2 nombres dentro de `<main>` | RF-1, RF-2 |
| TC-003-009 | `test_services_routes.py` | `GET /servicios` → **200** con 2 `<section>` propios, cada uno con `<img>` (src + alt), descripción y `<ul>` de beneficios | RF-3, RF-4, imágenes |
| TC-003-010 | `test_services_routes.py` | `POST/PUT/DELETE /servicios` → **405** sin efectos secundarios | CL-3, fuera de alcance |
| TC-003-011 | `test_services_routes.py` | **CL-3:** `GET /servicios/<recurso desconocido>` → **404** con `errors/404.html` | CL-3 |
| TC-003-012 | `test_services_routes.py` | Regresión: `PLACEHOLDER_SECTIONS` sin `/servicios` y `/articulos`, `/contacto`, `/citas` siguen «Sección en construcción.»; `/`, `/nosotros` intactos; nav de 6 hrefs → 200 | regresión HU-001/002 |
| TC-003-013 | `test_hu_003.py` | **RNF-1:** `<meta viewport>`, `main.css` con ≥1 `@media (max-width…)`, colores ⊆ paleta de 6 hex, medida (`max-width`) para la sección, párrafos con `text-align: justify` + `hyphens: none` | RNF-1, CL-2 |
| TC-003-014 | `test_hu_003.py` | **E2E:** desde `GET /` seguir «Ver todos los servicios» → **200** y «Psicología Integral» visible; «Volver al inicio» → `/` | RF-1, RF-2, criterios de finalización |
| TC-003-015 | `test_hu_003.py` | **Fuera de alcance:** `<main>` de `/servicios` sin `<form>`/`<input>` y sin enlace a `/citas` (sin CTA de reserva) | fuera de alcance |

### 6.2 Pirámide

1. **Unitarias** — `services_catalog` y `services_service` sin HTTP. `[RF-1..RF-4][CL-1][CL-2]`
2. **Integración HTTP** — `test_client` sobre `/servicios`, subrutas y secciones. `[RF-1..RF-4][CL-3]`
3. **Regresión** — `pytest -q` completo: los 45 tests de HU-001/HU-002 deben seguir
   verdes con el ajuste D6. `[todos]`
4. **Visual/manual** — capturas 1280 y 375 + recorrido de navegación en navegador
   (exigido por los criterios de finalización). `[RNF-1][RF-4][CL-2]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar.
- Pruebas deterministas: sin fechas, sin estado compartido, sin orden accidental.

```text
HU: HU-003
Caso: TC-003-008
Comando: pytest tests/test_hu_003.py -v
Resultado: PASS
Rama: feature/hu-003
Commit: <hash>
Evidencia visual: docs/evidencias/hu-003/escritorio-1280.png, movil-375.png
```

- Informe QA: `docs/evidencias/hu-003/qa-hu-003.md` con PASS/FAIL por TC y checkbox de
  aceptación; veredicto `PASS` / `PARCIAL` / `FAIL` (skill `pytest-qa`).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Servicios adicionales (duda abierta de la spec) | **Solo los 2 mínimos** (Psicología Integral y Psiconutrición), aprobado el 2026-10-07; la duda se cierra en la spec 003. |
| Q2 | Estructura de la sección | **Página única `/servicios`** (sin rutas de detalle; CL-3 = 404 de subrutas, D11). |
| Q3 | Copy de descripción y beneficios | **Propuestas del plan (§2) aprobadas por la usuaria el 2026-10-07** → se fijan en la spec 003 antes de codificar (mismo flujo que HU-002). |
| Q4 | Rama de trabajo | **Merge `feature/hu-002` → `main`** (HU-002 aceptada) y **`feature/hu-003` desde `main`**. |
| Q5 | Persistencia | Sin `persistence/` en HU-003 (contenido estático; D2). |
| Q6 | Imágenes por servicio | **Banner superior en cada bloque con proporción fija y esquinas redondeadas; PNG convertido a WebP** (decisión de la usuaria, 2026-10-08); rutas y `alt` como contrato en la spec 003 y en el catálogo (D14). |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Cerrar la duda abierta y fijar los literales RF-3 (descripción, beneficios y h1)
      en `specs/003_consultar-servicios/spec.md` — **bloquea la implementación** (Q3,
      textos ya aprobados).
- [x] Aprobación de este `plan.md` y de los literales RF-3 por la usuaria (2026-10-07).
- [x] Merge a `main` y creación de `feature/hu-003` (Q4).
- [x] Implementar módulos, plantilla y CSS (§1–§4).
- [x] Tests (§6) y `pytest -q` en verde (45 actuales + nuevos).
- [x] Evidencia QA (`qa-hu-003.md`, veredicto PASS) y evidencia visual
      (`escritorio-1280.png`, `movil-375.png`, verificadas) con demo sobre el servidor
      (`GET /servicios` → 200) — **regenerada tras la ampliación de imágenes (Q6)**.
- [x] Commit/Push de la evidencia y actualización de `MEMORY.md`.
- [ ] Aceptación de la HU (checkbox del informe QA).

---

## 8. Secuencia de implementación

0. **Git**: merge `feature/hu-002` → `main`; crear `feature/hu-003` desde `main` (Q4).
1. **Spec primero**: actualizar spec 003 — cerrar la duda abierta (Q1) y añadir la
   sección «Contenido de servicios» con los literales aprobados (Q3).
2. **Plan**: este `plan.md` (aprobado por la usuaria, 2026-10-07).
3. Capa de contenido: `consultorio/content/services_catalog.py`.
4. Capa de servicio: `consultorio/services/services_service.py`.
5. Capa web: `consultorio/web/services.py` + retirar `/servicios` de `placeholders.py` +
   registrar `services_bp` en `create_app()` + `PLACEHOLDER_SECTIONS` sin `/servicios`.
6. Plantilla: `templates/services/index.html` (extiende `base.html`).
7. CSS: sección `.services-page-*` en `static/css/main.css` (mobile-first, paleta
   intacta, párrafos justificados sin guiones).
8. Tests: espejo en `expected_content.py` → `test_services_content.py` →
   `test_services_service.py` → `test_services_routes.py` → `test_hu_003.py`.
9. `pytest -q` → evidencia → demo manual (1280 y 375) → `MEMORY.md`.
