# Tareas HU-003 — Consultar los servicios

> Trazabilidad: HU-003 → Spec 003 → `plan.md` (aprobado 2026-10-07) → **este task.md** → código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su `Hecho cuando:`
> es verificable con un comando o una observación concreta. Sin marcar una tarea, no se
> empieza la siguiente. RF indicados por tarea (matriz completa en `plan.md` §0).

## Tareas

- [x] **T1 — Git: rama de trabajo (plan §8.0)** `[base/regresión]`
  Merge `feature/hu-002` (HU-002 aceptada, `647b66e`) en `main` y crear `feature/hu-003`
  desde `main` (Q4).
  Hecho cuando: `git merge-base --is-ancestor 647b66e main` sale sin error,
  `git branch --show-current` → `feature/hu-003` y `git status` limpio.

- [x] **T2 — Spec 003: literales RF-3 y cierre de la duda (plan §8.1)** `[RF-2][RF-3][CL-1]`
  Añadir a `specs/003_consultar-servicios/spec.md` la sección «Contenido de servicios»
  con `SERVICES_PAGE_TITLE` «Servicios» y los 2 servicios (name, description, benefits)
  literales del plan §2 (aprobados 2026-10-07), y cerrar la duda abierta (Q1: solo los
  2 mínimos).
  Hecho cuando: la spec contiene los 4 bloques de texto idénticos a los del plan §2
  (comparación directa) y la duda aparece como cerrada/resuelta.

- [x] **T3 — Espejo de literales en `tests/expected_content.py` (plan §1)** `[RF-1..RF-4]`
  Incorporar `SERVICES_PAGE_TITLE` y `SERVICES_CATALOG` (espejo único; D5). No se toca
  aún `PLACEHOLDER_SECTIONS` (eso va en T8).
  Hecho cuando: `python -c "from tests.expected_content import SERVICES_CATALOG as c; assert set(c) == {'psychology_integral', 'nutrition'}"` → exit 0
  y `python -m pytest -q` sigue en **45 PASS / 0 FAIL**.

- [x] **T4 — Módulo de contenido `content/services_catalog.py` (plan §2)** `[RF-1..RF-4][CL-1][CL-2]`
  `SERVICES_CATALOG`, `DEFAULT_SERVICES_CATALOG` (deepcopy) y `SERVICES_PAGE_TITLE`,
  con claves en inglés y literales en español (D9).
  Hecho cuando: `python -c "from consultorio.content.services_catalog import SERVICES_CATALOG as c, DEFAULT_SERVICES_CATALOG as d; assert c == d and len(c) == 2 and all(v['description'] and v['benefits'] for v in c.values())"` → exit 0.

- [x] **T5 — Tests de contenido `test_services_content.py` (plan §6.1, TC-001..004)** `[RF-1..RF-4][RF-3][CL-1][CL-2]`
  Integridad del catálogo, defaults = spec, presencia de los 2 nombres mínimos
  (coherencia con `SERVICES_HIGHLIGHT`), description/beneficios no vacíos.
  Hecho cuando: `python -m pytest tests/test_services_content.py -v` → todos PASS, 0 FAIL.

- [x] **T6 — Módulo de servicio `services/services_service.py` (plan §3)** `[RF-1..RF-4][CL-1][CL-2]`
  `ServicesView`, `get_services_view()` y `validate_services()` con fallback por campo y
  por lista (FIRST_NON_EMPTY / lista no vacía), sin bloques incompletos.
  Hecho cuando: `python -c "from consultorio.services.services_service import get_services_view as g; v = g(); assert len(v.items) == 2 and v.fallback_active is False"` → exit 0.

- [ ] **T7 — Tests de servicio `test_services_service.py` (plan §6.1, TC-005..007)** `[RF-3][CL-1][CL-2]`
  View completo sin fallback; CL-1 con catálogo vacío (monkeypatch) → defaults +
  `fallback_active=True`; CL-2 con description/benefits vacíos → defaults por campo.
  Hecho cuando: `python -m pytest tests/test_services_service.py -v` → todos PASS, 0 FAIL.

