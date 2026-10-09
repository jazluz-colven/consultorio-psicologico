# Informe QA — HU-006 Evitar doble reserva

- **HU:** HU-006 — Spec 006 (`specs/006_evitar-doble-reserva/spec.md`, **enmendada
  dos veces** el 2026-10-09: Q1/Q3/Q4 + contratos RF-4/RF-5; y **Q6/D13** —
  duración mínima visible del estado en curso, 700 ms)
- **Rama:** `feature/hu-006` (desde `main` = `8463087`)
- **Commits:** `e6a8f4f` (spec+plan+task), `6233f9d` (literal, servicio y tests de
  servicio), `afa4423` (web, plantilla, JS, CSS y tests de ruta/HU), `4a26e5d`,
  `d028c0b`, `904ba86`, `44c5792` (progreso, evidencia y memoria) + commits de la
  enmienda 2 (Q6/D13)
- **Fecha:** 2026-10-09
- **Ejecución:** `python -m pytest -q` → **134 PASS / 0 FAIL** (118 previos de
  HU-001/002/003/004/005/016 + 16 nuevos de HU-006)

## Resumen

| Total TC | PASS | FAIL | BLOCKED |
|---|---|---|---|
| 17 | 17 | 0 | 0 |

> **Recuento**: TC-006-016 es la propia corrida de regresión de la suite, no una
> función; las funciones de test son **16** (TC-006-001…015 + TC-006-017), de modo
> que el total es **134** (118 previos + 16).

## Casos de prueba

| Caso | Comando | Resultado | Observación |
|---|---|---|---|
| TC-006-001 | `python -m pytest tests/test_double_booking_service.py -v` | PASS | Horario libre → `Appointment` `pending`, exactamente 1 fila |
| TC-006-002 | `python -m pytest tests/test_double_booking_service.py -v` | PASS | Reintento idéntico → `SLOT_TAKEN`, 0 filas nuevas, original intacta |
| TC-006-003 | `python -m pytest tests/test_double_booking_service.py -v` | PASS | 8 hilos + `Barrier` → 1 éxito, 7 `SLOT_TAKEN`, `COUNT(*) = 1` |
| TC-006-004 | `python -m pytest tests/test_double_booking_service.py -v` | PASS | Misma fecha/hora en servicio distinto → 2 citas (regresión TC-004-007) |
| TC-006-005 | `python -m pytest tests/test_double_booking_service.py -v` | PASS | `IntegrityError` y `database is locked` → `SLOT_TAKEN`; `ValueError` se propaga |
| TC-006-006 | `python -m pytest tests/test_double_booking_routes.py -v` | PASS | `POST` sobre ocupado → **200** + `MSG_SLOT_TAKEN`, hora «Ocupado» sin radio `name="time"`, 1 fila |
| TC-006-007 | `python -m pytest tests/test_double_booking_routes.py -v` | PASS | 8 `POST` concurrentes → 1×303, 7×200 con `MSG_SLOT_TAKEN`, `COUNT(*) = 1` |
| TC-006-008 | `python -m pytest tests/test_double_booking_routes.py -v` | PASS | Ocupada en A → `POST` con servicio B → 303 y 2 filas |
| TC-006-009 | `python -m pytest tests/test_double_booking_routes.py -v` | PASS | `GET /citas` → 200 con `data-submitting="Registrando tu cita…"` y botón `.appointment__submit` |
| TC-006-010 | `python -m pytest tests/test_double_booking_routes.py -v` | PASS | Regresión HU-005: día lleno ausente de `days`, hora en `occupied`, 400/405 intactos |
| TC-006-011 | `python -m pytest tests/test_hu_006.py -v` | PASS | `availability.js`: listener `submit`, `preventDefault`, `disabled`, `data-submitting` vía `dataAttr`, `aria-busy`; sin librerías |
| TC-006-012 | `python -m pytest tests/test_hu_006.py -v` | PASS | CSS `:disabled`/`[aria-busy]`, colores ⊆ 6 hex, `justify`+`hyphens: none`, sin anchos fijos > 375 px |
| TC-006-013 | `python -m pytest tests/test_hu_006.py -v` | PASS | `sqlite_master` conserva `UNIQUE (service, date, time)`; diagnóstico de duplicados → 0 filas tras flujo completo |
| TC-006-014 | `python -m pytest tests/test_hu_006.py -v` | PASS | Espejo `MSG_SUBMITTING`/`MSG_SLOT_TAKEN` idénticos a contenido y a las specs 004/006 |
| TC-006-015 | `python -m pytest tests/test_hu_006.py -v` | PASS | BD de prueba **sin índice** con 2 filas idénticas → el diagnóstico las detecta (política Q1) |
| TC-006-016 | `python -m pytest -q` | PASS | **134 PASS / 0 FAIL**: los 118 tests previos intactos (sin skips ni aserciones relajadas) |
| TC-006-017 | `python -m pytest tests/test_hu_006.py -v` | PASS | **Enmienda Q6/D13:** `SUBMITTING_MIN_MS = 700`, `preventDefault` en el primer envío y `setTimeout(… form.submit())`; valor fijado también en la spec |

