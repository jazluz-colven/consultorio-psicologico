# Informe QA — HU-005 Validar disponibilidad de horarios

- **HU:** HU-005 — Spec 005 (`specs/005_validar-dis-horarios/spec.md`, enmendada 2026-10-09)
- **Rama:** `feature/hu-005`
- **Commits:** `e92112b`…`accb304` (docs, contenido, repositorio, servicio, web, JS, CSS, tests)
- **Fecha:** 2026-10-09
- **Ejecución:** `python -m pytest -q` → **118 PASS / 0 FAIL** (102 previos de
  HU-001/002/003/004/016 + 16 nuevos de HU-005)

## Resumen

| Total | PASS | FAIL | BLOCKED |
|---|---|---|---|
| 16 | 16 | 0 | 0 |

## Casos de prueba

| Caso | Comando | Resultado | Observación |
|---|---|---|---|
| TC-005-001 | `python -m pytest tests/test_availability_service.py -v` | PASS | 14 pares libres en `BOOKING_HOURS`; orden exacto |
| TC-005-002 | `python -m pytest tests/test_availability_service.py -v` | PASS | Hora reservada → `free=False`; la envoltura la excluye |
| TC-005-003 | `python -m pytest tests/test_availability_service.py -v` | PASS | Días sin citas = laborables ≥ hoy; finde/pasada → `[]` |
| TC-005-004 | `python -m pytest tests/test_availability_service.py -v` | PASS | Tras `create_booking` con 14, el día desaparece del mes |
| TC-005-005 | `python -m pytest tests/test_availability_service.py -v` | PASS | Día lleno en servicio A sigue libre en servicio B (D2) |
| TC-005-006 | `python -m pytest tests/test_availability_service.py -v` | PASS | Mes sin huecos → `get_available_days` devuelve `[]` |
| TC-005-007 | `python -m pytest tests/test_availability_service.py -v` | PASS | Ocupada en A → libre en B; aislamiento por servicio |
| TC-005-008 | `python -m pytest tests/test_availability_routes.py -v` | PASS | JSON 200 con `available` + `occupied`; finde → ambos `[]` |
| TC-005-009 | `python -m pytest tests/test_availability_routes.py -v` | PASS | Hora insertada aparece en `occupied` y no en `available` |
| TC-005-010 | `python -m pytest tests/test_availability_routes.py -v` | PASS | E2E: `POST` → 303 → reconsulta con la hora ya ocupada |
| TC-005-011 | `python -m pytest tests/test_availability_routes.py -v` | PASS | `days` = laborables ≥ hoy del mes solicitado |
| TC-005-012 | `python -m pytest tests/test_availability_routes.py -v` | PASS | Día lleno ausente en A, presente en B |
| TC-005-013 | `python -m pytest tests/test_availability_routes.py -v` | PASS | Servicio/mes inválidos → 400; `POST` → 405 |
| TC-005-014 | `python -m pytest tests/test_hu_005.py -v` | PASS | Leyenda, `data-*` con literales, CSS nuevas reglas, paleta ⊆ 6 hex, justify |
| TC-005-015 | `python -m pytest tests/test_hu_005.py -v` | PASS | `availability.js`: tokens, guard `seq`, deselección, sin librerías externas |
| TC-005-016 | `python -m pytest tests/test_hu_005.py -v` | PASS | Carga inicial con BD vacía: 14 `name="time"`, 0 radios ocupados |

Única enmienda de test previo: **TC-004-021** ahora aserta `available` **y**
`occupied` (refuerzo, decisión D9; ningún criterio relajado).

## Regresión

| Suite | Resultado |
|---|---|
| HU-001/002/003/004/016 (102 tests previos) | PASS (0 FAIL, sin relajar aserciones) |
| `python -m pytest -q` (118 tests) | **118 PASS / 0 FAIL** |

## Demo manual (servidor `python app.py`, 2026-10-09)

Recorrido del flujo completo contra `http://127.0.0.1:5000`
(`scripts` temporales `demo_hu005.py`, 16/16 PASS):

1. `GET /citas` → **200** con leyenda del calendario («Con horarios
   disponibles» / «Sin horarios disponibles»), los 4 `data-*` nuevos
   (`data-checking`, `data-occupied-label`, `data-day-no-hours`,
   `data-slot-taken`) y **14 radios** `name="time"` en la carga inicial. ✔
2. `GET /citas/horarios?service=nutrition&date=2026-10-12` → **200** con
   claves `available` y `occupied`; `08:00` en `occupied` y fuera de
   `available`. ✔
