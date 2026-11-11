# Evidencia T12 — integridad, concurrencia, atomicidad, cold start y errores

> Trazabilidad: **Spec 019** (`specs/019_migrar-postgresql/spec.md`, RF-10 a
> RF-14, RF-20 a RF-23, RF-30; CL-1 a CL-11) → `plan.md` §6.2 y matriz de
> trazabilidad → `tasks.md` **T12** → código → tests → esta evidencia.
> Rama: `feature/hu-019-migracion-postgres`. HEAD al iniciar: `5419d4a`.
> Fecha: **2026-11-11**. PostgreSQL local: `postgres:16-alpine` (contenedor
> `consultorio-pg-019`, `127.0.0.1:55432`, versión 16.15).

## 1. Alcance y estado

T12 cubre **TC-019-003 a TC-019-018** con pruebas no vacuas. Esta evidencia
registra la auditoría y los refuerzos; los detalles por archivo están en:

- `schema.md` → TC-019-003, 004, 005, 018.
- `persistence.md` → TC-019-006 a 009, 011, 013 a 015, 017 (incluye TC-019-014).
- Este documento → TC-019-010, TC-019-016 (cold start) y la evidencia global.

Estado: **implementado y verificado; pendiente de revisión**. No se declara
T12 completada en `tasks.md` ni hay aceptación funcional. **Sin commit ni
push.** No se modificó producción (`consultorio/`, `templates/`, `static/`,
`app.py`) ni se añadieron dependencias.

## 2. Entorno

- PostgreSQL real **16.15** en Docker; `psycopg` **3.3.8**.
- `TEST_DATABASE_URL` obligatoria (D9/CL-10). Sin ella la sesión se detiene al
  inicio; no hay `skip` ni `xfail`.
- Cada test usa un esquema aislado `test_hu019_<uuid>` con `search_path` y
  `DROP SCHEMA … CASCADE`. No se escribe en `public`.

## 3. Resultados reales

| Ejecución | Comando | Resultado |
|---|---|---|
| Suite completa A | `python -m pytest -q` | **397 passed, 0 failed, 0 skipped** (183,12 s) |
| Suite completa B | `python -m pytest -q` | **397 passed, 0 failed, 0 skipped** (171,22 s) |
| Cuatro archivos T12 | `pytest tests/test_pg_schema.py tests/test_pg_persistence.py tests/test_pg_resilience.py tests/test_hu_019.py` | **77 passed** |
| Control sin TC-019-014 | el anterior con `--deselect …test_tc_019_014…` | **76 passed, 1 deselected** |
| TC-019-014 repetido | 3 ejecuciones | **1 passed** en las tres (0,93 / 1,14 / 0,64 s) |
| Esquema | `pytest tests/test_pg_schema.py` | **4 passed** |
| Persistencia + HU-019 | `pytest tests/test_pg_persistence.py tests/test_hu_019.py` | **16 passed** |
| Resiliencia T12 | `pytest tests/test_pg_resilience.py -k "tc_019_010 or tc_019_016"` | **11 passed** (10 de TC-019-010 + 1 de TC-019-016) |

La salida completa de la corrida B está en `suite-postgres.txt` (UTF-8 sin
BOM). TC-019-012 es la corrida de la suite, no una función de test.

## 4. Matriz consolidada TC → archivo → prueba → resultado

