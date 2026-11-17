# QA HU-019 — Migración a PostgreSQL/Neon (T17)

> **Trazabilidad:** `specs/019_migrar-postgresql/spec.md` (RF-19, RF-28;
> RNF-5, RNF-7) → `plan.md` §6.2 (TC-019-001…024) y §7 → `tasks.md` T17 →
> `docs/evidencias/hu-019/` (T1–T16) → este informe.
>
> **Estado del informe:** COMPLETADO. **Aceptación funcional EMITIDA por la
> usuaria el 2026-11-16**, con la limitación de n8n declarada en §7.1. T17 se
> marca como completada. T18 fue autorizada por la usuaria el 2026-11-16 y su
> implementación se inicia tras este cierre.

## 1. Cabecera, alcance y entorno

| Elemento | Valor real |
|---|---|
| Fecha de ejecución (UTC) | **2026-11-16 22:54** |
| Rama | `feature/hu-019-migracion-postgres` |
| HEAD / `origin/main` | `00e48b8` (`docs(hu-019): registrar commit de cierre de T16`) |
| Commits de referencia | T13 `6f5e132`; T14 `309a442`; T15 `87ab012`; T16 `861e3f4`; cierre T16 `00e48b8` |
| Spec / plan / tareas | `specs/019_migrar-postgresql/spec.md`, `plan.md`, `tasks.md` (T17 autorizada por la usuaria) |
| Alcance | QA, ejecución real de la suite y de las pruebas de HU-019 y rollback, compilación de evidencias T13–T16, solicitud de aceptación |
| Fuera del alcance de la ejecución QA | Cambios de código, tests, `spec.md`, `AGENTS.md` y retirada del rollback (T18). El cierre documental y su commit/push fueron autorizados el 2026-11-16. |
| Python | **3.14.6** (`py -3.14`) |
| pytest / Flask / driver | pytest **9.1.1**; Flask **3.1.3**; `psycopg` **3.3.8** |
| PostgreSQL de pruebas | **16.15** en Docker (`consultorio-pg-019`, `127.0.0.1:55432`) |
| Backend de pruebas | PostgreSQL local (no se usó la base gestionada para la suite) |
| Datos | Solo datos ficticios creados por la suite en esquemas aislados `test_hu019_<uuid>`; sin datos de pacientes |

**Privacidad:** este informe no incluye credenciales, cadenas de conexión,
parámetros de conexión sensibles ni datos personales de pacientes. Las
evidencias históricas citadas usan plantillas redactadas y datos ficticios.

## 2. Resumen del resultado

| Comprobación | Resultado real |
|---|---|
| Suite completa contra PostgreSQL | **399 passed / 0 failed / 0 skipped / 0 xfail**, `EXIT_CODE=0`, **183,39 s** |
| Pruebas específicas `tests/test_hu_019.py` + `tests/test_rollback_sqlite.py` | **8 passed / 0 failed**, **2,65 s**, `EXIT_CODE=0` |
| Salud de producción (Render, solo lectura) | **HTTP 200**, **22,55 s**, cuerpo de 3.653 caracteres / 3.680 bytes UTF-8; compatible con cold start |
| TC-019-001…TC-019-023 | 23 ejecutados: **23 PASS**, 0 FAIL; TC-019-019 con 1 subcomprobación **NO VERIFICADA** |
| TC-019-024 | **PENDIENTE** de T18 (autorizada el 2026-11-16) |
| Aceptación funcional | **EMITIDA por la usuaria el 2026-11-16**, con la limitación de n8n declarada |

**Veredicto QA:** **PASS técnico con limitaciones documentadas** (no es una
aprobación funcional). No hay FAIL ni regresiones detectadas en la suite. La
decisión de aceptación corresponde a la usuaria.

## 3. Matriz por caso de prueba

> PASS = comprobación ejecutada con resultado real y evidencia trazable.
> NO VERIFICADO = subcomprobación concreta que no se pudo ejercitar.
> La corrida de T17 (suite completa) volvió a ejecutar todos los tests
> automatizados; las evidencias de T13–T16 aportan los resultados externos.

