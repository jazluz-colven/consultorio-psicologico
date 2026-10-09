# Informe QA — HU-006 Evitar doble reserva

- **HU:** HU-006 — Spec 006 (`specs/006_evitar-doble-reserva/spec.md`, enmendada
  2026-10-09)
- **Rama:** `feature/hu-006` (desde `main` = `8463087`)
- **Commits:** `e6a8f4f` (spec+plan+task), `6233f9d` (literal, servicio y tests de
  servicio), `afa4423` (web, plantilla, JS, CSS y tests de ruta/HU) + commit de
  esta evidencia
- **Fecha:** 2026-10-09
- **Ejecución:** `python -m pytest -q` → **133 PASS / 0 FAIL** (118 previos de
  HU-001/002/003/004/005/016 + 15 nuevos de HU-006)

## Resumen

| Total TC | PASS | FAIL | BLOCKED |
|---|---|---|---|
| 16 | 16 | 0 | 0 |

> **Recuento (plan §6.1)**: TC-006-001…015 son funciones de test (15). TC-006-016
> es la propia corrida de regresión de la suite, por lo que el total de tests es
> **133** (118 + 15) y no 134; se registró la aclaración en el plan y en el
> `task.md` sin tocar ningún criterio.

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
| TC-006-016 | `python -m pytest -q` | PASS | **133 PASS / 0 FAIL**: los 118 tests previos intactos (sin skips ni aserciones relajadas) |

**Enmienda de test previo:** ninguna. No se modificó, eliminó ni relajó ninguna
aserción de HU-001/002/003/004/005/016.

### Desviaciones registradas (sin relajar criterios)

1. **TC-006-014 (literal de la spec 005).** El plan pedía el texto de
   `MSG_SLOT_TAKEN` «idéntico al de specs 004/005»; la spec 005 no declara ese
   literal (solo reutiliza los suyos), así que el test comprueba: igualdad
   espejo↔contenido, presencia del texto en las specs 004 y 006 y que la spec 005
   no introduce un texto contradictorio.
2. **Recuento 133 vs 134** (arriba). Criterio intacto: 0 FAIL con los 118 previos.

## Regresión

| Suite | Resultado |
|---|---|
| HU-001/002/003/004/005/016 (118 tests previos) | PASS (0 FAIL, sin relajar aserciones) |
| HU-006 (15 tests nuevos) | PASS |
| `python -m pytest -q` (133 tests) | **133 PASS / 0 FAIL** (14,95 s) |

## Demo manual — antes, durante y después (servidor `python app.py`)

Recorrido contra `http://127.0.0.1:5000` con Chrome headless + CDP
(`Emulation.setDeviceMetricsOverride`, `Page.captureScreenshot` y
`Fetch.requestPaused`):

1. **Antes** — `GET /citas` → **200**, fecha por defecto `2026-10-09`, 14 horas
   libres y botón «Agendar cita» en reposo. Captura `escritorio-1280.png`. ✔
2. **Durante** — formulario completo (Psicología Integral, 2026-10-09 08:30) y
   clic en «Agendar cita» con el `POST /citas` **pausado por CDP**
   (`Fetch.requestPaused`, payload
   `service=psychology_integral&…&date=2026-10-09&time=08%3A30`): el frame del
   formulario **cambia** respecto al reposo y el botón aparece
   **«Registrando tu cita…» deshabilitado** (arena `#E8D5B5`) con el form
   `aria-busy`. Captura `boton-en-curso-1280.png` verificada visualmente. ✔
3. **Después** — se libera la petición → **303** → `/citas/confirmada/24` →
   **200** «Cita registrada» (1 fila nueva). Captura `despues-reserva-1280.png`. ✔
4. **Reconsulta (RF-4)** — `GET /citas` → **200** con `08:30` como **«Ocupado»**
   (`takenCount: 1`), **sin** radio seleccionable (`selectable: 0`) para esa
   hora. Captura `ocupado-1280.png`. ✔
