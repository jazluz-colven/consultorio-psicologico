# Tareas HU-015 — Consultar información de contacto (ampliación: cajón + iconos + mapa)

> Trazabilidad: HU-015 → Spec 015 (enmendada 2026-10-12 con RF-7 y `MAP_*`) →
> `plan.md` (plan de ampliación, aprobado 2026-10-12) → **este task.md** →
> código → tests → evidencia → commit.
> Cada tarea dura **< 30 min**, se ejecuta **en orden** (dependencias) y su
> `Hecho cuando:` es verificable con un comando o una observación concreta. Sin
> marcar una tarea, no se empieza la siguiente. RF por tarea (matriz completa en
> `plan.md` §0). Baseline: **179 PASS / 0 FAIL** (HU-015 v1 + resto).
> Contexto: HU-015 **v1 aceptada y mergeada** (`f99490b`); esta rama
> `feature/hu-015-diseno` solo amplía presentación (cajón + iconos) y añade RF-7 (mapa).

## Tareas

- [x] **T1 — Aprobación del plan de ampliación y de Q13 (plan §7.1)** `[trazabilidad]`
  La usuaria aprueba este plan reescrito contra el código real: Q8 (iframe Google Maps
  sin API key + enlace), Q9 (cajón único con filas icono+etiqueta+valor; 2 columnas
  ≥900 px), Q10 (se conserva «Dirección»), Q11 (enmienda de la spec), Q12 (planes
  previos descartados) y Q13 (ampliar la HU-015 existente en la rama
  `feature/hu-015-diseno`).
  Hecho cuando: Q8–Q13 están fechadas en `plan.md` §7.1 y §7.2 marca la aprobación.

- [x] **T2 — Sincronización y rama (plan §8.0, Q4/Q13)** `[base]`
  `git pull --ff-only` de `main` a `f99490b` (HU-015 v1 + Render + MEMORY) y creación
  de `feature/hu-015-diseno` desde ese punto.
  Hecho cuando: `git branch --show-current` → `feature/hu-015-diseno`,
  `git merge-base --is-ancestor origin/main feature/hu-015-diseno` → exit 0 y
  `python -m pytest -q` → **179 PASS / 0 FAIL**.

- [x] **T3 — Spec 015: enmienda RF-7 + literales MAP_* (plan §8.1, Q11)** `[RF-7][CL-5]`
  RF-7 (mapa condicionado a dirección), los 5 literales `MAP_*` y el caso límite «mapa
  no disponible» sobre la spec ya commiteada en el remoto.
  Hecho cuando: la spec contiene «RF-7», `MAP_QUERY`/`MAP_EMBED_URL`/`MAP_LINK_URL`/
  `MAP_LINK_LABEL`/`MAP_FRAME_TITLE` y «Mapa no disponible», y la suite sigue en
  **179 PASS / 0 FAIL**.

- [ ] **T4 — Commit inicial: spec + plan + task en la rama (plan §7.2)** `[trazabilidad]`
  Commitear la enmienda de la spec y estos documentos de planificación antes de tocar
  código.
  Hecho cuando: `git status` limpio salvo `Campos_n8n.xlsx` (sin versionar, fuera del
  alcance) y `git show --stat HEAD` muestra `specs/015_consultar-contacto/{spec,plan,task}.md`.

- [ ] **T5 — Espejo: `CONTACT_MAP_*` en `tests/expected_content.py` (plan §2, D6)** `[RF-7]`
  Añadir `CONTACT_MAP_QUERY`, `CONTACT_MAP_EMBED_URL`, `CONTACT_MAP_LINK_URL`,
  `CONTACT_MAP_LINK_LABEL` y `CONTACT_MAP_FRAME_TITLE` (espejo único de la spec; los
  literales `CONTACT_*` de v1 no se tocan). Sin lógica.
  Hecho cuando: `python -c "import tests.expected_content as e; assert e.CONTACT_MAP_LINK_LABEL == 'Abrir en Google Maps' and e.CONTACT_MAP_EMBED_URL.startswith('https://www.google.com/maps?q=')"` → exit 0
  y `python -m pytest -q` sigue en **179 PASS / 0 FAIL**.