| TC | Objetivo (resumen) | Prueba / evidencia real | Resultado |
|---|---|---|---|
| TC-019-001 | Configuración por entorno, TLS en host no local y ausencia de credenciales en configuración | `tests/test_pg_resilience.py` (casos de configuración); `t2-driver-config.md` | **PASS** |
| TC-019-002 | Conexión reutilizada/liberada, semáforo, timeouts y traducción a `PersistenceUnavailable` | `tests/test_pg_resilience.py` (capa de conexiones); `t3-connection-layer.md` | **PASS** |
| TC-019-003 | BD vacía crea tablas, `UNIQUE(event_id)`, índice parcial y `schema_migrations` | `tests/test_pg_schema.py::test_tc_019_003_…`; `schema.md` | **PASS** |
| TC-019-004 | Segunda aplicación del esquema idempotente, sin duplicar objetos ni borrar datos | `tests/test_pg_schema.py::test_tc_019_004_…`; `schema.md` | **PASS** |
| TC-019-005 | Dos instancias concurrentes dejan un solo juego de objetos sin error | `tests/test_pg_schema.py::test_tc_019_005_…`; `schema.md` | **PASS** |
| TC-019-006 | Contrato del repositorio de citas: `RETURNING id`, `%s`, `rowcount`, disponibilidad e integridad | `tests/test_pg_persistence.py::test_tc_019_006_…` (2 casos); `persistence.md` | **PASS** |
| TC-019-007 | Eventos: deduplicación, `UNIQUE(event_id)`, `mark_sent` y `claim_failed_event` | `tests/test_pg_persistence.py::test_tc_019_007_…` (2 casos); `persistence.md` | **PASS** |
| TC-019-008 | `UniqueViolation → SLOT_TAKEN`; indisponibilidad no se confunde; 8 hilos → 1 reserva | `tests/test_pg_persistence.py::test_tc_019_008_…` (2 casos); `persistence.md` | **PASS** |
| TC-019-009 | Atomicidad cancelación + evento `pending`, rollback ante fallo y publicación tras commit | `tests/test_pg_persistence.py::test_tc_019_009_…` (3 casos); `persistence.md` | **PASS** |
| TC-019-010 | BD inalcanzable → 503 con literal aprobado, JSON 503, sin 409/«Ocupado»/inexistente/cancelada | `tests/test_pg_resilience.py::test_tc_019_010_…` (10 casos); `t9-unavailable.md`; capturas `persistence-unavailable.png` y `persistence-unavailable-movil.png` | **PASS** |
| TC-019-011 | Espejo exacto de `MSG_PERSISTENCE_UNAVAILABLE` y literales 004/005 sin cambios | `tests/test_hu_019.py::test_tc_019_011_…`; `t8-literal.md` | **PASS** |
| TC-019-012 | Suite completa contra PostgreSQL, sin `skip`, con cobertura de las Specs 004–018 | `suite-postgres.txt` (T17); corrida de este informe | **PASS** |
| TC-019-013 | Integridad directa del slot; cancelación libera el horario y permite re-reservar | `tests/test_hu_019.py::test_tc_019_013_…` (T17); `persistence.md` | **PASS** |
| TC-019-014 | 8 hilos sobre el mismo slot: 1 cita, 7 `SLOT_TAKEN`, sin excepciones no controladas | `tests/test_hu_019.py::test_tc_019_014_…` (T17); `resilience.md` | **PASS** |
| TC-019-015 | Deduplicación de eventos: segunda inserción `False`, una sola fila, sin segundo envío | `tests/test_hu_019.py::test_tc_019_015_…` (T17); `persistence.md` | **PASS** |
| TC-019-016 | Arranque sin BD no aborta; recuperación perezosa y cold start simulado | `tests/test_pg_resilience.py::test_tc_019_016_…`; `resilience.md` | **PASS** |
| TC-019-017 | `created_at` y `sent_at` en UTC, sin conversión a hora local | `tests/test_pg_persistence.py::test_tc_019_017_…`; `persistence.md` | **PASS** |
| TC-019-018 | Cambio aditivo con datos: conserva filas, integridad e idempotencia | `tests/test_pg_schema.py::test_tc_019_018_…`; `schema.md` | **PASS** |
| TC-019-019 | E2E Neon: TLS, esquema, reserva + eventos y cold start > 5 min | `e2e-neon.md` | **PASS** con 1 subcomprobación **NO VERIFICADA**: `ensure_schema` por el endpoint *pooler* con el parámetro de `statement_timeout` (rechazado por el pooler). Se usó el endpoint directo por la decisión D11. |
| TC-019-020 | Render + Neon: configuración, reserva, persistencia tras redespliegue y spin-down | `render-deploy.md` | **PASS** |
| TC-019-021 | Rollback por interruptor, pérdida aceptada y vuelta a PostgreSQL; incluye `TC-010-014` | `tests/test_rollback_sqlite.py::test_tc_019_021_…` y `test_tc_010_014_…` (T17); `rollback.md` | **PASS** (verificación local; no se ejecutó rollback sobre producción) |
| TC-019-022 | Planes 004/005/006/007/010 sin afirmaciones obsoletas sobre SQLite | `plan-updates.md`; T16 aprobada | **PASS** |
| TC-019-023 | Informe QA con PASS/FAIL por TC, evidencia y checkbox de aceptación | Este documento | **PASS** (informe completo; checkbox marcado el 2026-11-16 con la limitación de n8n declarada) |
| TC-019-024 | Retirada del interruptor, ruta anterior, DDL y pruebas de rollback | T18 | **PENDIENTE** (autorizada el 2026-11-16; se ejecuta en T18) |

