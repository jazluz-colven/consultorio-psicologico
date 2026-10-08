# Plan 002 — Conocer el consultorio

> Trazabilidad: **HU-002 → Spec 002 (`specs/002_conocer-consultorio/spec.md`) → este plan → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (6 principios). Ruta canónica de las specs: `/specs` (Q5).
> Etapa actual: **EVIDENCIA CERRADA** (2026-10-07): `pytest -q` → **45 PASS / 0 FAIL**,
> `docs/evidencias/hu-002/` completa (`qa-hu-002.md` + 2 capturas). **PENDIENTE de
> aceptación de la HU.**
> Ramas: `main` y `feature/hu-002` creadas en `ba23658` (cabecera de HU-001 aceptada).

---

## 0. Alcance y cobertura

Implementa únicamente lo autorizado por Spec 002: misión, visión, experiencia
profesional y valores en `/nosotros`.

**Fuera de alcance**: registro de pacientes, agendamiento y cancelación de citas,
gestión administrativa del contenido.

**Sin modelo de datos SQLite**: el contenido institucional es estático y versionado en
código (mismo criterio D2 del plan 001; la constitución #5 se activa con la primera HU
que use base de datos). No existe capa `persistence/`.

**Duda de la spec resuelta** (2026-10-07): los literales definitivos de los 4 bloques
están aprobados en la sección «Contenido institucional» de la spec 002.

### Matriz de cobertura RF

| RF | Enunciado (resumen) | Dónde se cubre |
|----|---------------------|----------------|
| RF-1 | Mostrar la misión | §1 `about_content.py` + `about_service` + `templates/about/index.html`; §2 `ABOUT_CONTENT["mission"]`; §3 `get_about_view()`; §4 `GET /nosotros`; §5 D2/D3; §6 TC-002-001..005 |
| RF-2 | Mostrar la visión | §1 idem; §2 `ABOUT_CONTENT["vision"]`; §3 `get_about_view()`; §4 `GET /nosotros`; §5 D2/D3; §6 TC-002-001..005 |
| RF-3 | Mostrar la experiencia profesional | §1 idem; §2 `ABOUT_CONTENT["experience"]`; §3 `get_about_view()`; §4 `GET /nosotros`; §5 D2/D3; §6 TC-002-001..005 |
| RF-4 | Mostrar los valores | §1 idem; §2 `ABOUT_CONTENT["values"]`; §3 `get_about_view()`; §4 `GET /nosotros`; §5 D2/D3; §6 TC-002-001..005 |
| RF-5 | Información institucional diferenciada de servicios y citas | §1 `about_content.py` independiente + `web/about.py`; §4 aserciones de `<main>` sin servicios/formularios + `POST → 405`; §5 D6; §6 TC-002-006/007/008/009/013 |
| RNF-1 | Legible en escritorio y móvil | §1 `about/index.html` + `.about-*` en `main.css` (mobile-first); §5 D9; §6 TC-002-010/011 y evidencia visual |
| CL-1 | Falta algún contenido institucional | §2 `DEFAULT_ABOUT_CONTENT` (literales de la spec) + §3 `validate_about()`; §5 D3; §6 TC-002-002/004 |
| CL-2 | Contenido excesivamente extenso | §3 estructura de 4 bloques con `<h2>` + medida CSS (sin truncar); §5 D4; §6 TC-002-011 |

---

## 1. Estructura de módulos

`[RF-1..RF-5]` — Constitución #3: contenido, lógica y presentación separadas; la
plantilla no contiene reglas de negocio. Se conserva la estructura por capas (D1/Q2 del
plan 001).

```text
Consultorio_Carolina/
├── consultorio/
│   ├── content/
│   │   └── about_content.py      # ABOUT_CONTENT {mission, vision, experience, values}
│   │                             # + DEFAULT_ABOUT_CONTENT (literales de la spec)  [RF-1..RF-4][CL-1]
│   ├── services/
│   │   └── about_service.py      # get_about_view(), validate_about()             [RF-1..RF-4][CL-1]
│   └── web/
│       ├── about.py              # blueprint "about": GET /nosotros               [RF-1..RF-5]
│       └── placeholders.py       # retira /nosotros; conserva las otras 4 rutas   [RF-5]
├── templates/
│   └── about/index.html          # h1 «Nosotros» + 4 <section>/<h2> + «Volver al inicio»
│                                                                             [RF-1..RF-4][RNF-1]
├── static/
│   └── css/main.css              # sección .about-* mobile-first (sin cambios de paleta)
│                                                                             [RNF-1]
└── tests/
    ├── expected_content.py       # + ABOUT_CONTENT (espejo único)                 [RF-1..RF-4]
    ├── test_about_content.py     # integridad del contenido                       [RF-1..RF-4][RF-5]
    ├── test_about_service.py     # fallback por campo                             [RF-1..RF-4][CL-1]
    ├── test_about_routes.py      # contrato HTTP /nosotros y regresión            [RF-1..RF-5]
    └── test_hu_002.py            # RNF + CL-2 + criterios de finalización         [todos]
```

