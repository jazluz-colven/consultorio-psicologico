# Plan 015 — Consultar información de contacto

> Trazabilidad: **HU-015 → Spec 015 (`specs/015_consultar-contacto/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs` (Q5).
> Etapa actual: **PLAN APROBADO** (2026-10-12): aprobado por la usuaria junto con los
> datos de contacto definitivos (**Q1**: dirección, WhatsApp y correo; **teléfono
> opcional, no disponible** — bloque omitido), la red social (**Q2**: solo Instagram)
> y los horarios (**Q3**: propuesta D13). Literales fijados en la spec 015
> (enmienda «Contenido de contacto», 2026-10-12).
> Rama: **`feature/hu-015`** desde `main` (Q4). Baseline de tests: **163 PASS / 0 FAIL**.

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 015: una **página única** `GET /contacto`
que concentra los datos de contacto (dirección, teléfono, WhatsApp, correo), los
horarios de atención y los enlaces a las redes sociales oficiales, cada dato en un
bloque propio y consultable.

**Fuera de alcance** (spec 015 + decisión D11): gestión de mensajes recibidos,
**formulario de contacto** (captura de mensajes → su gestión está fuera de alcance),
chat en línea, administración de redes sociales, envío de correos/WhatsApp desde la
página (specs 008/009), reservas desde contacto.

**Sin modelo de datos SQLite**: contenido estático versionado en el repositorio
(mismo criterio D2 del plan 001; la constitución #5 solo se activa con persistencia
requerida — aquí no la hay). No se crea ni se toca `consultorio/persistence/`.

**Sin dependencias nuevas** (constitución #1): solo Flask + Jinja + CSS propio.

**Dudas de la spec cerradas** (§7.1): Q1 y Q2 resueltas por la usuaria el 2026-10-12;
los literales están fijados en la spec 015 (sección «Contenido de contacto», enmienda
del mismo día). RF-3 es **condicional**: no haber teléfono fijo no lo incumple — el
bloque «Teléfono» simplemente no se muestra mientras el dato no exista (D16).

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Mostrar los datos de contacto disponibles | §1 `contact_content.py` + `contact_service` + `templates/contact/index.html`; §2 modelo; §3 `get_contact_view()`; §4 `GET /contacto`; §5 D1/D2/D3; §6 TC-015-004/009 |
| RF-2 | Mostrar la dirección cuando exista | §2 `ADDRESS_LINES`; §3 resolución por campo; §4 contrato semántico; §5 D3/D4; §6 TC-015-005/010 |
| RF-3 | Mostrar teléfono, WhatsApp y correo | §2 `PHONE`/`WHATSAPP`/`EMAIL`; §3 validación de formato; §4 bloques con `tel:`/`wa.me`/`mailto:`; §5 D3/D5; §6 TC-015-002/006/010 |
| RF-4 | Mostrar los horarios de atención | §2 `OFFICE_HOURS` + `DEFAULT_OFFICE_HOURS`; §3 fallback; §4 contrato semántico; §5 D3/D13; §6 TC-015-007/011 |
| RF-5 | Mostrar enlaces a redes sociales oficiales aprobadas | §2 `SOCIAL_LINKS`; §3 filtro de URLs; §4 `<a href="https://…" target="_blank" rel="noopener">`; §5 D3/D14; §6 TC-015-003/008/011 |
| RF-6 | Diferenciar los canales de contacto y sus datos | §1 bloques independientes en la plantilla; §4 «un `<section>` por canal»; §5 D4; §6 TC-015-012 + evidencia visual |
| RNF-1 | Legible en escritorio y móvil | §1 `contact/index.html` + `.contact-page-*` mobile-first en `main.css`; §5 D10; §6 TC-015-015 y evidencia |
| RNF-2 | Presentación clara y fácil de localizar | §1 estructura semántica (`<h2>` por canal, `<ul>` de horarios) + medida CSS; §5 D4/D10; §6 TC-015-012/015 |
| CL-1 | Dirección no aplicable | §3 omisión del bloque Dirección + `fallback_active`; §5 D3; §6 TC-015-005 |
| CL-2 | Algún canal de contacto no disponible | §3 omisión por campo (nunca bloque vacío); §5 D3; §6 TC-015-006 |
| CL-3 | Horarios no definidos | §3 `DEFAULT_OFFICE_HOURS`; §5 D3/D13; §6 TC-015-007 |
| CL-4 | Enlace a una red social no disponible | §3 descarte de URL no válida; §5 D3/D14; §6 TC-015-008 |
| Finalización | Tests en verde + demo manual | §6 pirámide y evidencia + §8 secuencia |

---

## 1. Estructura de módulos

`[RF-1..RF-6][CL-1..CL-4][RNF-1][RNF-2]` — Constitución #3: contenido, lógica y
presentación separadas; la plantilla no contiene reglas de negocio. Se conserva la
estructura por capas (D1/Q2 del plan 001) y el patrón de blueprint validado en
HU-002/003.

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   └── contact_content.py      # CONTACT_PAGE_TITLE, CONTACT_* y DEFAULT_*
│   │                             #   [RF-1..RF-6][CL-1..CL-4]
│   ├── services/
│   │   └── contact_service.py      # ContactView, get_contact_view(),
│   │                             #   validate_contact()             [RF-1..RF-6][CL-1..CL-4]
│   └── web/
│       ├── contact.py              # blueprint "contact": GET /contacto
│       │                         #   [RF-1..RF-6]
│       └── placeholders.py         # retira /contacto; conserva /articulos
│                                 #   [CL-*][regresión HU-001..008]
├── templates/
│   └── contact/index.html          # h1 «Contacto» + un <section> por canal
│                                 # (Dirección, Teléfono, WhatsApp, Correo,
│                                 # Horarios de atención, Redes sociales)
│                                 # + «Volver al inicio»
│                                 #   [RF-1..RF-6][RNF-1][RNF-2]
├── static/
│   └── css/main.css                # .contact-page-* mobile-first; paleta intacta
│                                 # [RNF-1][RNF-2]
└── tests/
    ├── expected_content.py         # + CONTACT_* (espejo único) y
    │                             # PLACEHOLDER_SECTIONS sin /contacto [RF-1..RF-6]
    ├── test_contact_content.py     # integridad y formatos del contenido
    │                             #   [RF-2][RF-3][RF-5][CL-1..CL-4]
    ├── test_contact_service.py     # resolución por campo y omisiones
    │                             #   [RF-1..RF-6][CL-1..CL-4]
    ├── test_contact_routes.py      # contrato HTTP + 405/404 + regresión
    │                             #   [RF-1..RF-6]
    └── test_hu_015.py              # RNF + E2E + fuera de alcance  [todos]
```

Responsabilidades (sin solaparse):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/contact_content.py` | Declarar los datos de contacto, horarios, redes y sus defaults + título de página | Contener lógica ni generar HTML |
| `services/contact_service.py` | Validar formato, aplicar fallback/omisión por campo y devolver un view saneado | Escribir HTML, manejar request/response |
| `web/contact.py` | Método/ruta, status code, `render_template` | Consultar contenido directamente ni decidir omisiones |
| `templates/contact/index.html` | Marco semántico: un `<section>` por canal con su `<h2>` | Condicionales de negocio |
| `placeholders.py` | Queda solo con `/articulos` | Ocultar la sección implementada |

`create_app()` registra `contact_bp` junto a `about_bp`, `home_bp`, `sections_bp`,
`services_bp` y `search_bp`. `base.html`, `nav.js` y `NAV_LINKS` no cambian: la
navegación ya incluye «Contacto» → `/contacto`.

---

## 2. Fuente de contenido de contacto

`[RF-1..RF-6][CL-1..CL-4]` — Contenido **estático versionado en el repositorio**
(mismo criterio D2/Q8 del plan 001). Identificadores en inglés, literales en español
(constitución #6).

> **Los valores concretos están pendientes de Q1 y Q2** (dudas abiertas de la spec 015):
> no se inventan datos de contacto ni redes sociales. Bajo ese supuesto, el modelo y
> las reglas quedan definidos aquí y los literales se fijan en la spec 015 **antes**
> de codificar (§8.1).

> **Texto aprobado (Q1/Q2/Q3, 2026-10-12)**: los literales de abajo están **fijados
> en la spec 015** (sección «Contenido de contacto») y son contrato; `tests/expected_content.py`
> es su espejo único (D6).

### `consultorio/content/contact_content.py`

```python
CONTACT_PAGE_TITLE: str = "Contacto"          # h1 literal (aprobado 2026-10-12)

# --- RF-2 -------------------------------------------------------------------
ADDRESS_LINES: list[str] = [                  # aprobado 2026-10-12
    "Calle 34 #29-18",
    "Mejoras Públicas",
    "Bucaramanga, Colombia",
]

# --- RF-3 -------------------------------------------------------------------
PHONE: str = ""                               # opcional, no disponible (D16)
WHATSAPP: str = "+573168756020"               # aprobado 2026-10-12 → wa.me/573168756020
EMAIL: str = "caritogomez26@gmail.com"        # aprobado 2026-10-12 → mailto:

# --- RF-4 (propuesta D13 aprobada el 2026-10-12) ----------------------------
OFFICE_HOURS: list[dict[str, str]] = [
    {"label": "Mañana", "days": "Lunes a viernes", "hours": "8:00 a. m. – 11:30 a. m."},
    {"label": "Tarde",  "days": "Lunes a viernes", "hours": "2:00 p. m. – 4:30 p. m."},
]

# --- RF-5 (aprobado 2026-10-12: solo Instagram) -----------------------------
SOCIAL_LINKS: list[dict[str, str]] = [
    {"platform": "instagram", "label": "Instagram",
     "url": "https://www.instagram.com/psi.carolinagomez/"},
]

# --- respaldos = copia literal de la spec (patrón de about/services) --------
DEFAULT_ADDRESS_LINES   = copy.deepcopy(ADDRESS_LINES)
DEFAULT_PHONE           = PHONE
DEFAULT_WHATSAPP        = WHATSAPP
DEFAULT_EMAIL           = EMAIL
DEFAULT_OFFICE_HOURS    = copy.deepcopy(OFFICE_HOURS)
DEFAULT_SOCIAL_LINKS    = copy.deepcopy(SOCIAL_LINKS)

# --- etiquetas de bloque (RF-6) --------------------------------------------
CONTACT_BLOCK_LABELS: dict[str, str] = {
    "address":  "Dirección",
    "phone":    "Teléfono",
    "whatsapp": "WhatsApp",
    "email":    "Correo electrónico",
    "hours":    "Horarios de atención",
    "social":   "Redes sociales",
}
DEFAULT_CONTACT_BLOCK_LABELS = copy.deepcopy(CONTACT_BLOCK_LABELS)
```

**Reglas de contenido** `[RF-1..RF-6][CL-*]`:

- Todo campo obligatorio está tras `.strip()`; vacío o solo espacios ⇒ **dato no
  disponible** (no se inventa contenido).
- `PHONE` y `WHATSAPP`: solo dígitos con `+` opcional al inicio (coherencia con la
  regla de la spec 004 — Q9). Formato inválido ⇒ tratado como no disponible.
- `EMAIL`: debe pasar una comprobación mínima `local@dominio.tld`.
- `SOCIAL_LINKS`: cada `url` debe empezar por `https://`; `platform`/`label` no
  vacíos y sin plataformas duplicadas. Una red **no aprobada o sin URL** no se
  muestra (RF-5 es condicional: «cuando existan»).
- Añadir un canal o una red futura exige actualizar primero la spec (spec primero).

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-6][CL-1..CL-4]`

```text
# --- capa de servicio -----------------------------------------------------
FUNCTION get_contact_view():
    channels, hours, socials, fallback = validate_contact()
    RETURN ContactView(title=CONTACT_PAGE_TITLE, channels=channels,
                       hours=hours, socials=socials,
                       titles=resolve_block_titles(), fallback_active=fallback)

FUNCTION _resolve(live, default):
    # patrón de about/services: valor vivo si no está vacío, si no el default
    IF live NON-EMPTY: RETURN live, FALSE
    RETURN default, (default NON-EMPTY)        # fallback solo si hay default

FUNCTION _clean_phone(v): RETURN v IF v MATCHES "^\+?[0-9]{7,}$" ELSE ""
FUNCTION _clean_email(v): RETURN v IF v MATCHES "^[^@\s]+@[^@\s]+\.[^@\s]+$" ELSE ""

FUNCTION validate_contact():
    fallback = FALSE
    channels = []

    # RF-2 / CL-1: dirección
    addr, used = _resolve(NON_EMPTY_LINES(ADDRESS_LINES),
                          NON_EMPTY_LINES(DEFAULT_ADDRESS_LINES))
    fallback |= used
    IF addr: channels.ADD({key:"address", lines:addr})
    ELSE: fallback = TRUE                              # sin default ⇒ omisión

    # RF-3 / CL-2: teléfono, WhatsApp, correo (uno por canal)
    FOR (key, live, default, clean, href_fmt) IN [
        ("phone",    PHONE,    DEFAULT_PHONE,    _clean_phone, "tel:+{v}"),
        ("whatsapp", WHATSAPP, DEFAULT_WHATSAPP, _clean_phone, "https://wa.me/{v}"),
        ("email",    EMAIL,    DEFAULT_EMAIL,    _clean_email, "mailto:{v}"),
    ]:
        val, used = _resolve(clean(live), clean(default))
        fallback |= used
        IF val: channels.ADD({key, value:val, href:href_fmt.format(v=val)})
    # PHONE = "" por diseño (D16): sin canal Teléfono y SIN fallback

    # RF-4 / CL-3: horarios (lista de entradas válidas: label+days+hours)
    hours = [h FOR h IN OFFICE_HOURS IF ALL_FIELDS_NON_EMPTY(h)]
    IF hours VACÍO:
        hours = [h FOR h IN DEFAULT_OFFICE_HOURS IF ALL_FIELDS_NON_EMPTY(h)]
        IF hours: fallback = TRUE                      # RF-4 es incondicional

    # RF-5 / CL-4: redes (filtro por entrada: https:// + etiquetas no vacías
    # + sin plataforma duplicada); la entrada descartada marca fallback
    socials, seen = [], {}
    FOR s IN SOCIAL_LINKS:
        IF s.url STARTS_WITH "https://" AND s.label/platform NON_EMPTY
           AND s.platform NOT IN seen:
            socials.ADD(s); seen.ADD(s.platform)
        ELSE: fallback = TRUE

    RETURN channels, hours, socials, fallback
    # Nunca se emite un bloque sin contenido (RF-6: bloques diferenciados).
    # fallback_active = TRUE ⇔ algún campo cayó en su default no vacío,
    # se descartó una entrada o un campo quedó sin default que lo respaldara.

# --- capa web -------------------------------------------------------------
FUNCTION handle_contact(request):
    IF request.method != "GET": RETURN error_405()          # solo lectura
    view    = get_home_view()                               # nav idéntica al resto
    contact = get_contact_view()                            # RF-1..RF-6, CL-1..CL-4
    RETURN render("contact/index.html", view=view, contact=contact)   # HTTP 200

# Página única SIN subrutas: GET /contacto/<recurso> → 404 → errors/404.html
```

**CL-1/CL-2/CL-4** se resuelven **omitiendo el bloque** cuando ni el valor vivo ni el
default aportan contenido (no se inventan datos); **CL-3** se resuelve con
`DEFAULT_OFFICE_HOURS` porque RF-4 es incondicional («mostrará los horarios») y el
respaldo está respaldado por la agenda de la spec 004 (Q3). `fallback_active=True`
queda registrado para los tests. El estado normal del sitio es
`fallback_active=False` con los literales de la spec.

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF-ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor de revisión | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `python -m pytest -q` | Suite completa (163 actuales + nuevos) | `N passed` | `0` / `1` |
| `python -m pytest tests/test_hu_015.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-1..RF-6]`

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `GET` | `/contacto` | `contact/index.html` con h1 «Contacto» y bloques de datos | **200**; **200** con omisiones si CL-1/CL-2/CL-4 |
| `POST/PUT/DELETE` | `/contacto` | `errors/405.html` | **405** |
| `GET` | `/contacto/<cualquier-recurso>` | `errors/404.html` | **404** (página única) |
| `GET` | `/articulos` | sigue en `sections/under_construction.html` | **200** (regresión HU-001) |
| `GET` | `/`, `/nosotros`, `/servicios`, `/buscar`, `/citas` | sin cambios | 200/303/404/405 como hasta ahora |

**Contrato semántico de `GET /contacto` (lo que verifican los tests):**

```text
[RF-1] <h1>Contacto</h1> y ≥1 bloque de datos dentro de <main>        → absent ⇒ FAIL
[RF-2] bloque «Dirección» con <p>/<li> no vacío                      → ausente ⇒ FAIL
[RF-3] bloques propios «WhatsApp» (a[href^="https://wa.me/"]) y «Correo
       electrónico» (a[href^="mailto:"]); «Teléfono» (a[href^="tel:"])
       solo si PHONE estuviera disponible (hoy no — D16)  → ausente ⇒ FAIL
[RF-4] bloque «Horarios de atención» con ≥1 horario (label + hours)  → ausente ⇒ FAIL
[RF-5] bloque «Redes sociales» con ≥1 <a href^="https://" target=
       "_blank" rel="noopener"                                      → ausente ⇒ FAIL
[RF-6] cada dato en su propio <section> con su <h2>; sin campos
       mezclados entre canales                                      → ausente/mixto ⇒ FAIL
[RNF-1] <meta viewport>, ≥1 @media (max-width…), paleta ⊆ 6 hex,
        párrafos justify + hyphens:none                              → absent ⇒ FAIL
[RNF-2] medida CSS (max-width ≈ 65ch), <ul> de horarios, orden
        Dirección → Canales → Horarios → Redes                      → absent ⇒ FAIL
[CL-1] dirección y default vacíos → sin bloque Dirección      → bloque vacío ⇒ FAIL
[CL-2] canal sin dato válido ni default → sin su bloque; ningún
       bloque vacío; «Teléfono» ausente por diseño (D16)     → vacío ⇒ FAIL
[CL-3] horarios vacíos → DEFAULT_OFFICE_HOURS (nunca bloque vacío)   → vacío ⇒ FAIL
[CL-4] red social sin URL https válida → sin su enlace               → enlace roto ⇒ FAIL
[alcance] <main> sin <form>/<input> y sin chat                       → presente ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Blueprint propio `contact`**; la ruta `/contacto` sale de `placeholders.py` | Frontera por HU (patrón D1 del plan 002 / D6 del plan 003); `placeholders.py` queda solo para secciones sin implementar | *Dejar la ruta en `placeholders.py`*: mezcla sección implementada con placeholders | RF-1..6 |
| D2 | **Contenido estático en `content/contact_content.py` versionado en git** | Misma arquitectura aceptada en HU-001/002/003; los datos de contacto cambian por revisión de código; no hay requisito de persistencia (constitución #5 no aplica) | *Tabla SQLite + seed*: esquema sin requisito (AGENTS: nada por conveniencia) | RF-1..6 |
| D3 | **`validate_contact()` con resolución por campo (vivo → default → omisión), patrón de about/services** | Cada campo se resuelve contra su `DEFAULT_*` (copia literal de la spec): valor vivo no vacío, si no default (marcando `fallback`), si no omisión del bloque. CL-1/CL-2/CL-4 degradan omitiendo (nunca bloques vacíos ni datos inventados); RF-4 exige horarios siempre ⇒ default | *HTTP 500 ante dato ausente*: convertir un caso límite en caída. *Bloque con «—»*: dato falso. *Inventar datos*: engaña al visitante | RF-2..5, CL-1..4 |
| D4 | **Un `<section>` con `<h2>` por canal: Dirección, Teléfono, WhatsApp, Correo, Horarios, Redes** | RF-6 pide canales «diferenciados»: bloques independientes verificables y localizables (RNF) | *Párrafo único con todo mezclado*: impide verificar RF por canal. *Acordeón/JS*: complejidad sin requisito (constitución #1) | RF-6, RNF-2 |
| D5 | **Cada canal es un enlace nativa**: `tel:+…`, `https://wa.me/…`, `mailto:…`; redes con `target="_blank" rel="noopener"` | Accesible y funcional en móvil (abre WhatsApp/teléfono), sin JS; Jinja escapa los valores (sin riesgo de inyección) | *Texto plano sin enlace*: fricciona el objetivo de la HU. *JS personalizado*: dependencia innecesaria | RF-3, RF-5, RNF-2 |
| D6 | **Copy y datos fijados en la spec 015 antes de codificar** (Q1/Q2/Q3) | La spec es la fuente de verdad del contenido; traza spec → `expected_content.py` → HTML (Q8/D12 del plan 001) | *Redactar los datos en el plan o en el código*: el requisito viviría fuera de la spec (rompe SDD) | RF-1..5 |
| D7 | **Ajuste mínimo de regresión: `PLACEHOLDER_SECTIONS` pierde `/contacto`** | Patrón D6/D11 del plan 003: la CL-3 de la spec 001 es genérica («aún no implementada»); los tests que iteran el espejo se ajustan solos | *Tocar la spec 001*: contradicción innecesaria. *Mantener `/contacto` en la lista*: test roto deliberadamente | regresión HU-001..008 |
| D8 | **Nav y base desde `get_home_view()`** | Misma navegación en todas las páginas; sin duplicar lógica de presentación (patrón D7/D8) | *Construir la nav propia*: doble mantenimiento | RF-1, regresión |
| D9 | **Identificadores en inglés, textos y mensajes en español** | Constitución #6 (`contact_content`, `CONTACT_PAGE_TITLE`, `address` en inglés; «Teléfono», «Horarios de atención» en español) | *Todo en español* / *todo en inglés*: ambos rompen la regla | RF-1..6 |
| D10 | **Extender `main.css` con `.contact-page-*` mobile-first**, reutilizando el patrón `.about-*`/`.services-page-*`, con la paleta Serenidad Natural y Open Sans (base 18 px, párrafos `justify` + `hyphens: none` — `docs/design-typography.md`) | RNF-1/RNF-2; sin archivos CSS nuevos que fragmenten la hoja | *CSS nuevo por HU*: fragmenta (descartado en specs 002/003). *Bootstrap/Tailwind*: dependencia sin aprobación. *Nuevos colores*: prohíbe AGENTS.md | RNF-1, RNF-2 |
| D11 | **Sin formulario de contacto ni chat** | La spec pone «gestión de mensajes recibidos» y «chat en línea» fuera de alcance; un formulario sin gestión sería un botón muerto (constitución #1) | *Form con `mailto:`*: obsoleto y sin gestión. *Form + endpoint*: crearía mensajes fuera de alcance | fuera de alcance |
| D12 | **«Volver al inicio» al pie de la página** | Coherencia con `/nosotros` y `/servicios` (D13 del plan 003) y E2E estable | *Sin enlace de retorno*: la sección queda como callejón sin salida | RF-1, finalización |
| D13 | **Horarios en bloques Mañana/Tarde (`label` + `days` + `hours`) coherentes con la agenda de la spec 004** (propuesta Q3) | Mismo vocabulario que la reserva (bloques Mañana/Tarde) y misma franja (08:00–11:30 / 14:00–16:30, lun–vie): una sola verdad operativa para el visitante | *Texto libre de una línea*: imposible de validar ni de reutilizar. *Horarios distintos a la agenda*: contradicción entre lo que se promete y lo que se puede reservar | RF-4, CL-3 |
| D14 | **Redes sociales como lista `SOCIAL_LINKS` con `platform`/`label`/`url`, solo `https://` y sin duplicados** | RF-5 es condicional y pendiente de Q2: la lista permite mostrar solo las aprobadas y omitir el bloque completo si no hay ninguna | *Redes fijas en la plantilla*: mostraría enlaces no aprobados. *Iconos con JS*: dependencia innecesaria | RF-5, CL-4 |
| D15 | **`fallback_active` en `ContactView`** | Hace observable la degradación (CL-1..CL-4) en tests unitarios sin inspeccionar HTML | *Ocultar la degradación*: los casos límite no serían verificables | CL-1..4 |
| D16 | **Sin bloque «Teléfono»**: `PHONE = ""` por diseño (Q1, usuaria 2026-10-12) | RF-3 es **condicional** («CUANDO el consultorio disponga de teléfono, WhatsApp y correo»): WhatsApp + correo bastan; el estado normal no es una degradación ⇒ **no** marca `fallback` | *Pedir un teléfono inventado*: dato falso. *Bloque «Teléfono» vacío*: incumple RF-6 (nunca bloques sin contenido) | RF-3, CL-2 |

---

## 6. Estrategia de tests

Ejecución: `python -m pytest -q` (suite) · `python -m pytest tests/test_hu_015.py -v`
(HU). Fixtures existentes en `conftest.py` (`app`, `client`) sin cambios.
`tests/expected_content.py` concentra los literales de la spec 015 (espejo único,
se actualiza junto con la spec — D6). Baseline previo: **163 PASS / 0 FAIL**.

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-015-001 | `test_contact_content.py` | El módulo define `CONTACT_PAGE_TITLE`, `ADDRESS_LINES`, `PHONE`, `WHATSAPP`, `EMAIL`, `OFFICE_HOURS` y `SOCIAL_LINKS`; el espejo de `expected_content.py` coincide con la spec | RF-1..RF-5 |
| TC-015-002 | `test_contact_content.py` | Formatos: teléfono/WhatsApp solo dígitos con `+` opcional, `EMAIL` válida, todas las `url` de redes empiezan por `https://` | RF-3, RF-5 |
| TC-015-003 | `test_contact_content.py` | `SOCIAL_LINKS` sin plataformas duplicadas y con `platform`/`label` no vacíos | RF-5, CL-4 |
| TC-015-004 | `test_contact_service.py` | `get_contact_view()` devuelve título, canales completos, horarios y redes con `fallback_active=False` | RF-1..RF-6 |
| TC-015-005 | `test_contact_service.py` | **CL-1:** `ADDRESS_LINES` vacío (monkeypatch) → default de la spec + `fallback_active=True`; `ADDRESS_LINES` y `DEFAULT_ADDRESS_LINES` vacíos → sin canal `address` | RF-2, CL-1 |
| TC-015-006 | `test_contact_service.py` | **CL-2:** `PHONE=""` por diseño → sin canal `Teléfono` y `fallback_active=False` (D16); `WHATSAPP`/`EMAIL` con formato inválido (monkeypatch) → default u omisión; ningún canal emitido sin `href` | RF-3, CL-2 |
| TC-015-007 | `test_contact_service.py` | **CL-3:** `OFFICE_HOURS` vacío → se aplican `DEFAULT_OFFICE_HOURS` (≥1 horario) y `fallback_active=True` | RF-4, CL-3 |
| TC-015-008 | `test_contact_service.py` | **CL-4:** red social con `url` no `https` o etiqueta vacía → omitida; el resto de enlaces se conservan | RF-5, CL-4 |
| TC-015-009 | `test_contact_routes.py` | `GET /contacto` → **200** con `<h1>Contacto</h1>` y ≥1 bloque dentro de `<main>` | RF-1 |
| TC-015-010 | `test_contact_routes.py` | **RF-2/RF-3:** presencia de «Dirección», enlace `https://wa.me/573168756020` y `mailto:caritogomez26@gmail.com`; **ausencia** del bloque «Teléfono» (D16) | RF-2, RF-3 |
| TC-015-011 | `test_contact_routes.py` | **RF-4/RF-5:** bloque «Horarios de atención» con ≥1 horario y «Redes sociales» con `<a>` `https://` + `target="_blank" rel="noopener"` | RF-4, RF-5 |
| TC-015-012 | `test_contact_routes.py` | **RF-6:** ≥4 `<section>` propias con `<h2>`; sin datos de un canal dentro del bloque de otro | RF-6, RNF-2 |
| TC-015-013 | `test_contact_routes.py` | `POST/PUT/DELETE /contacto` → **405**; `GET /contacto/<recurso>` → **404** con `errors/404.html` | fuera de alcance, página única |
| TC-015-014 | `test_contact_routes.py` | Regresión: `PLACEHOLDER_SECTIONS == ["/articulos"]`; `/articulos` sigue «Sección en construcción.»; nav de 6 hrefs → 200; el buscador de `base.html` sigue presente en `/contacto` | regresión HU-001..008/016 |
| TC-015-015 | `test_hu_015.py` | **RNF-1/RNF-2:** `<meta viewport>`, `main.css` con ≥1 `@media (max-width…)`, colores ⊆ paleta de 6 hex, medida `max-width` de la sección, párrafos `justify` + `hyphens: none` | RNF-1, RNF-2 |
| TC-015-016 | `test_hu_015.py` | **E2E + fuera de alcance:** desde `GET /` seguir «Contacto» → **200** y «Contacto» visible; «Volver al inicio» → `/`; `<main>` sin `<form>`/`<input>` (sin formulario ni chat) | RF-1, fuera de alcance, finalización |

### 6.2 Pirámide

1. **Unitarias** — `contact_content` y `contact_service` sin HTTP.
   `[RF-1..RF-6][CL-1..CL-4]`
2. **Integración HTTP** — `test_client` sobre `/contacto`, subrutas y regresión.
   `[RF-1..RF-6]`
3. **Regresión** — `python -m pytest -q` completo: los 163 tests de
   HU-001/002/003/016/004/005/006/007/008 deben seguir verdes con el ajuste D7.
   `[todos]`
4. **Visual/manual** — capturas 1280 y 375 + recorrido de navegación en navegador
   (exigido por los criterios de finalización). `[RNF-1][RNF-2][RF-6]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar (skill `pytest-qa`).
- Pruebas deterministas: sin fechas, sin estado compartido, sin orden accidental.

```text
HU: HU-015
Caso: TC-015-009
Comando: python -m pytest tests/test_contact_routes.py -v
Resultado: PASS
Rama: feature/hu-015
Commit: <hash>
Evidencia visual: docs/evidencias/hu-015/escritorio-1280.png, movil-375.png
```

- Informe QA: `docs/evidencias/hu-015/qa-hu-015.md` con PASS/FAIL por TC y checkbox
  de los criterios de aceptación; veredicto `PASS` / `PARCIAL` / `FAIL` (skill
  `pytest-qa`).
- Capturas exactas con DevTools Protocol (`Emulation.setDeviceMetricsOverride`), no
  con `--window-size` (AGENTS.md).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Datos de contacto definitivos y opcionales (duda de la spec) | **Aprobado 2026-10-12**: dirección «Calle 34 #29-18 / Mejoras Públicas / Bucaramanga, Colombia», WhatsApp `+573168756020`, correo `caritogomez26@gmail.com`; **el teléfono fijo es opcional y no disponible** (bloque omitido, D16). |
| Q2 | Redes sociales oficiales (duda de la spec) | **Aprobado 2026-10-12**: solo **Instagram** `psi.carolinagomez` → `https://www.instagram.com/psi.carolinagomez/`. |
| Q3 | Horarios de atención | **Propuesta D13 aprobada 2026-10-12**: Mañana 8:00 a. m.–11:30 a. m. y Tarde 2:00 p. m.–4:30 p. m., lunes a viernes. |
| Q4 | Rama de trabajo | **`feature/hu-015` desde `main`** (patrón de las HU anteriores). |
| Q5 | Persistencia | **Sin SQLite** en HU-015: contenido estático en `content/contact_content.py` (D2). |
| Q6 | ¿Formulario de contacto? | **No** (D11): la spec lo deja fuera de alcance («gestión de mensajes», «chat»). |
| Q7 | ¿Estructura de la página? | **Página única `/contacto`** sin subrutas (patrón de `/servicios`, D11 del plan 003). |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] **Q1 — datos de contacto definitivos y opcionales** (2026-10-12): dirección,
      WhatsApp y correo fijados; teléfono opcional no disponible (D16). Cerrada en la
      spec 015 (enmienda «Contenido de contacto»).
- [x] **Q2 — redes sociales oficiales aprobadas** (2026-10-12): solo Instagram.
      Cerrada en la spec 015.
- [x] **Q3 — horarios de atención** (2026-10-12): propuesta D13 aprobada. Cerrada en
      la spec 015.
- [x] Aprobación de este `plan.md` por la usuaria (2026-10-12, con Q1/Q2/Q3).
- [x] Fijar Q1/Q2/Q3 en la spec 015 (literales contractuales) y actualizar este plan
      con los valores reales.
- [ ] Crear `feature/hu-015` desde `main` (verificar antes `git status` y la
      relación con `origin/main` — incidente 2026-10-12 de MEMORY).
- [ ] Implementar módulos, plantilla y CSS (§1–§4).
- [ ] Tests (§6) y `python -m pytest -q` en verde (163 actuales + nuevos).
- [ ] Evidencia QA (`qa-hu-015.md`) y evidencia visual (1280/375) con demo sobre el
      servidor (`GET /contacto` → 200).
- [ ] Commit/Push trazable, actualización de `MEMORY.md` y aceptación de la HU.

---

## 8. Secuencia de implementación

0. **Git**: verificar `git status`/`git log main..origin/main`; crear
   `feature/hu-015` desde `main` (Q4).
1. **Spec primero (requiere petición explícita)**: enmienda de la spec 015 — cerrar
   Q1 y Q2 y añadir la sección «Contenido de contacto» con los literales aprobados
   (Q3 incluido). *Mientras sigan abiertas, no se codifica.*
2. **Plan**: este `plan.md` (aprobado por la usuaria).
3. **task.md**: desglose de tareas < 30 min con `Hecho cuando:` verificable.
4. Capa de contenido: `consultorio/content/contact_content.py`.
5. Tests de contenido: espejo en `expected_content.py` → `test_contact_content.py`.
6. Capa de servicio: `consultorio/services/contact_service.py` →
   `test_contact_service.py`.
7. Capa web: `consultorio/web/contact.py` + retirar `/contacto` de
   `placeholders.py` + registrar `contact_bp` en `create_app()` +
   `PLACEHOLDER_SECTIONS` sin `/contacto` (D7).
8. Plantilla: `templates/contact/index.html` (extiende `base.html`).
9. CSS: sección `.contact-page-*` en `static/css/main.css` (mobile-first, paleta
   intacta, párrafos justificados sin guiones).
10. Tests de ruta y HU: `test_contact_routes.py` → `test_hu_015.py` → ajuste de
    regresión en los tests que iteran `PLACEHOLDER_SECTIONS`.
11. `python -m pytest -q` → evidencia → demo manual (1280 y 375) → `MEMORY.md`
    → commits separados por fase → push.
