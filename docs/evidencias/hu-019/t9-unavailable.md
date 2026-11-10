# Evidencia T9 — Errores HTTP/UX de indisponibilidad de persistencia

- **Fecha:** 2026-11-10
- **Rama:** `feature/hu-019-migracion-postgres`
- **HEAD:** `0f5b0d8`
- **Tarea:** T9 — manejo HTTP/UX mínimo de indisponibilidad de persistencia
- **Autorización:** expresa de la usuaria el 2026-11-10
- **Alcance:** handler central 503, plantilla de indisponibilidad, estado de
  `availability.js`, pruebas TC-019-010 y documentación operativa. No se
  modifican specs (salvo el marcador de T9 ya existente), literales
  contractuales ni `tests/expected_content.py`.

## 1. Trazabilidad

`Spec 019 RF-20, RF-21 / RNF-6 / CL-1, CL-2, CL-3, CL-11` → `plan.md` D6, D12,
§5 y §6 (TC-019-010) → `tasks.md` T9 → `TC-019-010`.

- **RF-20:** una base no disponible no registra la cita, no muestra confirmación
  y comunica el literal aprobado.
- **RF-21:** el fallo no se presenta como horario ocupado, cita inexistente ni
  cita cancelada.
- **RNF-6:** sin DSN, contraseña ni PII en la respuesta ni en los logs.
- **CL-1/CL-2/CL-3/CL-11:** cuota agotada, base dormida/inalcanzable, escrituras
  fallidas y límite de conexiones terminan en indisponibilidad, nunca en un
  conflicto de negocio.

## 2. Implementación

| Archivo | Cambio |
|---|---|
| `consultorio/errors.py` | Handler `PersistenceUnavailable` → **503**. Decide HTML/JSON por `request.endpoint` (`appointments.horarios`, `appointments.disponibilidad`). Log constante sin DSN/PII. |
| `templates/errors/persistence_unavailable.html` | Plantilla 503: literal aprobado y enlace a `/citas` con etiqueta reutilizada `ADMIN_BACK_BUTTON` («Volver»). Sin copy nuevo. |
| `consultorio/web/appointments.py` | Pasa `MSG_PERSISTENCE_UNAVAILABLE` a la plantilla de reserva. |
| `templates/appointments/index.html` | `data-unavailable-message` con el literal servido por el backend. |
| `static/js/availability.js` | Ante 503/no-2xx/fallo de red: limpia las horas, muestra el literal y **no** crea badges «Ocupado» ni estados de día engañosos. Mantiene los guards `daySeq`/`hoursSeq`. |
| `tests/test_pg_resilience.py` | TC-019-010 con 10 pruebas contra un fallo real del driver. |
| `docs/operaciones/postgresql.md` | Comportamiento 503 y procedimiento de reproducción con un DSN inalcanzable. |

### Decisión JSON vs HTML

Determinista por *endpoint*, no por `Accept`:

- `appointments.horarios` y `appointments.disponibilidad` →
  `{"error": MSG_PERSISTENCE_UNAVAILABLE}` con 503.
- Cualquier otra superficie → plantilla HTML 503.

### Decisión sobre el enlace de vuelta

El enlace apunta a `/citas` y su etiqueta es **`ADMIN_BACK_BUTTON` = «Volver»**
(literal contractual ya existente en `consultorio/content/admin_content.py`).
No se creó ningún texto nuevo. El `<title>` reutiliza el propio literal
aprobado.

## 3. Pruebas TC-019-010

Comando:

```powershell
python -m pytest -q tests/test_pg_resilience.py -k "tc_019_010"
```

Resultado real:

```text
..........                                                               [100%]
10 passed, 47 deselected in 41.19s
```

La indisponibilidad se fuerza con una aplicación real:

- `PERSISTENCE_BACKEND=postgres`
- `DATABASE_URL` con `127.0.0.1:1` (puerto sin servidor) y credenciales
  ficticias de prueba
- `DATABASE_CONNECT_TIMEOUT=1` y `DATABASE_ACQUIRE_TIMEOUT=1`
- `create_app(...)` con `TESTING=True`; el fallo nace en `psycopg`, se traduce
  en `consultorio.persistence.database` y llega al handler. **No** se
  monkeypatchea `get_database` ni el resultado de los servicios.