5. **RF-4 por HTTP** — `POST /citas` sobre la terna ocupada → **200** con
   «Ese horario ya no está disponible. Selecciona otro horario.» y **0 filas**
   nuevas (TC-006-006). ✔
6. **RF-5 (envío repetido)** — guard JS: segundo envío en curso →
   `preventDefault` sin segundo `POST` (TC-006-011 + demo en el paso 2). ✔

Nota de integridad de la demo: la reserva del paso 2/3 quedó registrada como
dato de demostración (`psychology_integral`, 2026-10-09, 08:30, id 24) en
`data/consultorio.db`, junto con las filas de demo previas de HU-004/005.

## Evidencia visual

| Fichero | Medidas programáticas (IHDR) | Verificación |
|---|---|---|
| `docs/evidencias/hu-006/escritorio-1280.png` | 1280×1486 | CDP; antes: 14 horas libres, botón en reposo, calendario octubre 2026 |
| `docs/evidencias/hu-006/movil-375.png` | 375×2656 | CDP con `setDeviceMetricsOverride` (no `--window-size`); ancho exacto 375 |
| `docs/evidencias/hu-006/boton-en-curso-1280.png` | 1152×1010 | CDP; recorte del formulario con el botón «Registrando tu cita…» deshabilitado; frame ≠ reposo |
| `docs/evidencias/hu-006/despues-reserva-1280.png` | 1280×900 | CDP; confirmación `/citas/confirmada/24` |
| `docs/evidencias/hu-006/ocupado-1280.png` | 1280×1539 | CDP; 08:30 «Ocupado» sin radio seleccionable |

## Defectos encontrados

Ninguno.

### Notas de proceso

- `Network.emulateNetworkConditions` no retrasó el `POST` en este Chrome
  headless; se sustituyó por **`Fetch.requestPaused`** (CDP), que pausa la
  petición de forma determinista y permite capturar el estado en curso real.
- Dos ejecuciones fallidas del script de evidencia dejaron citas de prueba en
  `data/consultorio.db` (ids 21, 22 y 23); se **eliminaron** antes de la
  ejecución final, que dejó únicamente la fila de la demo (id 24).
- El texto «Registrando tu cita…» del botón es contractual: vive en
  `MSG_SUBMITTING` (spec 006, `appointment_content.py`, espejo
  `expected_content.py`); el JS solo lo lee de `data-submitting`.

## Trazabilidad

| Elemento | Estado |
|---|---|
| Spec 006 enmendada (duda Q1 cerrada, `MSG_SUBMITTING`, reintento, contratos RF-4/RF-5) | ✔ `e6a8f4f` |
| Plan 006 (D1–D12, Q1–Q5) y `task.md` T1–T17 | ✔ `e6a8f4f` |
| Literal `MSG_SUBMITTING` (contenido + espejo) | ✔ `6233f9d` |
| Servicio `create_booking()` endurecido (D3) | ✔ `6233f9d` |
| Tests de servicio (TC-006-001..005) | ✔ `6233f9d` |
| Capa web + plantilla `data-submitting` | ✔ `afa4423` |
| JS guard de submit | ✔ `afa4423` |
| CSS estado en curso | ✔ `afa4423` |
| Tests de ruta (TC-006-006..010) y de HU (TC-006-011..015) | ✔ `afa4423` |
| Evidencia QA y visual (T15) | ✔ esta carpeta |
| Servidor de revisión | `python app.py` → http://127.0.0.1:5000/citas |

## Veredicto

**PASS** — 16/16 TC en verde, 133/133 de la suite, regresión intacta, demo
antes-durante-después verificada (incluido el estado en curso del botón) y
capturas 1280/375 medidas programáticamente.

## Aceptación de la HU

- [ ] **PENDIENTE** — T17: aceptación de la usuaria.