## 4. Suite completa y pruebas específicas

### 4.1 Suite completa contra PostgreSQL

Comando ejecutado (el DSN local de pruebas se aportó por entorno y **no se
registra**; su formato operativo está en `docs/operaciones/postgresql.md`):

```powershell
$env:TEST_DATABASE_URL = '<DSN local de pruebas; valor no registrado>'
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
py -3.14 -m pytest -q
```

Salida real:

```text
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 54%]
........................................................................ [ 72%]
........................................................................ [ 90%]
.......................................                                  [100%]
399 passed in 183.39s (0:03:03)
EXIT_CODE=0
```

- **399 tests recolectados y 399 PASS**; 0 failed, 0 skipped, 0 xfail.
- PostgreSQL 16.15 local; `psycopg` 3.3.8; Python 3.14.6.
- La salida completa con encabezado, fecha, rama y commit está en
  `suite-postgres.txt`. Se conserva la constancia histórica de T11/T12
  (**397 PASS**).

### 4.2 Pruebas específicas de HU-019 y rollback

Comando:

```powershell
$env:TEST_DATABASE_URL = '<DSN local de pruebas; valor no registrado>'
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
py -3.14 -m pytest -v tests/test_hu_019.py tests/test_rollback_sqlite.py
```

Salida real:

```text
collected 8 items
tests/test_hu_019.py::test_tc_019_013_slot_integrity_and_cancelled_release PASSED
tests/test_hu_019.py::test_tc_019_014_eight_threads_one_booking_seven_slot_taken PASSED
tests/test_hu_019.py::test_tc_019_015_event_dedup_single_row_without_second_send PASSED
tests/test_hu_019.py::test_tc_019_011_persistence_unavailable_literal_and_unchanged_mirror PASSED
tests/test_hu_019.py::test_sqlite_rollback_route_keeps_repository_contract PASSED
tests/test_hu_019.py::test_t5_target_scope_closes_connection_in_app_context PASSED
tests/test_rollback_sqlite.py::test_tc_010_014_migracion_indice_parcial_respaldo_idempotente_y_aborto PASSED
tests/test_rollback_sqlite.py::test_tc_019_021_rollback_switch_isolates_stores_and_postgres_data_survives PASSED
8 passed in 2.65s
EXIT_CODE=0
```

## 5. Salud de producción (solo lectura)

- Petición: `GET /` a la URL pública del servicio en Render.
- Resultado: **HTTP 200** en **22,55 s**, cuerpo de **3.653 caracteres /
  3.680 bytes UTF-8** (`Content.Length` / `RawContentLength`).
- No se escribió ningún dato ni se ejecutó ninguna reserva.
- Latencia compatible con el arranque en frío del servicio web ya observado en
  T13/T14; no se atribuye a un fallo funcional.
- No se registran aquí encabezados ni valores de configuración del servicio.

## 6. Regresiones revisadas (Specs 004–018)

La suite completa se ejecutó contra PostgreSQL y terminó en verde. Cobertura
recolectada por HU y área afectada:

| Área / Spec | Archivos representativos | Tests recolectados | Resultado |
|---|---|---:|---|
| 004 reserva | `test_hu_004.py`, `test_appointment_*`, `test_home_*` | 5 + 9 + 7 + 4 + 3 + 26 (54) | PASS |
| 005 disponibilidad | `test_hu_005.py`, `test_availability_*` | 3 + 6 + 7 | PASS |
| 006 doble reserva | `test_hu_006.py`, `test_double_booking_*` | 6 + 5 + 5 | PASS |
| 007 automatización | `test_hu_007.py`, `test_automation_service.py`, `test_email_service.py` | 3 + 13 + 12 | PASS |
| 008/010 citas y cancelación | `test_hu_008.py`, `test_hu_010.py`, `test_cancellation_*` | 6 + 4 + 44 + 16 + 17 + 5 | PASS |
| 015/016/017/018 | `test_hu_015.py`, `test_hu_016.py`, `test_hu_017.py`, `test_hu_018.py`, `test_admin_*` | 2 + 2 + 23 + 7 + 9 + 2 | PASS |
| Contenido, rutas y contraste | `test_*_content.py`, `test_*_routes.py`, `test_contraste.py`, `test_search_*` | varios | PASS |
| Persistencia y esquema PG | `test_pg_*.py` | 4 + 10 + 57 | PASS |
| Render | `test_render_manifest.py` | 1 | PASS |
| HU-019 y rollback | `test_hu_019.py`, `test_rollback_sqlite.py` | 6 + 2 | PASS |