| # | Caso | Resultado |
|---|---|---|
| 1 | `GET /citas` HTML → 503, literal exacto y enlace `href="/citas"` | PASS |
| 2 | `GET /citas/horarios` → 503 con `{"error": MSG_PERSISTENCE_UNAVAILABLE}` | PASS |
| 3 | `GET /citas/disponibilidad` → 503 con la misma forma | PASS |
| 4 | `POST /citas` con datos válidos → 503, sin 303/Location, sin `MSG_SLOT_TAKEN` ni «Ocupado» ni confirmación | PASS |
| 5 | `GET /citas/confirmada/1` → 503, no 404 | PASS |
| 6 | Cancelación 017: verificación, confirmación y éxito → 503, sin `MSG_VERIFICATION_FAILED` ni «ya cancelada» | PASS |
| 7 | Admin 018: detalle, cancelar y reprogramar → 503, sin `ADMIN_APPOINTMENT_NOT_FOUND` ni «ya estaba cancelada» | PASS |
| 8 | Cuerpo y logs sin DSN, contraseña, documento, nombre, email ni teléfono | PASS |
| 9 | Regresión: 404, 405 y 500 siguen respondiendo con sus plantillas | PASS |
| 10 | Comprobación de plantilla/JS: literal servido por el backend; rama 503 sin `createTakenHour` ni `data-occupied-label` | PASS |

### Fragmento real del cuerpo 503

```text
No pudimos completar tu solicitud en este momento. Inténtalo de nuevo en unos minutos.

Volver
```

## 4. Suite completa (PostgreSQL real)

Comando:

```powershell
$env:TEST_DATABASE_URL='postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable'
python -m pytest -q
```

Resultado real:

```text
396 passed in 91.75s (0:01:31)
```

- Baseline previo de T8: **386 PASS**.
- T9 añade **10** pruebas ⇒ **396 PASS / 0 FAIL**, sin `skip`.
- El contenedor `consultorio-pg-019` (PostgreSQL 16.15) estaba en marcha.

## 5. Validación visual

La app se levantó con `DATABASE_URL` apuntando a `127.0.0.1:1` y se capturó con
Google Chrome 157.0.8103.38 + DevTools Protocol
(`Emulation.setDeviceMetricsOverride`; **no** se usó `--window-size`).

| Vista | Viewport | `scrollWidth` | `innerWidth` | Desborde | Archivo |
|---|---|---|---|---|---|
| Escritorio | 1280×900 | 1280 | 1280 | No | `docs/evidencias/hu-019/persistence-unavailable.png` |
| Móvil (emulación) | 375×800 | 375 | 375 | No | `docs/evidencias/hu-019/persistence-unavailable-movil.png` |

En ambas vistas el texto visible es exactamente el literal aprobado y «Volver»;
el enlace resuelve a `/citas`. La pantalla usa `.error-page` y la paleta
vigente; no se añadieron colores ni literales. Medidas completas en el reporte
CDP de la sesión (no versionado) y resumidas en esta tabla.

Auditoría de consola/red con el mismo navegador:

- **503 real:** sin `Runtime.exceptionThrown` ni subrecursos fallidos. La consola
  registra el 503 del documento (esperado) y el 404 preexistente de
  `/favicon.ico`; no hay errores de JavaScript.
- **Servidor normal (`/citas`, 200):** sin excepciones ni peticiones fallidas;
  solo el 404 preexistente de `/favicon.ico`.

El 404 de `favicon.ico` no lo introduce T9 y no afecta a la pantalla de
indisponibilidad.

## 6. Limitaciones

- El proyecto no tiene runner de pruebas de JavaScript. La rama 503 de
  `availability.js` se validó con comprobación estática y con la respuesta real
  503 del backend en navegador; no se ejecutó una prueba unitaria de JS.
- La captura visual reproduce la pantalla 503 con una base inalcanzable; no
  sustituye la aceptación funcional de la usuaria.
- No se modificaron `specs/`, literales contractuales ni
  `tests/expected_content.py`.
