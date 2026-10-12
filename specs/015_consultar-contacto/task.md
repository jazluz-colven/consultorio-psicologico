# Tareas HU-015 — Consultar información de contacto

> Trazabilidad: HU-015 → Spec 015 → `plan.md` (propuesto 2026-10-12, pendiente de
> aprobación) → **este task.md** → código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su
> `Hecho cuando:` es verificable con un comando o una observación concreta. Sin
> marcar una tarea, no se empieza la siguiente. RF indicados por tarea (matriz
> completa en `plan.md` §0). Baseline previo: **163 PASS / 0 FAIL**.

## Tareas

- [x] **T1 — Aprobación del plan y datos Q1/Q2/Q3 (plan §7.1)** `[trazabilidad][RF-1..RF-5]`
  La usuaria aprueba el `plan.md` y aporta (2026-10-12): **Q1** dirección
  «Calle 34 #29-18 / Mejoras Públicas / Bucaramanga, Colombia», WhatsApp
  `+573168756020`, correo `caritogomez26@gmail.com` — **teléfono fijo opcional y no
  disponible** (bloque omitido, D16) —; **Q2** solo Instagram `psi.carolinagomez`;
  **Q3** horarios D13 (Mañana 8:00–11:30 a. m. / Tarde 2:00–4:30 p. m., lun–vie).
  Hecho cuando: las filas Q1/Q2/Q3 de `plan.md` §7.1/§7.2 están fechadas como
  resueltas.

- [x] **T2 — Spec 015: enmienda con los literales (plan §8.1)** `[RF-1..RF-5][CL-1..CL-4]`
  Petición explícita de la usuaria («Sí, enmendar»): sección «Contenido de contacto»
  con `CONTACT_PAGE_TITLE`, `ADDRESS_LINES`, `PHONE` (opcional, vacío), `WHATSAPP`,
  `EMAIL`, `OFFICE_HOURS` y `SOCIAL_LINKS`; dudas Q1/Q2 marcadas [RESUELTA].
  Hecho cuando: `specs/015_consultar-contacto/spec.md` contiene «Contenido de
  contacto», sus dudas constan [RESUELTA] y `python -m pytest -q` sigue en
  **163 PASS / 0 FAIL**.

- [ ] **T3 — Git: rama `feature/hu-015` desde `main` + commit de spec/plan/task (plan §8.0, Q4)** `[base][regresión]`
  Verificar `git status` y `git log main..origin/main` (incidente 2026-10-12 de
  MEMORY), crear la rama desde `main` y commitear `spec.md`, `plan.md` y `task.md`;
  confirmar el baseline antes de tocar código.
  Hecho cuando: `git branch --show-current` → `feature/hu-015`,
  `git merge-base --is-ancestor main feature/hu-015` → exit 0, `git status` limpio y
  `python -m pytest -q` → **163 PASS / 0 FAIL**.

- [ ] **T4 — Espejo: literales de contacto en `tests/expected_content.py` (plan §1, D6)** `[RF-1..RF-5]`
  Añadir `CONTACT_PAGE_TITLE`, `ADDRESS_LINES`, `PHONE`, `WHATSAPP`, `EMAIL`,
  `OFFICE_HOURS` y `SOCIAL_LINKS` (espejo único de la spec; sin lógica). **No se toca
  aún `PLACEHOLDER_SECTIONS`** (eso va en T9).
  Hecho cuando: `python -c "import tests.expected_content as e; assert e.CONTACT_PAGE_TITLE == 'Contacto' and hasattr(e, 'OFFICE_HOURS') and hasattr(e, 'SOCIAL_LINKS')"` → exit 0
  y `python -m pytest -q` sigue en **163 PASS / 0 FAIL**.

- [ ] **T5 — Contenido: `content/contact_content.py` (plan §2, D2/D9)** `[RF-1..RF-6][CL-1..CL-4]`
  Constantes de la spec con identificadores en inglés y literales en español; los
  valores = espejo de T4; sin lógica ni BD.
  Hecho cuando: `python -c "import tests.expected_content as e; from consultorio.content import contact_content as c; assert c.CONTACT_PAGE_TITLE == e.CONTACT_PAGE_TITLE and c.OFFICE_HOURS == e.OFFICE_HOURS and c.SOCIAL_LINKS == e.SOCIAL_LINKS"` → exit 0.

- [ ] **T6 — Tests de contenido `test_contact_content.py` (plan §6.1, TC-015-001..003)** `[RF-2][RF-3][RF-5][CL-4]`
  Integridad del módulo y su espejo; formatos (`tel`/`wa` solo dígitos con `+`
  opcional, `EMAIL` válida, URLs `https://`); `SOCIAL_LINKS` sin duplicados.
  Hecho cuando: `python -m pytest tests/test_contact_content.py -v` → todos PASS, 0 FAIL.

- [ ] **T7 — Servicio: `services/contact_service.py` (plan §3, D3/D15)** `[RF-1..RF-6][CL-1..CL-4]`
  `ContactView` (con `fallback_active`), `get_contact_view()` y `validate_contact()`:
  omisión por campo (dirección/canales/redes) y `DEFAULT_OFFICE_HOURS` para los
  horarios; ningún bloque emitido sin contenido.
  Hecho cuando: `python -c "from consultorio.services.contact_service import get_contact_view as g; v = g(); assert v.title == 'Contacto' and v.hours and v.fallback_active is False"` → exit 0
  y `python -m pytest -q` → **0 FAIL**.