**Enmiendas de test previo:** ninguna. No se modificó, eliminó ni relajó ninguna
aserción de HU-001/002/003/004/005/016.

### Desviaciones registradas (sin relajar criterios)

1. **TC-006-014 (literal de la spec 005).** El plan pedía el texto de
   `MSG_SLOT_TAKEN` «idéntico al de specs 004/005»; la spec 005 no declara ese
   literal, así que el test comprueba igualdad espejo↔contenido, presencia en las
   specs 004/006 y ausencia de texto contradictorio en la 005.
2. **Recuento de la suite** (arriba): TC-006-016 es la corrida, no una función.

## Regresión

| Suite | Resultado |
|---|---|
| HU-001/002/003/004/005/016 (118 tests previos) | PASS (0 FAIL, sin relajar aserciones) |
| HU-006 (16 tests nuevos) | PASS |
| `python -m pytest -q` (134 tests) | **134 PASS / 0 FAIL** |

## Demo manual — antes, durante y después (servidor `python app.py`)

Recorrido contra `http://127.0.0.1:5000` con Chrome headless + CDP
(`Emulation.setDeviceMetricsOverride`, `Page.captureScreenshot`):

1. **Antes** — `GET /citas`, servicio Psicología Integral + clic del día **13 de
   octubre** en el calendario → **14 horas libres**, botón «Agendar cita» en
   reposo. Captura `escritorio-1280.png`. ✔
2. **Durante** — formulario completo (08:00) y clic en «Agendar cita»: a **14 ms**
   del clic el botón ya muestra **«Registrando tu cita…» deshabilitado** con el
   form `aria-busy`, y el frame difiere del reposo; la navegación sigue en
   `/citas` al capturar. Captura `boton-en-curso-1280.png`. ✔
3. **Retención medida (Q6/D13)** — instrumentación de `form.submit()` en el reloj
   de la página: el POST real se emite a **728 ms** del clic (≥ 700 ms exigidos) y
   la navegación a la confirmación se completa a **871 ms**. ✔
4. **Después** — **303** → `/citas/confirmada/34` → **200** «Cita registrada»
   (1 fila nueva: `psychology_integral`, 2026-10-13, 08:00). Captura
   `despues-reserva-1280.png`. ✔
5. **Reconsulta (RF-4)** — `GET /citas` + servicio y día 13 → `08:00` como
   **«Ocupado»**; el JSON de `/citas/horarios` y el DOM coinciden exactamente
   (`taken = ["08:00"]`) y **0 radios** seleccionables para esa hora. Captura
   `ocupado-1280.png`. ✔
6. **RF-4 por HTTP** — `POST /citas` sobre la terna ocupada → **200** con
   «Ese horario ya no está disponible. Selecciona otro horario.» y **0 filas**
   nuevas (TC-006-006). ✔
7. **RF-5 (envío repetido)** — guard JS: el segundo envío en curso llama
   `preventDefault` sin segundo `POST` (TC-006-011/017 + demo en el paso 2). ✔

### Datos de la BD de desarrollo usada en la demo

- Filas 1–4: demos de HU-004. Fila 24: demo HU-006 inicial (2026-10-09 08:30).
- Filas 25–28: **pruebas manuales de la usuaria** en el servidor (2026-10-12),
  conservadas.
- Fila 34: reserva de esta evidencia (`psychology_integral`, 2026-10-13, 08:00).
- Las filas 29–33 pertenecían a ejecuciones intermedias del script de evidencia
  (con fallos de medición ya corregidos) y se **eliminaron** antes de la pasada
  final; no eran datos de pacientes.

## Evidencia visual