- [ ] **T6 — Contenido: `MAP_*` en `contact_content.py` (plan §2, D2)** `[RF-7][CL-1][CL-5]`
  `MAP_QUERY`, `MAP_EMBED_URL`/`MAP_LINK_URL` con `urllib.parse.quote` (stdlib),
  `MAP_LINK_LABEL`, `MAP_FRAME_TITLE` y `DEFAULT_MAP_QUERY`; el resto del módulo queda
  idéntico a v1.
  Hecho cuando: `python -c "from consultorio.content import contact_content as c; assert c.MAP_QUERY.startswith('Calle 34 #29-18') and c.MAP_EMBED_URL.endswith('&output=embed') and c.DEFAULT_MAP_QUERY == c.MAP_QUERY"` → exit 0.

- [ ] **T7 — Tests de contenido: TC-015-017 (plan §6.1)** `[RF-7]`
  Unidad de `CONTACT_MAP_*`: dominio `www.google.com/maps`, `output=embed`, consulta
  URL-encoded en embed y link, literal de enlace y título.
  Hecho cuando: `python -m pytest tests/test_contact_content.py -v` → todos PASS (los 4
  de v1 + el nuevo), 0 FAIL.

- [ ] **T8 — Servicio: `ContactMap` + `map` en `ContactView` (plan §3, D3/D15/D17)** `[RF-7][CL-1][CL-5]`
  Dataclass `ContactMap`, campo `map` en `ContactView`, `_resolve_map()` (vivo →
  default → omisión; `None` si no hay dirección ni consulta) y `fallback` ampliado; el
  resto de `validate_contact()` queda intacto.
  Hecho cuando: `python -c "from consultorio.services.contact_service import get_contact_view as g; v = g(); assert v.map and v.map.title and v.fallback_active is False and len(v.channels) == 3"` → exit 0
  y `python -m pytest -q` → **0 FAIL** (los tests de servicio de v1 siguen verdes).

- [ ] **T9 — Tests de servicio: TC-015-018 (plan §6.1)** `[RF-7][CL-1][CL-5]`
  `map` completo sin fallback; CL-1 dirección+default vacíos → `map is None`; CL-5
  `MAP_QUERY` vacío → `map is None` con dirección intacta y `fallback_active=True`.
  Hecho cuando: `python -m pytest tests/test_contact_service.py -v` → todos PASS (los 5
  de v1 + el nuevo), 0 FAIL.

- [ ] **T10 — Plantilla: refactor a cajón + iconos + mapa (plan §8.7, D4/D5/D8/D19)** `[RF-1..RF-7][RNF-2]`
  `templates/contact/index.html`: h1 intacto, cajón `.contact__panel` con `<ul>` de
  filas `<li class="contact__row">` (icono SVG inline `aria-hidden` + etiqueta de
  `titles` + valor/enlaces **con el mismo marcado de enlaces de v1**), bloque
  `.contact__map` (`iframe` con `title` + `loading="lazy"` + enlace «Abrir en Google
  Maps» `target="_blank" rel="noopener"`) y «Volver al inicio»; sin condicionales de
  negocio.
  Hecho cuando: `python -c "from consultorio import create_app; h = create_app().test_client().get('/contacto').get_data(as_text=True); assert 'contact__panel' in h and 'contact__row' in h and 'aria-hidden=\"true\"' in h and 'www.google.com/maps' in h and 'Abrir en Google Maps' in h and '>Teléfono<' not in h"` → exit 0.