Responsabilidades (sin solaparse):

| Módulo | Responsabilidad | NO debe hacer |
|---|---|---|
| `content/about_content.py` | Declarar los 4 literales institucionales y sus defaults | Contener lógica ni generar HTML |
| `services/about_service.py` | Validar completitud y aplicar fallback por campo | Escribir HTML, manejar request/response |
| `web/about.py` | Método/ruta, status code, `render_template` | Consultar contenido directamente ni decidir fallbacks |
| `templates/about/index.html` | Marco semántico y estilos | Condicionales de negocio |

`create_app()` registra `about_bp` (punto único de extensión previsto en D11 del plan
001). `base.html` y `nav.js` no cambian: la navegación se sirve desde `get_home_view()`
misma que el resto de páginas.

---

## 2. Fuente de contenido institucional

`[RF-1..RF-4][CL-1]` — Contenido **estático versionado en el repositorio** cuyos
literales coinciden con la spec 002 (mismo criterio D12/Q8 del plan 001).

### `consultorio/content/about_content.py`

```python
ABOUT_CONTENT = {
    "mission": (
        "Acompañar a cada persona, pareja o familia en el cuidado de su salud mental "
        "y su bienestar alimentario, ofreciendo atención personalizada basada en "
        "evidencia, con un trato cercano, respetuoso y confidencial en un espacio "
        "seguro y sin juicios."
    ),
    "vision": (
        "Ser un espacio de confianza donde cada persona encuentre las herramientas "
        "para comprenderse, cuidarse y sostener cambios duraderos en su bienestar, "
        "reconocido por la calidez humana y la solidez profesional con la que "
        "acompaña a su comunidad."
    ),
    "experience": (
        "Soy profesional en el área de la Psicología, diplomada en primeros auxilios "
        "psicológicos, psiconutrición, y a través de esta formación me he dedicado a "
        "brindar acompañamiento y herramientas de apoyo emocional y espiritual."
    ),
    "values": (
        "Profesionalismo basado en evidencia. Escucha empática y sin juicios. "
        "Confidencialidad y respeto en cada proceso. Calidez humana y compromiso con "
        "el bienestar de cada persona."
    ),
}
DEFAULT_ABOUT_CONTENT = {**ABOUT_CONTENT}   # literales de respaldo = los de la spec

BLOCK_TITLES = {
    "mission": "Misión",
    "vision": "Visión",
    "experience": "Experiencia profesional",
    "values": "Valores",
}
DEFAULT_BLOCK_TITLES = {**BLOCK_TITLES}
```

**Reglas**: claves fijas (`mission`, `vision`, `experience`, `values`); ningún valor
vacío o solo espacios; los títulos de bloque son también literales de la spec.

---

## 3. Algoritmo en pseudocódigo

`[RF-1..RF-4][CL-1][RF-5]`

```text
# --- capa web -------------------------------------------------------------
FUNCTION handle_about(request):
    IF request.method != "GET": RETURN error_405()            # RF-5: solo lectura
    view  = get_home_view()                                    # nav idéntica al resto
    about = get_about_view()
    RETURN render("about/index.html", view=view, about=about)  # HTTP 200

# --- capa de servicio -----------------------------------------------------
FUNCTION get_about_view():
    content, fallback = validate_about()                      # RF-1..RF-4, CL-1
    RETURN AboutView(mission=…, vision=…, experience=…, values=…,
                     titles=…, fallback_active=fallback)

FUNCTION validate_about():
    resolved = {}
    fallback = FALSE
    FOR k IN DEFAULT_ABOUT_CONTENT:
        text, used = FIRST_NON_EMPTY(ABOUT_CONTENT.get(k), DEFAULT_ABOUT_CONTENT[k])
        resolved[k] = text
        fallback = fallback OR used
    titles = MERGE(DEFAULT_BLOCK_TITLES, BLOCK_TITLES saneado)
    RETURN resolved, titles, fallback
    # Nunca se emite un bloque vacío; los 4 campos siempre presentes
```