- **Total recolectado: 399 tests; 399 PASS; 0 FAIL.**
- Los 18 casos de HU-018 siguen cubiertos (`test_admin_routes.py` 9,
  `test_admin_content.py` 2, `test_hu_018.py` 7) y pasan.
- No se redujo ni relajó ninguna aserción durante T17.
- No se detectaron regresiones funcionales en las Specs 004–018.

## 7. Limitaciones, NO VERIFICADO y pendientes

1. **Automatización real (n8n) no verificada.** El servicio de n8n fue
   eliminado por la usuaria; por eso los eventos de la reserva de T14 quedaron
   en estado `skipped`. La suite cubre la lógica de automatización con tests,
   pero **no se verificó un envío real de extremo a extremo**. Es una
   **limitación operativa externa de HU-007/008 (n8n)**, no una regresión de la
   migración ni un incumplimiento de RNF-5: la suite y los literales
   contractuales sí se verificaron. La restauración de n8n queda fuera del
   alcance de la Spec 019 y la asume la usuaria.
2. **Pooler de Neon con `statement_timeout`.** Con la configuración actual, el
   *pooler* rechaza el parámetro de arranque de timeout; `ensure_schema` a
   través del pooler queda **NO VERIFICADO**. Por la decisión D11 se usó el
   endpoint directo, que sí está verificado (T13/T14). No se debilitó TLS.
3. **Rollback real sobre producción no ejecutado.** TC-019-021 verifica el
   interruptor, la pérdida aceptada y la vuelta a PostgreSQL en local. No se
   tocó el servicio de Render ni la base gestionada durante T15/T17. El
   procedimiento con snapshot manual y hora de corte está documentado en
   `rollback.md` y en la guía operativa.
4. **Cold start.** Se observó en T13 (más de 5 minutos de inactividad) y en el
   ciclo de vida del servicio web de T14. En T17 la comprobación de salud tardó
   22,55 s, compatible con un arranque en frío.
5. **Cuotas de Neon Free.** El plan y la región se verificaron por API en T13;
   no se midieron las cuotas de 1 GB ni de horas de cómputo.
6. **TC-019-024 pendiente.** La retirada del rollback fue autorizada el
   2026-11-16 (T18); no se ejecutó durante T17.

## 8. Privacidad y revisión de credenciales

- No se incluyen cadenas de conexión ni credenciales en este informe ni en
  `suite-postgres.txt`.
- Las evidencias históricas citadas usan plantillas redactadas, nombres de
  variables y descripciones de configuración; no contienen valores de
  credenciales, claves ni datos de pacientes.
- Los datos de las pruebas son ficticios y se crean en esquemas aislados que se
  eliminan al terminar cada test.
- No se usó la base de producción para ejecutar la suite ni para escribir datos
  de prueba.

## 9. Solicitud formal de aceptación

La ejecución técnica de la Spec 019 está completa (T1–T17), con las limitaciones
del §7. Se solicita formalmente a la usuaria la **aceptación funcional** de la
migración a PostgreSQL/Neon.

- [x] Aceptación funcional de la usuaria — **2026-11-16**, con la limitación de
  n8n declarada en §7.1.

**Decisión registrada:** la usuaria aceptó la funcionalidad el **2026-11-16**
con la limitación de n8n declarada en §7.1. La aceptación no declara verificada
la automatización real de n8n. T17 queda completada; T18 fue autorizada el
2026-11-16 y se inicia tras este cierre.

## 10. Trazabilidad y cambios de esta tarea

- **Archivos creados:** `docs/evidencias/hu-019/qa-hu-019.md`.
- **Archivos actualizados:** `docs/evidencias/hu-019/suite-postgres.txt`
  (encabezado y salida real de T17, con nota histórica);
  `docs/evidencias/hu-019/e2e-neon.md` y
  `docs/evidencias/hu-019/render-deploy.md` (solo encabezados de estado
  obsoletos, corregidos con evidencia de Git); `specs/019_migrar-postgresql/tasks.md`
  y `MEMORY.md` (registro de la aceptación funcional del 2026-11-16).
- **No modificados:** código de aplicación, tests, `spec.md`, `plan.md`,
  `AGENTS.md`.
- **Rama/commit:** `feature/hu-019-migracion-postgres` / `00e48b8`.
- **Commit y push:** autorizados el 2026-11-16; el hash se registra en el cierre
  de T17.