- [ ] **T11 — CSS: refactor `.contact-*` (plan §8.8, D10)** `[RNF-1][RNF-2]`
  `.contact` en grid: 1 columna por defecto y `@media (min-width: 900px)` con
  `grid-template-columns` de 2 columnas (cajón ‖ mapa, misma altura); `.contact__panel`
  (fondo `--color-secondary`, radio 12 px, hairlines `--color-primary`), filas con
  iconos (`currentColor`), `.contact__map` con `aspect-ratio` + `border-radius`,
  `justify`+`hyphens: none` donde aplique y paleta intacta (solo los 6 hex).
  Hecho cuando: `python -m pytest tests/test_hu_001.py tests/test_hu_002.py tests/test_hu_003.py tests/test_hu_016.py -q` → **0 FAIL**
  (paleta/tipografía intactas).

- [ ] **T12 — Tests de ruta: TC-015-009/012 adaptados + TC-015-019 nuevo (plan §6.1, D7)** `[RF-1][RF-6][RF-7]`
  TC-009 ⇒ cajón `.contact__panel` con ≥1 fila; TC-012 ⇒ ≥5 `.contact__row` con
  `<svg aria-hidden="true">` y etiqueta, sin datos mezclados; TC-019 ⇒ iframe
  `www.google.com/maps` con `title` y `loading="lazy"` + enlace de respaldo + dirección
  fuera del iframe. TC-010/011/013/014 de v1 **sin cambios** y en verde.
  Hecho cuando: `python -m pytest tests/test_contact_routes.py -v` → todos PASS, 0 FAIL.

- [ ] **T13 — Tests de HU: TC-015-015 adaptado (plan §6.1)** `[RNF-1][RNF-2]`
  Añadir la aserción de grid de 2 columnas en `@media (min-width: 900px)` y ajustar los
  selectores de justificación a `.contact__row`/enlaces del mapa; paleta ⊆ 6 hex y
  viewport intactos; TC-015-016 sin cambios.
  Hecho cuando: `python -m pytest tests/test_hu_015.py -v` → todos PASS, 0 FAIL.

- [ ] **T14 — Suite completa y regresión (plan §6.2)** `[todos]`
  Ejecutar la suite completa sin relajar aserciones previas.
  Hecho cuando: `python -m pytest -q` → **0 FAIL** con los **179** actuales (v1 con 3
  adaptados) más los **3** nuevos (**182 en total**).

- [ ] **T15 — Evidencia QA y visual de la ampliación (plan §6.3, D21)** `[RF-6][RF-7][RNF-1][finalización]`
  Servidor, recorrido manual (cajón con iconos, enlaces `wa.me`/`mailto:`/Instagram,
  mapa embebido visible y «Abrir en Google Maps») y capturas CDP regeneradas →
  `docs/evidencias/hu-015/escritorio-1280.png` (cajón ‖ mapa) y
  `movil-375.png` (cajón sobre mapa); sección «Ampliación 2026-10-12» en
  `qa-hu-015.md` con PASS/FAIL por TC y checkbox (skill `pytest-qa`).
  Hecho cuando: las capturas miden 1280 y 375 px de ancho con la altura de
  `scrollHeight`, el iframe aparece en la de escritorio y `qa-hu-015.md` deja constancia
  de la ampliación con veredicto; servidor en marcha con la URL comunicada.

- [ ] **T16 — Commits por fase, Push y `MEMORY.md` (plan §8.10)** `[trazabilidad]`
  Commits por fase (spec+plan+task+espejo → contenido+servicio → plantilla+CSS →
  tests → evidencia+MEMORY) citando HU-015/Spec 015 (ampliación); nunca datos sensibles
  en repo o memoria.
  Hecho cuando: `git status` limpio (salvo `Campos_n8n.xlsx`), `git rev-parse HEAD` =
  `git rev-parse origin/feature/hu-015-diseno` y `MEMORY.md` registra la ampliación
  (cajón + iconos + mapa RF-7, rama `feature/hu-015-diseno`).

- [ ] **T17 — Aceptación de la ampliación (usuaria)** `[cierre]`
  Hecho cuando: el checkbox de la ampliación en `qa-hu-015.md` está marcado con fecha y
  la §7.2 del plan queda íntegramente en `[x]`.