**CL-2 (contenido excesivamente extenso)**: sin truncado automático —la información no
se oculta—; la lectura clara se garantiza con estructura (4 bloques con `<h2>`
«Misión», «Visión», «Experiencia profesional», «Valores») y medida CSS (`max-width`
≈ 65ch, interlineado con la base tipográfica de 18 px).

---

## 4. Contrato (comandos, salidas, códigos de salida)

### 4.1 Comandos `[RNF ops]`

| Comando | Descripción | Salida esperada | Exit code |
|---|---|---|---|
| `python app.py` | Arranca el servidor de desarrollo | `Running on http://127.0.0.1:5000` | `0` con Ctrl+C; `1` si falla |
| `pytest -q` | Suite completa (29 de HU-001 + nuevos) | `N passed in Xs` | `0` / `1` / `5` |
| `pytest tests/test_hu_002.py -v` | Pruebas de la HU | listado PASS/FAIL | `0` / `1` |

### 4.2 Contrato HTTP `[RF-1..RF-5]`

| Método | Ruta | Salida (cuerpo) | Códigos |
|---|---|---|---|
| `GET` | `/nosotros` | HTML con los 4 literales, `<nav>` de 6 enlaces y «Volver al inicio» | **200**; **200** con defaults si CL-1 |
| `POST/PUT/DELETE` | `/nosotros` | `errors/405.html` | **405** |
| `GET` | `/servicios`, `/articulos`, `/contacto`, `/citas` | siguen en `sections/under_construction.html` | **200** (regresión HU-001) |
| `GET` | `/` y resto | sin cambios | 200 / 404 |

**Contrato semántico de `GET /nosotros` (lo que verifican los tests):**

```text
[RF-1..RF-4] 4 <section> con <h2> (Misión, Visión, Experiencia profesional,
        Valores) y los 4 literales dentro de <main>      → absent ⇒ FAIL
[RF-5] <main> sin «Psicología Integral», «Psiconutrición», «Ver todos
        los servicios» ni <form>; POST /nosotros → 405   → presente/2xx ⇒ FAIL
[RNF-1] <meta viewport>, ≥1 @media (max-width…), paleta ⊆ 6 hex  → absent ⇒ FAIL
[CL-2] 4 bloques con <h2> + regla de medida (max-width) en CSS    → absent ⇒ FAIL
```

---

## 5. Decisiones técnicas (justificación y alternativa descartada)