- [ ] **T8 — Capa web + plantilla + placeholders (plan §8.5-6)** `[RF-1..RF-4][CL-3][regresión HU-001/002]`
  `web/services.py` (blueprint GET `/servicios`), retiro de `/servicios` de
  `placeholders.py`, registro en `create_app()`, `PLACEHOLDER_SECTIONS` sin `/servicios`
  (D6) y `templates/services/index.html` (h1, un `<section>` con h2 + descripción +
  `<ul>` de beneficios por servicio, «Volver al inicio»; nav desde `get_home_view()`).
  Hecho cuando: `python -c "from consultorio import create_app; c = create_app().test_client(); r = c.get('/servicios'); assert r.status_code == 200 and 'Servicios</h1>' in r.get_data(as_text=True) and 'Psicología Integral' in r.get_data(as_text=True) and 'Psiconutrición' in r.get_data(as_text=True)"` → exit 0
  y `python -m pytest -q` → 0 FAIL.

- [ ] **T9 — CSS `.services-page-*` en `main.css` (plan §8.7, D10)** `[RNF-1][CL-2]`
  Sección mobile-first con medida `max-width` ≈ 65ch por bloque, párrafos
  `text-align: justify` + `hyphens: none`, paleta intacta (solo los 6 hex).
  Hecho cuando: `grep -c "#789B8A\|#B8D8CE\|#F7F3EA\|#D99A7A\|#E8D5B5\|#30454B" static/css/main.css` no introduce hex nuevos (test de paleta en verde) y
  `python -m pytest tests/test_hu_002.py tests/test_hu_001.py -q` → 0 FAIL
  (la regla de paleta existente sigue pasando).

- [ ] **T10 — Tests de ruta `test_services_routes.py` (plan §6.1, TC-008..012)** `[RF-1..RF-4][CL-3][regresión]`
  200 con h1/nombres, 2 secciones con descripción y beneficios, POST → 405,
  `GET /servicios/<recurso>` → 404 con `errors/404.html`, placeholders restantes 200,
  nav de 6 hrefs → 200.
  Hecho cuando: `python -m pytest tests/test_services_routes.py -v` → todos PASS, 0 FAIL.

- [ ] **T11 — Tests de HU `test_hu_003.py` (plan §6.1, TC-013..015)** `[RNF-1][RF-1][RF-2][CL-2][fuera de alcance]`
  RNF (viewport, @media, paleta, medida, justify+hyphens), E2E portada →
  «Ver todos los servicios» → `/servicios` y «Volver al inicio» → `/`, `<main>` sin
  formularios ni enlace a `/citas`.
  Hecho cuando: `python -m pytest tests/test_hu_003.py -v` → todos PASS, 0 FAIL.

- [ ] **T12 — Suite completa y regresión (plan §6.2)** `[todos]`
  Hecho cuando: `python -m pytest -q` → **0 FAIL** con los 45 tests previos intactos
  (HU-001 y HU-002 sin relajar) más los nuevos de HU-003.

- [ ] **T13 — Evidencia QA y visual (plan §6.3)** `[RF-1..RF-4][RNF-1][finalización]`
  Servidor (`python app.py`), capturas CDP con alturas exactas →
  `docs/evidencias/hu-003/escritorio-1280.png` y `movil-375.png`, informe
  `qa-hu-003.md` con PASS/FAIL por TC y veredicto.
  Hecho cuando: los 3 archivos existen, las capturas miden 1280 y 375 px de ancho con
  la altura de `scrollHeight` y `qa-hu-003.md` declara veredicto **PASS** con todos los
  TC en verde.

- [ ] **T14 — Commit/Push de la evidencia + `MEMORY.md`** `[trazabilidad]`
  Hecho cuando: `git status` limpio, `git rev-parse HEAD origin/feature/hu-003` iguales
  y `MEMORY.md` registra HU-003 en evidencia con sus commits.

- [ ] **T15 — Aceptación de la HU (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de aceptación de `docs/evidencias/hu-003/qa-hu-003.md`
  está marcado con fecha y el plan §7.2 queda íntegramente en `[x]`.