- [ ] **T8 — Tests de servicio `test_contact_service.py` (plan §6.1, TC-015-004..008)** `[RF-1..RF-6][CL-1..CL-4]`
  View completo sin fallback; CL-1 dirección vacía → sin bloque + `fallback_active`;
  CL-2 canal vacío/inválido → omitido; CL-3 horarios vacíos → defaults; CL-4 red sin
  `https://` → omitida.
  Hecho cuando: `python -m pytest tests/test_contact_service.py -v` → todos PASS, 0 FAIL.

- [ ] **T9 — Capa web + plantilla + placeholders (plan §8.7-8, D1/D4/D5/D7/D8/D12)** `[RF-1..RF-6][regresión HU-001..008/016]`
  `web/contact.py` (blueprint GET `/contacto`), retiro de `/contacto` de
  `placeholders.py`, registro en `create_app()`, `PLACEHOLDER_SECTIONS = ["/articulos"]`
  (D7) y `templates/contact/index.html` (h1 «Contacto», un `<section>` con `<h2>` por
  canal presente — Dirección, WhatsApp, Correo, Horarios, Redes; **sin Teléfono**
  (D16) — enlaces `wa.me`/`mailto:` y redes con `target="_blank" rel="noopener"`,
  «Volver al inicio»; nav desde `get_home_view()`).
  Hecho cuando: `python -c "from consultorio import create_app; c = create_app().test_client(); r = c.get('/contacto'); assert r.status_code == 200 and 'Contacto</h1>' in r.get_data(as_text=True)"` → exit 0,
  `python -c "from consultorio import create_app; c = create_app().test_client(); assert c.get('/articulos').status_code == 200"` → exit 0
  y `python -m pytest -q` → **0 FAIL**.

- [ ] **T10 — CSS `.contact-page-*` en `main.css` (plan §8.9, D10)** `[RNF-1][RNF-2]`
  Sección mobile-first con medida `max-width` ≈ 65ch, párrafos
  `text-align: justify` + `hyphens: none`, paleta intacta (solo los 6 hex) y orden
  Dirección → Canales → Horarios → Redes.
  Hecho cuando: `python -m pytest tests/test_hu_001.py tests/test_hu_002.py tests/test_hu_016.py -q` → **0 FAIL** (las reglas de paleta y tipografía existentes siguen pasando).

- [ ] **T11 — Tests de ruta `test_contact_routes.py` (plan §6.1, TC-015-009..014)** `[RF-1..RF-6][regresión]`
  200 con h1 y bloques, `wa.me`/`mailto:` (sin bloque «Teléfono», D16), horarios y
  redes con `target/rel`, ≥4 `<section>` propias, POST → 405, `GET /contacto/<recurso>` → 404 con
  `errors/404.html`, `PLACEHOLDER_SECTIONS` sin `/contacto`, `/articulos` en
  construcción, nav de 6 hrefs y buscador presentes.
  Hecho cuando: `python -m pytest tests/test_contact_routes.py -v` → todos PASS, 0 FAIL.

- [ ] **T12 — Tests de HU `test_hu_015.py` (plan §6.1, TC-015-015..016)** `[RNF-1][RNF-2][RF-1][fuera de alcance]`
  RNF (viewport, `@media`, paleta ⊆ 6 hex, medida, `justify` + `hyphens: none`) y
  E2E portada → «Contacto» → `/contacto`, «Volver al inicio» → `/`, `<main>` sin
  `<form>`/`<input>` (sin formulario ni chat).
  Hecho cuando: `python -m pytest tests/test_hu_015.py -v` → todos PASS, 0 FAIL.

- [ ] **T13 — Suite completa y regresión (plan §6.2)** `[todos]`
  Ejecutar la suite completa sin relajar aserciones previas.
  Hecho cuando: `python -m pytest -q` → **0 FAIL** con los **163 previos** intactos
  más los **16 nuevos** (**179 en total**).

- [ ] **T14 — Evidencia QA y visual (plan §6.3)** `[RF-1..RF-6][RNF-1][finalización]`
  Servidor (`python app.py`), recorrido manual de la sección y capturas CDP con
  alturas exactas → `docs/evidencias/hu-015/escritorio-1280.png` y
  `movil-375.png`, informe `qa-hu-015.md` con PASS/FAIL por TC, checkbox de los
  criterios de aceptación y veredicto (skill `pytest-qa`).
  Hecho cuando: los 3 archivos existen, las capturas miden 1280 y 375 px de ancho
  con la altura de `scrollHeight`, `qa-hu-015.md` declara veredicto **PASS** y el
  servidor queda en marcha con la URL comunicada.

- [ ] **T15 — Commits por fase, Push y `MEMORY.md` (plan §8.11)** `[trazabilidad]`
  Commits por fase (spec+plan+task+espejo → contenido → servicio → web+plantilla+CSS →
  tests → evidencia+MEMORY) citando HU-015/Spec 015; nunca datos sensibles en repo o
  memoria.
  Hecho cuando: `git status` limpio, `git rev-parse HEAD` =
  `git rev-parse origin/feature/hu-015` y `MEMORY.md` registra HU-015 (página
  `/contacto`, bloques por canal, PLACEHOLDER_SECTIONS solo `/articulos`).

- [ ] **T16 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `qa-hu-015.md` está marcado con fecha y
  la §7.2 del plan queda íntegramente en `[x]`.