| Fichero | Medidas programáticas (IHDR) | Verificación |
|---|---|---|
| `docs/evidencias/hu-006/escritorio-1280.png` | 1280×1486 | CDP; antes: día 13 seleccionado, 14 horas libres, botón en reposo |
| `docs/evidencias/hu-006/movil-375.png` | 375×2736 | CDP con `setDeviceMetricsOverride` (no `--window-size`); ancho exacto 375 |
| `docs/evidencias/hu-006/boton-en-curso-1280.png` | 1152×1090 | CDP; recorte del formulario con el botón «Registrando tu cita…» deshabilitado; frame ≠ reposo; capturado dentro de la ventana de 700 ms |
| `docs/evidencias/hu-006/despues-reserva-1280.png` | 1280×900 | CDP; confirmación `/citas/confirmada/34` |
| `docs/evidencias/hu-006/ocupado-1280.png` | 1280×1539 | CDP; 08:00 «Ocupado» con 0 radios seleccionables (espera determinista contra el JSON del backend) |

## Defectos encontrados

Ninguno.

### Notas de proceso (enmienda 2, Q6/D13)

- **Hallazgo de diseño durante la implementación**: el guard original no hacía
  `preventDefault` en el primer envío (el navegador navegaba de inmediato), por lo
  que un simple `setTimeout` no habría garantizado nada. Se añadió
  `preventDefault()` en el primer envío y `form.submit()` a los 700 ms; queda
  registrado en D13. Con JS deshabilitado el formulario se envía nativamente
  (mejora progresiva intacta).
- **La fecha la gobierna el clic del calendario** (`selectDate`), no un `change`
  del input; los scripts de evidencia que fijaban `input.value` directamente
  miraban la vista de otra fecha. Corregido usando el clic real del día.
- **Esperas deterministas en el DOM**: esperar «algún taken» o «el radio X»
  acepta vistas previas/retrasadas de otra fecha; ahora el DOM debe coincidir
  exactamente con el `occupied` del JSON de `/citas/horarios`.
- **Medición del retardo**: correlacionar el reloj mono de CDP con `Date.now()` de
  Node es impreciso; se instrumentó `HTMLFormElement.prototype.submit` para medir
  clic→POST en el reloj de la página (**728 ms**). `Network.emulateNetworkConditions`
  no retrasa el POST en este Chrome headless (se documentó en la enmienda 1).
- El texto «Registrando tu cita…» es contractual: `MSG_SUBMITTING` (spec 006,
  `appointment_content.py`, espejo `expected_content.py`); el JS solo lo lee de
  `data-submitting`.

## Trazabilidad

| Elemento | Estado |
|---|---|
| Spec 006 enmendada (duda Q1, `MSG_SUBMITTING`, reintento, contratos RF-4/RF-5) | ✔ `e6a8f4f` |
| Spec 006 enmienda 2 (Q6: `SUBMITTING_MIN_MS = 700 ms` en contrato RF-5 y dudas cerradas) | ✔ enmienda 2 |
| Plan 006 (D1–D13, Q1–Q6) y `task.md` T1–T19 | ✔ `e6a8f4f` + enmienda 2 |
| Literal `MSG_SUBMITTING` (contenido + espejo) | ✔ `6233f9d` |
| Servicio `create_booking()` endurecido (D3) | ✔ `6233f9d` |
| Tests de servicio (TC-006-001..005) | ✔ `6233f9d` |
| Capa web + plantilla `data-submitting` + JS guard + CSS | ✔ `afa4423` |
| JS `SUBMITTING_MIN_MS` + `preventDefault` + `setTimeout` (D13) | ✔ enmienda 2 |
| Tests de ruta (TC-006-006..010) y de HU (TC-006-011..015, 017) | ✔ `afa4423` + enmienda 2 |
| Evidencia QA y visual (T15/T19) | ✔ esta carpeta |
| Servidor de revisión | `python app.py` → http://127.0.0.1:5000/citas |

## Veredicto

**PASS** — 17/17 TC en verde, 134/134 de la suite, regresión intacta, demo
antes-durante-después con el estado en curso medido (**728 ms** hasta el POST real,
≥ 700 ms exigidos por Q6/D13) y capturas 1280/375 medidas programáticamente.

## Aceptación de la HU

- [x] **ACEPTADA** — T17: aceptación de la usuaria el **2026-10-09** (incluye la
  enmienda 2 Q6/D13: estado en curso visible ≥ 700 ms). HU cerrada y mergeada a
  `main`.