| TC | Archivo | Prueba(s) | Resultado | No vacuidad (resumen) |
|---|---|---|---|---|
| TC-019-003 | `test_pg_schema.py` | `test_tc_019_003_empty_database_creates_expected_schema` | PASS | Catálogos reales (`information_schema`, `pg_constraint`, `pg_indexes`); igualdad exacta de tablas e índices. |
| TC-019-004 | `test_pg_schema.py` | `test_tc_019_004_second_run_is_idempotent_and_keeps_data` | PASS | Dos `ensure_schema()` con instancias distintas e inserción real entre medias; preserva filas e índices. |
| TC-019-005 | `test_pg_schema.py` | `test_tc_019_005_concurrent_bootstrap_leaves_single_object_set` | PASS | Dos instancias reales con `threading.Barrier`; advisory lock y un solo juego de objetos. |
| TC-019-006 | `test_pg_persistence.py` | `test_tc_019_006_appointments_repository_contract`; `…_sql_sent_to_postgres_uses_percent_s_and_returning` | PASS | Repositorio real, `RETURNING id`, `%s`, `rowcount`, índice parcial, disponibilidad sin canceladas. |
| TC-019-007 | `test_pg_persistence.py` | `test_tc_019_007_events_repository_dedup_and_claim`; `…_claim_failed_event_retryability_patterns` | PASS | `UNIQUE(event_id)` real, dedup, `mark_sent`, `claim_failed_event` con `rowcount`. |
| TC-019-008 | `test_pg_persistence.py` | `test_tc_019_008_booking_service_maps_only_slot_uniqueness`; `…_eight_threads_create_exactly_one_booking` | PASS | Violación real con transacción bloqueante (sin mock de persistencia); indisponibilidad con DSN inalcanzable; 8 conexiones reales y `Barrier`. |
| TC-019-009 | `test_pg_persistence.py` | `test_tc_019_009_update_and_event_share_connection_and_single_commit`; `…_real_event_insert_failure_rolls_back_cancellation`; `…_publication_runs_only_after_commit` | PASS | Fallo real de `INSERT` por `UNIQUE(event_id)`; rollback durable comprobado desde conexión independiente; publicación solo tras el commit. |
| TC-019-010 | `test_pg_resilience.py` | 10 pruebas `test_tc_019_010_*` | PASS | App con PostgreSQL real y DSN inalcanzable (`127.0.0.1:1`): 503, literal, JSON, sin 409/«Ocupado»/«no existe»/«cancelada», sin PII ni DSN. |
| TC-019-011 | `test_hu_019.py` | `test_tc_019_011_persistence_unavailable_literal_and_unchanged_mirror` | PASS | Contrato textual exacto y espejo; no es una prueba de persistencia por naturaleza. |
| TC-019-012 | suite | `python -m pytest -q` | **397 passed** ×2 | Evidencia de suite real; ver `suite-postgres.txt`. |
| TC-019-013 | `test_hu_019.py` | `test_tc_019_013_slot_integrity_and_cancelled_release` | PASS | `INSERT` directo duplicado falla en el motor; cancelar libera el slot y permite re-reservar. |
| TC-019-014 | `test_hu_019.py` | `test_tc_019_014_eight_threads_one_booking_seven_slot_taken` | PASS | 8 hilos reales + `Barrier`; 1 cita, 7 `SLOT_TAKEN`, 0 excepciones, sin filas extra; sin mocks. |
| TC-019-015 | `test_hu_019.py` | `test_tc_019_015_event_dedup_single_row_without_second_send` | PASS | Dedup real con una sola fila y sin reiniciar el estado ya enviado. |
| TC-019-016 | `test_pg_resilience.py` | `test_tc_019_016_startup_tolerates_outage_and_recovers` | PASS | Arranque con DSN inalcanzable + recuperación perezosa + **cold start**: cierra la conexión recuperada y fuerza una nueva con escritura/lectura reales. |
| TC-019-017 | `test_pg_persistence.py` | `test_tc_019_017_created_at_and_sent_at_are_utc` | PASS | Comparación con reloj UTC y `America/Bogota`; formato y desfase reales. |
| TC-019-018 | `test_pg_schema.py` | `test_tc_019_018_reapply_over_data_preserves_rows_and_integrity` | PASS | Paso aditivo real sobre datos (versión 5), filas conservadas, integridad vigente e idempotencia. |

## 5. TC-019-010 — indisponibilidad (detalle)

La app se construye con `PERSISTENCE_BACKEND=postgres` y un DSN real pero
inalcanzable: `postgresql://consultorio_dev:<redactado>@127.0.0.1:1/…`
(`connect_timeout=1`). No se mockea ni el repositorio ni el servicio: la
cadena completa driver → capa de persistencia → servicio → manejador HTTP se
ejecuta de verdad y termina en `PersistenceUnavailable`.

Se comprueban las superficies HTML/JSON, la confirmación, la cancelación 017,
el admin 018, el estado del JS/plantilla y que 404/405/500 siguen funcionando.
También se comprueba que la respuesta y los logs no contienen el DSN, la
contraseña ni los datos del paciente.

## 6. TC-019-016 — arranque, recuperación y cold start (detalle)

- **Parte A:** `create_app()` con DSN inalcanzable no aborta; `GET /` responde
  200. La advertencia de arranque no contiene DSN ni usuario.