3. `GET /citas/horarios?…&date=2026-10-11` (finde) → `available: []`,
   `occupied: []`. ✔
4. `POST /citas` con la hora ocupada (2026-10-12 08:00) → **200** con
   «Ese horario ya no está disponible. Selecciona otro horario.» y
   **sin fila nueva** (total de filas sin incremento). ✔
5. `POST /citas` válido (Psicología Integral, 2026-10-21 10:00) → **303** →
   `GET /citas/confirmada/20` → **200** «Cita registrada», paciente, fecha,
   hora y estado «Pendiente». ✔
6. Reconsulta: `10:00` ya aparece en `occupied` y no en `available`. ✔
7. Aislamiento por servicio: `GET /citas/horarios?service=nutrition&date=2026-10-21`
   → `10:00` sigue **libre** para el otro servicio. ✔
8. `GET /citas/disponibilidad?service=nutrition&month=2026-10` → **200**
   con `days` (16 días laborables ≥ hoy). ✔
9. Errores: servicio fantasma → **400**; `month=2026-13` → **400**;
   `POST /citas/disponibilidad` → **405**. ✔
10. Día lleno (siembra temporal 2027-01-06, 14 citas, retirada tras la
    prueba): ausente de `days` para nutrition, presente para
    psychology_integral. ✔

### Demo visual (CDP, `Emulation.setDeviceMetricsOverride`)

1. Servicio Psiconutrición + clic «12 de octubre de 2026» → fecha
   `2026-10-12`, Mañana con **08:00 «Ocupado»** (deshabilitado, sin `name`,
   badge), 13 horas libres y leyenda visible. ✔
2. Navegación a enero de 2027 con siembra → día **6** con clase `is-full`,
   `disabled`, `aria-label` «6 de enero de 2027, sin horarios disponibles»,
   `text-decoration: line-through` y fondo arena `#E8D5B5`; resto de días
   laborables `is-bookable` (20) y sábados/domingos `is-disabled` (10). ✔
3. Sin desborde horizontal: `scrollWidth` = `clientWidth` (1280 y 375). ✔

## Evidencia visual

| Fichero | Medidas programáticas | Verificación |
|---|---|---|
| `docs/evidencias/hu-005/escritorio-1280.png` | 1280×1539 | CDP; día 12 seleccionado, badge «Ocupado», leyenda, sin desborde (`1280 = 1280`) |
| `docs/evidencias/hu-005/movil-375.png` | 375×2726 | CDP; mismo flujo en móvil, sin desborde (`375 = 375`) |
| `docs/evidencias/hu-005/dia-lleno-1280.png` | 1280×1486 | CDP; enero 2027 con día 6 `is-full` («sin horarios disponibles») y leyenda |

## Defectos encontrados

Ninguno.

Nota de proceso: las primeras capturas se lanzaron en paralelo sobre el
mismo puerto CDP y se pisaron (medición y mes incorrectos); se repitieron
secuencialmente con medición estable. Es un artefacto del script de
evidencia, no del producto.

## Trazabilidad

| Elemento | Estado |
|---|---|
| Spec 005 enmendada (duda cerrada, literales y contratos) | ✔ `e92112b`, `56cff54` |
| Plan 005 (D1–D11) y `task.md` T1–T18 | ✔ |
| Espejo de literales en `tests/expected_content.py` | ✔ `56cff54` |
| Repositorio `list_booked_times_by_date` | ✔ `40a71ac` |
| Servicio `get_hours_with_status` / `get_available_days` / `is_valid_month` | ✔ `9d92e0c` |
| Tests de servicio (TC-005-001..007) | ✔ `ef8a5ca` |
| Capa web + plantilla + enmienda TC-004-021 (D9) | ✔ `faf967c` |
| Tests de ruta (TC-005-008..013) | ✔ `c37fd53` |
| JS (estados de día, guard, ocupadas) | ✔ `f9b62f1` |
| CSS (`is-full`, ocupadas, leyenda) | ✔ `6dedebd` |
| Tests de HU (TC-005-014..016) | ✔ `accb304` |
| `task.md` T6–T15 marcadas | ✔ esta evidencia |
| Evidencia QA y visual (T16) | ✔ esta carpeta |
| Servidor de revisión | `python app.py` → http://127.0.0.1:5000/citas |

## Veredicto

**PASS** — 16/16 TC en verde, 118/118 de la suite, regresión intacta, demo
manual del flujo completo (16/16 comprobaciones) y demo visual verificadas.

## Aceptación de la HU

- [x] **ACEPTADA 2026-10-09** — T18: aceptación de la usuaria («Se acepta HU-005»).