| # | Decisión | Justificación | Alternativa descartada | RF |
|---|---|---|---|---|
| D1 | **Blueprint propio `about`**; la ruta `/nosotros` sale de `placeholders.py` | Frontera por HU (D11 del plan 001); `placeholders.py` queda solo para secciones no implementadas | *Dejar la ruta en `placeholders.py`*: mezcla sección implementada con placeholders y obliga a condicionar un módulo genérico | RF-1..5 |
| D2 | **Contenido estático en `content/about_content.py` versionado en git** | Misma arquitectura aceptada en HU-001; el contenido cambia por revisión de código, no por usuario final | *Tabla SQLite + seed*: esquema/BD sin requisito de persistencia (AGENTS: nada por conveniencia). *CMS/administración*: fuera de alcance explícito de la spec | RF-1..4 |
| D3 | **`validate_about()` con fallback por campo a `DEFAULT_ABOUT_CONTENT`** | CL-1 exige degradar ante contenido faltante; la plantilla recibe un view saneado (constitución #3) | *Condicionales Jinja `{% if not mission %}`*: regla en la interfaz, no testeable unitariamente. *HTTP 500*: convertir un caso límite en caída total | RF-1..4, CL-1 |
| D4 | **4 bloques con `<h2>` + medida CSS; sin truncar** | CL-2 pide «lectura clara»: se mitiga con estructura y tipografía, no recortando información (RF-1..4 exigen el texto completo) | *Párrafo único*: no permite verificar RF por campo. *Truncado con «…»*: incumple RF al ocultar contenido. *Paginación*: complejidad sin requisito | RF-1..4, CL-2, RNF-1 |
| D5 | **Copy literal fijado en la spec 002 antes de codificar** (criterio Q8/D12) | La spec es la fuente de verdad del copy; traza spec → `expected_content.py` → HTML | *Redactar el copy en el plan o en código*: el requisito viviría fuera de la spec (rompe SDD). **Resuelto**: literales aprobados 2026-10-07 | RF-1..4 |
| D6 | **Módulo de contenido independiente + aserción de no-derivación en `<main>`** | RF-5 exige diferenciar la información institucional de servicios y citas | *Reutilizar `SERVICES_HIGHLIGHT` en la página*: acopla módulos y confunde lo institucional con lo comercial | RF-5 |
| D7 | **Nav y base desde `get_home_view()`** | Misma navegación en todas las páginas; sin duplicar lógica de presentación | *Construir la nav propio en about*: doble mantenimiento y riesgo de divergencia entre páginas | RF-5 |
| D8 | **Identificadores en inglés, textos y mensajes en español** | Constitución #6 (`about_service`, `ABOUT_CONTENT` en inglés; literales en español) | *Todo en español* / *todo en inglés*: ambos rompen la regla | RF-1..5 |
| D9 | **Extender `main.css` con `.about-*` mobile-first**, paleta y tipografía vigentes (Palatino, base 18 px) | RNF-1/RNF-2; sin dependencias externas (constitución #1); los cambios de color/tipo ya están documentados | *Archivo CSS nuevo*: fragmenta la hoja de estilos. *Bootstrap/Tailwind/fuente externa*: dependencia sin aprobación. *Nuevos colores*: prohíbe AGENTS.md sin decisión de diseño documentada | RNF-1 |
| D10 | **«Volver al inicio» en `/nosotros`** | Coherencia con el resto de secciones y deja intacta la aserción de regresión TC-001-017 de la HU-001 ya cerrada | *Quitar el enlace y ajustar TC-001-017*: tocar pruebas de una HU aceptada sin necesidad funcional | RF-5 |
| D11 | **Ajuste mínimo de regresión: `PLACEHOLDER_SECTIONS` pierde `/nosotros`** | D6 del plan 001 ya previó «cada HU posterior reemplaza el placeholder»; la CL-3 de la spec 001 es genérica («sección **aún no implementada**»), así que **no requiere cambiar la spec 001** | *Tocar la spec 001*: contradicción innecesaria, la cláusula ya es genérica. *Mantener `/nosotros` en la lista*: test roto deliberadamente | RF-5, regresión |

---

## 6. Estrategia de tests

Ejecución: `pytest -q` (suite) · `pytest tests/test_hu_002.py -v` (HU).
Fixtures existentes en `conftest.py` (`app`, `client`). Arrange/Act/Act/Assert, sin
dependencia del orden. `tests/expected_content.py` concentra los literales de las specs
(espejo único, se actualiza junto con la spec — D5).

### 6.1 Casos de prueba

| ID | Archivo | Objetivo y resultado esperado | RF |
|---|---|---|---|
| TC-002-001 | `test_about_content.py` | `ABOUT_CONTENT` tiene exactamente `mission/vision/experience/values`, sin valores vacíos, iguales al espejo | RF-1..4 |
| TC-002-002 | `test_about_content.py` | `DEFAULT_ABOUT_CONTENT` = literales de la spec; `BLOCK_TITLES` = títulos de la spec | RF-1..4, CL-1 |
| TC-002-003 | `test_about_service.py` | `get_about_view()` devuelve los 4 campos completos y `fallback_active=False` | RF-1..4 |
| TC-002-004 | `test_about_service.py` | **CL-1:** campo vacío (monkeypatch) → default aplicado, ningún bloque vacío ni whitespace, `fallback_active=True` | RF-1..4, CL-1 |
| TC-002-005 | `test_about_routes.py` | `GET /nosotros` → **200** con los 4 `<h2>` y los 4 literales dentro de `<main>` | RF-1..4 |
| TC-002-006 | `test_about_routes.py` | `POST /nosotros` → **405**; sin efectos secundarios | RF-5 |
| TC-002-007 | `test_about_routes.py` | **RF-5:** `<main>` sin «Psicología Integral», «Psiconutrición», «Ver todos los servicios»; sin `<form>`/`<input>` | RF-5 |
| TC-002-008 | `test_about_routes.py` | Regresión: `/servicios`, `/articulos`, `/contacto`, `/citas` siguen respondiendo «Sección en construcción.» y `/nosotros` ya no | RF-5, regresión HU-001 |
| TC-002-009 | `test_about_content.py` | **RF-5 (unit):** ningún literal de `ABOUT_CONTENT` contiene textos de servicios ni llamadas a agendar | RF-5 |
| TC-002-010 | `test_hu_002.py` | `<meta viewport>`, `main.css` con ≥1 `@media (max-width…)`, colores ⊆ paleta de 6 hex | RNF-1 |
| TC-002-011 | `test_hu_002.py` | **CL-2:** la respuesta contiene 4 bloques con `<h2>` y `main.css` declara medida (`max-width`) para `.about` | CL-2, RNF-1 |
| TC-002-012 | `test_hu_002.py` | **E2E:** desde `GET /` seguir el enlace «Nosotros» → **200** y misión visible; «Volver al inicio» → `/` | RF-1..5, criterios de finalización |
| TC-002-013 | `test_about_routes.py` | Nav en `/nosotros`: 6 `<a href>` visibles y cada href responde **200** | RF-5, regresión |

### 6.2 Pirámide

1. **Unitarias** — `about_content` y `about_service` sin HTTP. `[RF-1..RF-4][RF-5]`
2. **Integración HTTP** — `test_client` sobre `/nosotros` y secciones. `[RF-1..RF-5]`
3. **Regresión** — `pytest -q` completo: los 29 tests de HU-001 deben seguir verdes
   con el ajuste D11. `[todos]`
4. **Visual/manual** — capturas 1280×800 y 375×812 + recorrido de navegación en
   navegador (exigido por los criterios de finalización). `[RNF-1][CL-2]`

### 6.3 Ejecución y evidencia

- Prohibido eliminar/`skip`/relajar aserciones para pasar.
- Pruebas deterministas: sin fechas, sin estado compartido, sin orden accidental.

```text
HU: HU-002
Caso: TC-002-005
Comando: pytest tests/test_hu_002.py -v
Resultado: PASS
Rama: feature/hu-002
Commit: <hash>
Evidencia visual: docs/evidencias/hu-002/escritorio-1280.png, movil-375.png
```

- Informe QA: `docs/evidencias/hu-002/qa-hu-002.md` con PASS/FAIL por TC y checkbox de
  aceptación; veredicto `PASS` / `PARCIAL` / `FAIL` (skill `pytest-qa`).

---

## 7. Decisiones registradas y pendientes

### 7.1 Resueltas

| # | Pregunta | Decisión |
|---|---|---|
| Q1 | Contenido de misión/visión/experiencia/valores | **Aprobado por la usuaria el 2026-10-07** y fijado como literales en la spec 002 (duda abierta cerrada). |
| Q2 | Estructura del plan | **Aprobada por la usuaria el 2026-10-07** (módulos, decisiones con alternativa descartada, estrategia de tests). |
| Q3 | Rama de trabajo | **`main`** creada en `ba23658` (HU-001 aceptada) y **`feature/hu-002`** a partir de ella. |
| Q4 | Rol de «Experiencia profesional» | Literal en **primera persona** tal como lo dictó la usuaria (los otros 3 en tercera); decisión aceptada. |
| Q5 | Persistencia | Sin `persistence/` en HU-002 (contenido estático; D2). |

### 7.2 Pendientes (bloquean declarar COMPLETADO)

- [x] Implementar módulos, plantilla y CSS (§1–§4) — commit `f782797`.
- [x] Tests (§6) y `pytest -q` en verde: **45 PASS** (29 de HU-001 + 16 nuevos,
      incluye el bug de plantilla `titles["values"]` detectado por TC-002-005).
- [x] Evidencia QA (`qa-hu-002.md`, veredicto PASS) y evidencia visual
      (`escritorio-1280.png` 1280×1394 y `movil-375.png` 375×1903, verificadas) con
      demo sobre el servidor (`GET /nosotros` → 200).
- [x] Commit/Push de la evidencia y actualización de `MEMORY.md`.
- [ ] Aceptación de la HU (checkbox del informe QA).

---

## 8. Secuencia de implementación

0. **Git**: `main` + `feature/hu-002` (hecho, en `ba23658`).
1. **Spec primero**: spec 002 actualizada con literales (hecho).
2. **Plan**: este `plan.md` (aprobado).
3. Capa de contenido: `consultorio/content/about_content.py`.
4. Capa de servicio: `consultorio/services/about_service.py`.
5. Capa web: `consultorio/web/about.py` + retirar `/nosotros` de `placeholders.py` +
   registrar `about_bp` en `create_app()` + `PLACEHOLDER_SECTIONS` sin `/nosotros`.
6. Plantilla: `templates/about/index.html` (extiende `base.html`).
7. CSS: sección `.about-*` en `static/css/main.css` (mobile-first, paleta intacta).
8. Tests: espejo en `expected_content.py` → `test_about_content.py` →
   `test_about_service.py` → `test_about_routes.py` → `test_hu_002.py`.
9. `pytest -q` → evidencia → demo manual (1280 y 375) → `MEMORY.md`.