- **Parte B:** un `connect_factory` falla una vez y luego delega en PostgreSQL
  real. El primer `ensure_schema()` lanza `PersistenceUnavailable` y no crea
  objetos; el segundo crea el esquema sin reiniciar el proceso.
- **Parte C (nueva en T12):** tras la recuperación, `Database.transaction()`
  escribe una cita real y, al salir del bloque fuera de contexto Flask, la
  conexión queda cerrada (`warm_connection.closed is True`). A continuación se
  **fuerza una conexión nueva** que ejecuta `SELECT 1`, lee la cita persistida
  y se cierra al terminar. Esto cubre literalmente «cerrar conexiones y forzar
  una nueva»; el scale-to-zero real de Neon queda para T13.

## 7. No vacuidad de TC-019-014

Además de las 3 repeticiones y del control `76` vs `77`, se ejecutó una
**mutación fuera del repositorio** en un esquema temporal: se aplicó el esquema
aprobado **sin el paso 4** (índice parcial `ux_appointments_slot_open`) y se
repitió la misma carrera de 8 hilos.

```text
without partial index -> persisted rows: 8 | winners: 8 | SLOT_TAKEN: 0
```

Sin el índice real la prueba fallaría (8 ganadores en lugar de 1). Por tanto
TC-019-014 depende de la garantía del motor y no de un mock, del azar ni de una
comprobación previa. El esquema de mutación se eliminó (`t12_mutation_*`: 0
residuales).

## 8. Aislamiento y estado de `public`

Comprobado tras las dos corridas completas finales:

```text
residual_test_schemas = []
residual_mutation_schemas = []
public.appointments.rows = 0
public.automation_events.rows = 0
public.schema_migrations.rows/max = (4, 4)
```

## 9. Sin `skip`, `xfail` ni SQLite en T12

- No hay `@pytest.mark.skip` ni `xfail` nuevos en los cuatro archivos T12.
- Las pruebas de TC-019-003..018 se ejecutan contra PostgreSQL real.
- Las únicas referencias SQLite de esos archivos son: (a) `test_pg_resilience.py`
  usa clases `sqlite3.*` para verificar la traducción de errores de T3
  (TC-019-002, fuera de T12), y (b) `test_hu_019.py` conserva la prueba de la
  ruta de rollback de T5, fuera de los TC de T12. Ninguna de las dos es
  evidencia de paridad ni sustituye a PostgreSQL.

## 10. Auditoría de mocks

- **TC-019-008:** el mock de `booking.repository.is_slot_taken` (T5) se
  **eliminó en T12**; la violación ahora la produce una transacción real
  bloqueante, detectada con `pg_stat_activity`.
- **TC-019-008 (concurrencia) y TC-019-009:** los mocks restantes son de
  `automation_service`/`email_service` (evitan envíos externos y observan el
  orden). **No mockean persistencia**: las filas, transacciones, `rowcount` y
  violaciones las produce PostgreSQL.
- **TC-019-018:** `monkeypatch` solo cambia la tupla de pasos DDL en el proceso
  de test para simular una migración aditiva; el DDL se ejecuta en PostgreSQL
  real y la producción conserva sus cuatro pasos.
- Los mocks aprobados en T10/T11 de `tests/test_double_booking_service.py` no
  forman parte de T12 y no se han modificado.

## 11. Refuerzos no mecánicos de T12

1. **TC-019-014** nuevo: concurrencia real con `Barrier`, sin mocks, con
   verificación de filas, eventos del ganador y limpieza del esquema.
2. **TC-019-008**: se sustituye el mock de persistencia por una carrera real
   determinista (transacción bloqueante + poll de `pg_stat_activity`).
3. **TC-019-003/005**: igualdad exacta de tablas e índices (antes solo
   subconjunto).
4. **TC-019-018**: se añade un paso aditivo real (versión 5) con datos
   existentes y se verifica de nuevo la integridad y la idempotencia.
5. **TC-019-016**: se añade la parte C de cold start (cierre + conexión nueva
   con escritura/lectura).

## 12. Riesgos y pendientes

- T12 está **verificada pero pendiente de revisión**; no se marca completada.
- El cold start es una simulación a nivel de conexión; el scale-to-zero real,
  TLS y la latencia de Neon pertenecen a T13.
- T14 verificará el ciclo de vida del servicio web en Render.
- Sin commit ni push.
