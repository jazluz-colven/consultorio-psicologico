# Tareas 019 — Migración a PostgreSQL/Neon

> Trazabilidad: **Spec 019 (`specs/019_migrar-postgresql/spec.md`) → `plan.md` →
> este `tasks.md` → código → tests → evidencia → commit**
> Constitución: `docs/constitution.md` (#1 sin ORM ni dependencias sin
> justificación y aprobación; #5 integridad en el punto de persistencia).
>
> **Estado: Aprobado por la usuaria el 2026-11-08.**
>
> La Spec 019 fue aprobada por la usuaria el 2026-11-07. Las enmiendas
> coordinadas 004/005/006/010 fueron aprobadas el 2026-11-08. El plan y estas
> tareas fueron aprobados el 2026-11-08. **Solo T1 está autorizada**; las demás
> requieren autorización expresa y revisión tras cada tarea.

## Control de autorización

- **T1 completada y revisada (2026-11-09); T2 autorizada (2026-11-09).** Las
  tareas T3–T18 están planificadas y **no autorizadas**; cada una lleva la marca
  **[NO AUTORIZADA]**.
- La implementación de una tarea exige: (1) aprobación explícita de `plan.md`
  y `tasks.md`; (2) autorización expresa de la fase o entrega correspondiente;
  (3) que la tarea anterior de la que depende esté cerrada con evidencia.
- **T18 [NO AUTORIZADA — REQUIERE ACEPTACIÓN]** solo puede ejecutarse después de
  la aceptación funcional de la usuaria y de la autorización de retirada del
  rollback.
- No se marca una tarea como terminada por inspección del código. Cada cierre
  exige pruebas ejecutadas, resultado real y evidencia (AGENTS.md).
- No se modifican requisitos, literales, tarifas ni alcance sin actualizar
  primero la Spec 019 y sus enmiendas coordinadas.

## Fases

| Fase | Tareas | Contenido |
|---|---|---|
| A — Núcleo | T1–T9 | Docker/dev, dependencia/config, conexiones, DDL, repositorios, servicios, atomicidad, literal y errores/UX |
| B — Validación y despliegue | T10–T14 | Migración de la suite, pruebas nuevas, E2E Neon y Render |
| C — Cierre | T15–T18 | Rollback, actualización de planes, QA/aceptación y retirada del rollback |

> El alcance supera diez tareas. Se recomienda autorizar y revisar por fases
> (Entrega A, B y C) para no convertir la migración en un bloque monolítico.
> Las tareas T5, T10, T11 y T12 pueden subdividirse durante la implementación si
> la usuaria lo autoriza.

---

## Fase A — Núcleo de la migración

- [x] **T1. Preparar PostgreSQL 16 local en Docker y la documentación operativa inicial. [AUTORIZADA 2026-11-08]**
  - **Objetivo:** disponer de un PostgreSQL 16 reproducible en local para
    desarrollo y pruebas, sin secretos reales, y dejar documentado el
    procedimiento.
  - **Cubre:** RF-29; RNF-2, RNF-7; CL-10.
  - **Depende de:** —.
  - **Archivos previstos:** `docs/operaciones/postgresql.md` (nuevo);
    `docs/evidencias/hu-019/setup-local.md` (nuevo).
  - **Criterios de aceptación:**
    - El documento contiene un comando `docker run` reproducible con
      `postgres:16-alpine`, puerto local (por ejemplo `55432`), base y usuario
      de desarrollo, y una contraseña local de usar y tirar que **no** es un
      secreto real.
    - `SELECT version()` devuelve una versión 16.x.
    - El documento explica que la suite exige `TEST_DATABASE_URL` y que sin
      PostgreSQL la suite falla explícitamente (no se salta).
    - No se añaden credenciales de Neon, Render ni datos de pacientes.
  - **Pruebas:** comprobación manual E-019-01: `docker ps` muestra el
    contenedor y `docker exec ... psql -c "SELECT version();"` responde 16.x.
  - **Evidencia:** salida de `docker ps` y de `SELECT version()` en
    `setup-local.md`, sin contraseña.
  - **Hecho cuando:** el contenedor responde y el documento permite a otra
    persona repetir el entorno sin consultar al autor.

- [x] **T2. Añadir la dependencia `psycopg` y la configuración por entorno. [COMPLETADA 2026-11-09 — APROBADA POR REVISOR]**
  - **Objetivo:** incorporar el driver aprobado y leer/validar la configuración
    de PostgreSQL sin secretos en el repositorio.
  - **Cubre:** RF-15, RF-16, RF-17; RNF-1, RNF-6, RNF-8.
  - **Depende de:** T1.
  - **Archivos previstos:** `requirements.txt`, `consultorio/config.py`,
    `docs/operaciones/postgresql.md`.
  - **Criterios de aceptación:**
    - `requirements.txt` incluye `psycopg[binary]==3.3.8` (versión fijada).
    - `Config` expone `DATABASE_URL`, `PERSISTENCE_BACKEND`,
      `DATABASE_PATH` (solo rollback), `DATABASE_MAX_CONNECTIONS`,
      `DATABASE_CONNECT_TIMEOUT`, `DATABASE_ACQUIRE_TIMEOUT` y
      `DATABASE_STATEMENT_TIMEOUT_MS`.
    - En host no local, un DSN sin `sslmode=require`/`verify-ca`/`verify-full`
      produce un error de configuración; en local se admite
      `sslmode=disable`.
    - Un `PERSISTENCE_BACKEND` distinto de `postgres`/`sqlite` falla al
      arrancar con un mensaje claro.
    - Si falta `DATABASE_URL`, la aplicación no cae al arrancar; las rutas de
      persistencia quedan en indisponibilidad (RF-22).
    - Ningún DSN con contraseña aparece en el repositorio, la documentación ni
      los tests.
  - **Pruebas:** TC-019-001.
  - **Evidencia:** salida de `python -c "import psycopg; print(psycopg.__version__)"`
    (3.3.8), verificación de los binarios 16.15-5 (tamaño `373254386`, SHA-256
    oficial coincidente y `NotSigned` aceptado por A1), conexión real y
    TC-019-001; DSN redactado.
  - **Hecho cuando:** TC-019-001 PASS y la configuración no filtra secretos.
  - **Decisión A1 (2026-11-09):** la usuaria aceptó los binarios oficiales de
    EDB sin firma Authenticode, verificados por el SHA-256 oficial, y el uso de
    PostgreSQL 16.15-5 en local. Verificación real: zip de `373254386` bytes,
    SHA-256 `43bb45f1…ccaa8281` coincidente, `libpq.dll` `FileVersion 16.15` y
    `NotSigned`; conexión real correcta contra el servidor PostgreSQL 16.15.
    T2 queda **implementada y verificada con A1**, pendiente del cierre formal
    del coordinador.

- [x] **T3. Implementar la capa de conexiones y errores de dominio. [COMPLETADA 2026-11-09 — APROBADA POR REVISOR]**
  - **Objetivo:** abrir, reutilizar y cerrar conexiones por petición/operación,
    limitar la concurrencia y traducir errores del driver a errores de dominio.
  - **Cubre:** RF-17, RF-22, RF-23; CL-9, CL-11.
  - **Depende de:** T2.
  - **Archivos previstos:** `consultorio/persistence/database.py`,
    `consultorio/persistence/__init__.py`, `consultorio/config.py`,
    `consultorio/__init__.py`.
  - **Criterios de aceptación:**
    - Existen `DatabaseTarget` y `Database` con `connection()`, `transaction()`
      y `ensure_schema()`.
    - Una petición web reutiliza como máximo una conexión y la cierra al
      terminar; no hay conexiones globales por worker ni al importar módulos.
    - Un `BoundedSemaphore` limita las conexiones a
      `DATABASE_MAX_CONNECTIONS`; el timeout de adquisición produce
      `PersistenceUnavailable`.
    - `OperationalError`, `InterfaceError`, timeout de conexión y límite de
      conexiones se traducen a `PersistenceUnavailable`.
    - No se registran DSN, contraseñas ni datos de pacientes en logs.
  - **Pruebas:** TC-019-002.
  - **Evidencia:** salida de TC-019-002 y conteo de conexiones observado.
  - **Hecho cuando:** TC-019-002 PASS; no queda ninguna conexión global.

- [x] **T4. Crear el DDL idempotente, el bloqueo de arranque y la inicialización perezosa. [COMPLETADA 2026-11-09 — APROBADA POR REVISOR]**
  - **Objetivo:** crear y evolucionar el esquema PostgreSQL sin ORM, de forma
    idempotente y segura ante dos instancias, tolerando el arranque sin BD.
  - **Cubre:** RF-22, RF-23, RF-24, RF-25, RF-26, RF-27; CL-4, CL-5, CL-7.
  - **Depende de:** T3.
  - **Archivos previstos:** `consultorio/persistence/database.py`,
    `consultorio/__init__.py`, `docs/operaciones/postgresql.md`.
  - **Criterios de aceptación:**
    - Una BD vacía crea `appointments`, `automation_events`,
      `UNIQUE(event_id)`, el índice parcial
      `ux_appointments_slot_open (service, date, time) WHERE status <> 'cancelled'`
      y `schema_migrations`.
    - Una segunda ejecución no duplica objetos ni borra datos.
    - Dos instancias concurrentes sobre una BD vacía terminan sin error y
      dejan un solo juego de objetos (advisory lock + `IF NOT EXISTS`).
    - `create_app()` no aborta si la BD no está disponible; las páginas sin
      persistencia siguen respondiendo.
    - `ensure_schema()` reintenta de forma perezosa y recupera la operación
      cuando la BD vuelve, sin reinicio manual.
    - El DDL SQLite de rollback se conserva y sigue siendo idempotente.
  - **Pruebas:** TC-019-003, TC-019-004, TC-019-005, TC-019-016, TC-019-018.
  - **Evidencia:** consultas a `pg_indexes`/`information_schema` y salida de
    los TC en `docs/evidencias/hu-019/schema.md`.
  - **Hecho cuando:** los TC PASS y los catálogos reales muestran el esquema
    esperado.

- [x] **T5. Adaptar los repositorios de citas y eventos al dialecto PostgreSQL. [COMPLETADA Y APROBADA por @revisor 2026-11-09 — 378 PASS; autorizada por la usuaria]**
  - **Objetivo:** ejecutar el SQL de citas y eventos sobre PostgreSQL sin ORM,
    conservando las garantías de integridad y los contratos de datos.
  - **Cubre:** RF-4, RF-6, RF-7, RF-10, RF-11, RF-12, RF-14, RF-30; CL-8.
  - **Depende de:** T4.
  - **Archivos previstos:**
    `consultorio/persistence/appointments_repository.py`,
    `consultorio/persistence/automation_events_repository.py`.
  - **Criterios de aceptación:**
    - El SQL usa `%s`, `INSERT ... RETURNING id`, `rowcount` y acceso por
      nombre (`dict_row` o equivalente).
    - `insert_appointment()` devuelve el `Appointment` con el id real.
    - El índice parcial impide dos citas no canceladas en el mismo
      `(service, date, time)`; una cita cancelada libera el horario.
    - `automation_events.event_id` es único; el segundo `insert_event()`
      devuelve `False` y no crea fila.
    - `mark_sent()` escribe `sent_at` en UTC; `created_at` se lee en UTC.
    - `claim_failed_event()` conserva la transición atómica y `rowcount`.
    - Los repositorios no contienen reglas de negocio ni mensajes de usuario.
  - **Pruebas:** TC-019-006, TC-019-007, TC-019-013, TC-019-015, TC-019-017.
  - **Evidencia:** salida de los TC y consultas de catálogo.
  - **Hecho cuando:** los TC PASS y no queda SQL incompatible con PostgreSQL
    en estos repositorios.

- [x] **T6. Adaptar los servicios de reserva y disponibilidad y el mapeo de errores. [COMPLETADA Y APROBADA por @revisor 2026-11-10 — 382 PASS; autorizada por la usuaria]**
  - **Objetivo:** conservar las reglas de reserva/disponibilidad y distinguir
    conflicto de horario de indisponibilidad de la base.
  - **Cubre:** RF-4, RF-5, RF-6, RF-14, RF-20, RF-21; CL-8.
  - **Depende de:** T5.
  - **Archivos previstos:** `consultorio/services/appointment_service.py`,
    `consultorio/services/cancellation_flow_service.py`,
    `consultorio/web/appointments.py`, `consultorio/web/cancellation.py`,
    `consultorio/web/admin.py`.
  - **Criterios de aceptación:**
    - `create_booking()` mapea únicamente la violación de unicidad del slot a
      `SLOT_TAKEN`; `PersistenceUnavailable` **no** se convierte en
      `SLOT_TAKEN`.
    - `get_hours_with_status()` y `get_available_days()` conservan su
      contrato y excluyen `cancelled`.
    - La concurrencia de 8 hilos sobre el mismo slot produce exactamente una
      cita y el resto `SLOT_TAKEN`.
    - Las firmas de negocio y los sentinelas existentes se conservan; el
      cambio es el objeto de persistencia.
    - No quedan imports de `sqlite3` en los servicios.
  - **Pruebas:** TC-019-008.
  - **Evidencia:** salida de TC-019-008 y prueba de concurrencia.
  - **Hecho cuando:** TC-019-008 PASS y no hay `except sqlite3.OperationalError`
    en los servicios.

- [x] **T7. Preservar la atomicidad de la cancelación de la Spec 010 en 017/018. [COMPLETADA Y APROBADA por @revisor 2026-11-10 — 385 PASS; autorizada por la usuaria]**
  - **Objetivo:** confirmar la transición a `cancelled` y el evento `pending`
    en una sola transacción, con publicación posterior al commit.
  - **Cubre:** RF-8, RF-9, RF-13.
  - **Depende de:** T5, T6.
  - **Archivos previstos:**
    `consultorio/persistence/appointments_repository.py`,
    `consultorio/services/appointment_service.py`,
    `consultorio/services/cancellation_flow_service.py`,
    `tests/test_cancellation_service.py`, `tests/test_hu_018.py`.
  - **Criterios de aceptación:**
    - `update_appointment_status_with_pending_event()` usa la misma conexión y
      la misma transacción para el `UPDATE` y el `INSERT` del evento.
    - Si el `INSERT` del evento falla, se hace rollback y la cita sigue
      `confirmed`; no queda evento huérfano.
    - El commit es único; la publicación del evento de negocio y el correo
      ocurren después del commit.
    - Los flujos 017 (paciente) y 018 (consultorio) siguen delegando en el
      servicio centralizado, sin lógica de persistencia propia.
  - **Pruebas:** TC-019-009 y regresión de `test_cancellation_service.py` y
    `test_hu_018.py`.
  - **Evidencia:** salida de TC-019-009 y volcado de `appointments.status` y
    `automation_events` tras el fallo simulado.
  - **Hecho cuando:** TC-019-009 PASS y los flujos 017/018 no presentan
    regresiones.

- [x] **T8. Implementar el literal coordinado `MSG_PERSISTENCE_UNAVAILABLE`. [COMPLETADA Y APROBADA por @revisor 2026-11-10 — 386 PASS; autorizada por la usuaria]**
  - **Objetivo:** añadir la constante contractual y su espejo exacto, sin
    cambiar otros literales.
  - **Cubre:** RF-20; RNF-5.
  - **Depende de:** T2.
  - **Archivos previstos:** `consultorio/content/appointment_content.py`,
    `tests/expected_content.py`, `tests/test_appointment_content.py` o
    `tests/test_hu_019.py`.
  - **Criterios de aceptación:**
    - `MSG_PERSISTENCE_UNAVAILABLE` vale exactamente «No pudimos completar tu solicitud en este momento. Inténtalo de nuevo en unos minutos.».
    - El espejo en `tests/expected_content.py` es idéntico.
    - Las referencias a las Specs 004/005 (enmienda aprobada el 2026-11-08)
      quedan trazadas.
    - No se modifica ningún otro literal contractual.
  - **Pruebas:** TC-019-011.
  - **Evidencia:** salida de TC-019-011 y diff de los dos archivos.
  - **Hecho cuando:** TC-019-011 PASS y el espejo coincide exactamente.

- [x] **T9. Añadir el manejo HTTP/UX mínimo de indisponibilidad de persistencia. [COMPLETADA, APROBADA por @revisor Y ACEPTADA por la usuaria 2026-11-10 — 396 PASS]**
  - **Objetivo:** comunicar la indisponibilidad con el literal aprobado y sin
    confundirla con un conflicto de horario, una cita inexistente o una cita
    cancelada.
  - **Cubre:** RF-20, RF-21; RNF-6; CL-1, CL-2, CL-3, CL-11.
  - **Depende de:** T8, T3, T6.
  - **Archivos previstos:** `consultorio/errors.py`,
    `templates/errors/persistence_unavailable.html` (nuevo),
    `static/js/availability.js`, `templates/appointments/index.html` (solo si
    hace falta un atributo de estado), `docs/operaciones/postgresql.md`.
  - **Criterios de aceptación:**
    - Una petición HTML con `PersistenceUnavailable` responde **503** con el
      literal aprobado y un enlace de vuelta a `/citas`.
    - `/citas/horarios` y `/citas/disponibilidad` responden **503** con
      `{"error": MSG_PERSISTENCE_UNAVAILABLE}`.
    - `POST /citas` no muestra confirmación; no devuelve 409 ni «Ocupado».
    - La confirmación, la cancelación y el admin no presentan el fallo como
      cita inexistente, cancelada u ocupada.
    - `availability.js` no marca horas como «Ocupado» ante 503; muestra el
      estado de indisponibilidad.
    - La pantalla usa la paleta y la tipografía vigentes; no se añaden colores
      ni copy nuevos.
    - La pantalla 503 solo muestra el literal aprobado
      `MSG_PERSISTENCE_UNAVAILABLE`; si el enlace de vuelta necesita etiqueta,
      reutiliza un literal contractual ya existente (por ejemplo
      `ADMIN_BACK_BUTTON` = «Volver») o no introduce texto nuevo. Queda
      **prohibido crear copy adicional**.
    - Los logs no contienen DSN, contraseña ni PII.
  - **Pruebas:** TC-019-010.
  - **Evidencia:** salida de TC-019-010 y captura de la pantalla 503 si se
    valida visualmente.
  - **Hecho cuando:** TC-019-010 PASS y ninguna superficie confunde
    indisponibilidad con negocio.

---

## Fase B — Validación y despliegue

- [x] **T10. Migrar las fixtures y los tests de persistencia a PostgreSQL. [COMPLETADA Y APROBADA por @revisor 2026-11-10 — T10 18 PASS; suite 372/24, fallos de T11]**
  - **Objetivo:** hacer que la suite use siempre PostgreSQL, con esquema
    aislado por test y sin accesos directos a SQLite.
  - **Cubre:** RF-28, RF-29; RNF-5; CL-10.
  - **Depende de:** T4, T5, T8, T9.
  - **Archivos previstos:** `tests/conftest.py`,
    `tests/test_appointment_persistence.py`, `tests/test_hu_006.py`,
    `tests/test_hu_007.py`, `tests/test_hu_010.py`,
    `tests/test_rollback_sqlite.py` (nuevo: reubicación de `TC-010-014`).
  - **Criterios de aceptación:**
    - `TEST_DATABASE_URL` es obligatoria; si falta o no responde, la sesión de
      pytest falla al inicio con instrucciones, sin `skip`.
    - Cada test usa un esquema aislado (`test_<uuid>`) con `search_path` y
      limpieza posterior.
    - Los tests de esquema consultan `pg_indexes`, `pg_index` e
      `information_schema`, no `sqlite_master` ni `PRAGMA`.
    - `test_hu_010` conserva sus criterios restantes de la Spec 010 y la
      idempotencia PostgreSQL. La prueba de migración del esquema legado SQLite
      (`TC-010-014`) **no se elimina ni se sustituye**: se reubica a
      `tests/test_rollback_sqlite.py`, manteniendo la cobertura de respaldo,
      idempotencia y aborto ante duplicados; se ejecutará y registrará aparte
      como verificación de rollback en T15, no como evidencia de paridad.
    - No quedan `sqlite3.connect` directos en los archivos de la suite de
      paridad.
  - **Pruebas:** TC-019-003, TC-019-004, TC-019-005, TC-019-006, TC-019-007,
    TC-019-012 (parcial).
  - **Evidencia:** primera salida de `python -m pytest -q` contra PostgreSQL en
    `docs/evidencias/hu-019/suite-postgres.txt`.
  - **Hecho cuando:** estos archivos pasan contra PostgreSQL, la falta de BD
    produce un fallo explícito y `TC-010-014` queda reubicado en
    `tests/test_rollback_sqlite.py` sin pérdida de cobertura.

- [x] **T11. Migrar los tests de servicios, rutas y HU, y ejecutar la suite completa. [COMPLETADA Y APROBADA por @revisor 2026-11-11 — 396 PASS / 0 FAIL / 0 skipped]**
  - **Objetivo:** cubrir los flujos 004–018 contra PostgreSQL, incluidos los 18
    tests de HU-018, sin relajar aserciones.
  - **Cubre:** RF-4..RF-9, RF-28; RNF-5; CL-10.
  - **Depende de:** T10.
  - **Archivos previstos:** `tests/test_double_booking_service.py`,
    `tests/test_cancellation_service.py`, `tests/test_availability_service.py`,
    `tests/test_appointment_service.py`, `tests/test_appointment_routes.py`,
    `tests/test_double_booking_routes.py`, `tests/test_availability_routes.py`,
    `tests/test_hu_018.py` y los demás tests que usen `database_path`.
  - **Criterios de aceptación:**
    - Todos los criterios de las Specs 004–018, incluidos los 18 casos de
      HU-018, se ejecutan contra PostgreSQL.
    - `python -m pytest -q` termina con **0 FAIL** y sin `skip` que oculte
      falta de BD.
    - No se elimina ni se relaja ninguna aserción para pasar.
    - No quedan accesos directos a SQLite en la suite de paridad.
    - El baseline es 320 PASS / 0 FAIL en SQLite, pero el conteo final puede
      variar por la reubicación de `TC-010-014` a
      `tests/test_rollback_sqlite.py` y por renombrados; se registra el
      **número real verificado**, sin declarar cifras no ejecutadas.
  - **Pruebas:** TC-019-012.
  - **Evidencia:** `docs/evidencias/hu-019/suite-postgres.txt` actualizado con
    la corrida completa.
  - **Hecho cuando:** la suite completa contra PostgreSQL termina con 0 FAIL,
    cubre los criterios de las Specs 004–018 y se reporta el número real
    verificado.

- [x] **T12. Añadir las pruebas nuevas de integridad, concurrencia, atomicidad, cold start y errores. [COMPLETADA Y APROBADA por @revisor 2026-11-11 — 397 PASS / 0 FAIL / 0 skipped]**
  - **Objetivo:** demostrar con pruebas no vacuas las garantías nuevas y los
    casos límite de la Spec 019.
  - **Cubre:** RF-10..RF-14, RF-20..RF-23, RF-30; CL-1..CL-5, CL-7..CL-11
    (CL-6 se verifica en T15 con TC-019-021).
  - **Depende de:** T10, T11.
  - **Archivos previstos:** `tests/test_pg_schema.py`,
    `tests/test_pg_persistence.py`, `tests/test_pg_resilience.py`,
    `tests/test_hu_019.py`.
  - **Criterios de aceptación:**
    - Se cubren TC-019-003 a TC-019-018.
    - Las pruebas de esquema leen catálogos reales; las de concurrencia usan
      conexiones reales y `Barrier`; la atomicidad provoca un fallo real; la
      indisponibilidad usa un DSN inalcanzable o timeout corto.
    - El cold start se simula cerrando conexiones y forzando una nueva; el
      scale-to-zero real se reserva para T13.
    - No hay tests vacíos, emulados o que pasen sin ejercitar PostgreSQL.
  - **Pruebas:** TC-019-003..TC-019-018.
  - **Evidencia:** salida de los TC y notas de no vacuidad en
    `docs/evidencias/hu-019/schema.md` y `resilience.md`.
  - **Hecho cuando:** todos los TC nuevos PASS y la revisión de no vacuidad
    queda registrada.

- [x] **T13. Ejecutar el E2E contra Neon desde un entorno controlado. [COMPLETADA Y APROBADA por @revisor 2026-11-12 — E2E con endpoint directo; TLS, esquema, reserva, eventos y cold start PASS; pooler con `statement_timeout` bloquea T14]**
  - **Hallazgo 2026-11-12:** el endpoint pooler rechaza `options=-c statement_timeout=...`; `ensure_schema` vía pooler queda sin verificar y requiere decisión antes de T14.
  - **Objetivo:** verificar contra la base gestionada real, sin desplegar el
    servicio web, la conexión TLS, la creación del esquema, una reserva con sus
    eventos y el cold start tras inactividad/scale-to-zero.
  - **Cubre:** RF-1; RNF-2, RNF-4.
  - **Depende de:** T12.
  - **Archivos previstos:** `docs/operaciones/postgresql.md`,
    `docs/evidencias/hu-019/e2e-neon.md`.
  - **Criterios de aceptación:**
    - Proyecto/base Neon Free en la región acordada, conectada exclusivamente
      con TLS desde el entorno controlado (sin depender del servicio Render).
    - El esquema se crea en Neon sin pasos manuales y coincide con el DDL
      aprobado.
    - Una reserva completa y sus eventos quedan persistidos y visibles en Neon.
    - Tras más de 5 minutos de inactividad (scale-to-zero), la primera consulta
      de disponibilidad y una reserva completa terminan con éxito: la base
      despierta sin fallo por cold start.
    - **No** incluye redespliegue ni spin-down del servicio web; esas
      verificaciones pertenecen a T14.
    - El procedimiento es reproducible y no contiene DSN, contraseña ni PII en
      el repositorio.
    - Se documenta cualquier límite o comportamiento no verificado.
  - **Pruebas:** TC-019-019.
  - **Evidencia:** `docs/evidencias/hu-019/e2e-neon.md` con pasos y resultados
    reales de TLS, esquema, reserva + eventos y cold start/scale-to-zero.
  - **Hecho cuando:** TLS, esquema, reserva + eventos y cold start quedan
    verificados contra Neon o, si no se pueden verificar, se registran como NO
    VERIFICADO sin declarar PASS.

- [ ] **T14. Desplegar en Render con Neon y verificar la persistencia. [NO AUTORIZADA]**
  - **Objetivo:** dejar la aplicación desplegada con `DATABASE_URL` secreta,
    región coincidente y backend PostgreSQL, y verificar que las citas y eventos
    persisten tras un redespliegue y tras un spin-down del servicio web.
  - **Cubre:** RF-1, RF-2, RF-3, RF-15; RNF-1, RNF-3, RNF-6, RNF-7.
  - **Depende de:** T13.
  - **Decisión 2026-11-12 (T13):** `DATABASE_URL` en Render debe apuntar al
    **endpoint directo** de Neon (sin `-pooler`); el pooler rechaza
    `options=-c statement_timeout=...`. No se modifica el código ni TLS.
  - **Archivos previstos:** `render.yaml`, `docs/operaciones/postgresql.md`,
    `docs/evidencias/hu-019/render-deploy.md`.
  - **Criterios de aceptación:**
    - `render.yaml` declara `DATABASE_URL` con `sync: false`,
      `PERSISTENCE_BACKEND=postgres` y no contiene `DATABASE_PATH` ni secretos.
    - La región de Neon coincide con la del servicio de Render y se documenta.
    - El despliegue arranca, el esquema se crea en Neon y una reserva completa
      funciona.
    - La cita y sus eventos persisten tras un **redespliegue** del servicio web.
    - La cita y sus eventos persisten tras un **spin-down** del servicio web, y
      la primera petición al volver a iniciarse termina con éxito.
    - No se duplica el cold start de Neon de T13: aquí se verifica el ciclo de
      vida del servicio web, no el despertar de la base.
    - No hay recursos de pago ni credenciales en el repositorio.
    - Se documenta la verificación de Python 3.12.7 y de `psycopg` en Render.
  - **Pruebas:** TC-019-020.
  - **Evidencia:** `docs/evidencias/hu-019/render-deploy.md` con variables
    redactadas, región, horas, redespliegue, spin-down y resultados.
  - **Hecho cuando:** la persistencia tras redespliegue y spin-down del servicio
    web en Render queda verificada y documentada.

---

## Fase C — Cierre

- [ ] **T15. Documentar y probar el rollback temporal a SQLite. [NO AUTORIZADA]**
  - **Objetivo:** disponer de una vía de repliegue reproducible, con pérdida de
    filas aceptada y snapshot manual documentado.
  - **Cubre:** RF-18, RF-19; RNF-7; CL-6.
  - **Depende de:** T14.
  - **Archivos previstos:** `docs/operaciones/postgresql.md`,
    `docs/evidencias/hu-019/rollback.md`, `tests/test_rollback_sqlite.py`
    (obligatorio: reubicación de `TC-010-014`, fuera de la suite de paridad).
  - **Criterios de aceptación:**
    - `PERSISTENCE_BACKEND=sqlite` + `DATABASE_PATH` permite operar sin cambios
      de código.
    - Se documenta que las filas creadas en PostgreSQL después del corte no se
      trasladan y se pierden; la pérdida está aceptada por la usuaria.
    - Antes de un rollback con datos reales se exige un snapshot manual en
      Neon y se registra la hora del corte.
    - Se verifica la vuelta a PostgreSQL y que las filas SQLite del periodo de
      rollback no se trasladan.
    - `TC-010-014` (respaldo, idempotencia y aborto ante duplicados del esquema
      SQLite legado) **sigue ejecutándose** en `tests/test_rollback_sqlite.py`
      como verificación de la ruta SQLite de rollback; su cobertura se conserva
      íntegra y su resultado se registra **aparte** de la suite de paridad.
    - La prueba de rollback se identifica como verificación de rollback, no
      como evidencia de paridad (RF-28).
  - **Pruebas:** TC-019-021 (incluye la ejecución de `TC-010-014`).
  - **Evidencia:** `docs/evidencias/hu-019/rollback.md`, con el resultado de
    `TC-010-014` registrado en una sección separada de la evidencia de paridad.
  - **Hecho cuando:** el rollback se ejecuta y documenta con el resultado real,
    incluida la pérdida aceptada y el resultado de `TC-010-014`.

- [ ] **T16. Actualizar las menciones a SQLite en los planes 004/005/006/007/010. [NO AUTORIZADA]**
  - **Objetivo:** alinear la documentación técnica anterior con la migración,
    sin cambiar requisitos ni literales aprobados.
  - **Cubre:** RNF-7; trazabilidad de la Spec 019.
  - **Depende de:** T9, T14.
  - **Archivos previstos:** `specs/004_agendar-cita/plan.md`,
    `specs/005_validar-dis-horarios/plan.md`,
    `specs/006_evitar-doble-reserva/plan.md`,
    `specs/007_automatizacion-reservas/plan.md`,
    `specs/010_notificar-cancelacion/plan.md`,
    `docs/evidencias/hu-019/plan-updates.md`.
  - **Criterios de aceptación:**
    - Las menciones a `DATABASE_PATH`, `sqlite3`, `sqlite_master`, `PRAGMA`,
      `busy_timeout` y «transacción de SQLite» se sustituyen por la capa de
      persistencia/PostgreSQL o por una redacción independiente del motor.
    - Se conservan las notas históricas de enmiendas y las decisiones ya
      aprobadas.
    - No se cambia ningún requisito, criterio ni literal.
    - Cada cambio queda trazado a la Spec 019.
  - **Pruebas:** TC-019-022 (revisión documental).
  - **Evidencia:** diff de los planes y `plan-updates.md`.
  - **Hecho cuando:** no quedan afirmaciones obsoletas que contradigan la
    migración y la revisión documental queda registrada.

- [ ] **T17. Ejecutar QA, reunir evidencias y solicitar la aceptación. [NO AUTORIZADA]**
  - **Objetivo:** cerrar la validación con resultados reales y solicitar la
    aceptación funcional de la usuaria.
  - **Cubre:** RNF-5, RNF-7.
  - **Depende de:** T15, T16.
  - **Archivos previstos:** `docs/evidencias/hu-019/qa-hu-019.md`,
    `docs/evidencias/hu-019/suite-postgres.txt`,
    `docs/evidencias/hu-019/e2e-neon.md`,
    `docs/evidencias/hu-019/render-deploy.md`,
    `docs/evidencias/hu-019/rollback.md`, capturas si aplica.
  - **Criterios de aceptación:**
    - Informe con PASS/FAIL por TC, comandos ejecutados, resultados reales y
      regresiones revisadas.
    - Se distingue PASS, FAIL y NO VERIFICADO; no se declara PASS por
      inspección del código.
    - El checkbox de aceptación queda **sin marcar** hasta la decisión de la
      usuaria.
    - No hay secretos, DSN ni PII en las evidencias.
    - Si se generan capturas, usan CDP y la paleta vigente.
  - **Pruebas:** TC-019-023.
  - **Evidencia:** `docs/evidencias/hu-019/qa-hu-019.md`.
  - **Hecho cuando:** el informe está completo y la aceptación se solicita
    formalmente; no se declara aprobado.

- [ ] **T18. Retirar el rollback y el almacenamiento anterior tras la aceptación. [NO AUTORIZADA — REQUIERE ACEPTACIÓN]**
  - **Objetivo:** eliminar el interruptor y la ruta SQLite cuando la migración
    haya sido aceptada, dejando una sola vía de persistencia.
  - **Cubre:** RF-18; RNF-7.
  - **Depende de:** T17 y aceptación funcional explícita de la usuaria.
  - **Archivos previstos:** `consultorio/config.py`,
    `consultorio/persistence/database.py`, `render.yaml`,
    `docs/operaciones/postgresql.md`, tests de rollback.
  - **Criterios de aceptación:**
    - Se retiran `PERSISTENCE_BACKEND`, `DATABASE_PATH`, el DDL SQLite, la
      prueba de rollback y la documentación de rollback.
    - No queda código muerto ni configuración ambigua.
    - La suite sigue ejecutándose contra PostgreSQL con 0 FAIL.
    - La documentación operativa describe solo PostgreSQL.
  - **Pruebas:** TC-019-024.
  - **Evidencia:** diff de retirada y corrida final de la suite.
  - **Hecho cuando:** la usuaria aceptó la migración, la retirada está
    autorizada y la suite final pasa sin la ruta SQLite.

---

## Resumen de tareas y requisitos

| Tarea | Título | RF/RNF/CL principales |
|---|---|---|
| T1 | PostgreSQL local en Docker y documentación inicial | RF-29; RNF-2, RNF-7; CL-10 |
| T2 | Dependencia `psycopg` y configuración por entorno | RF-15, RF-16, RF-17; RNF-1, RNF-6, RNF-8 |
| T3 | Capa de conexiones y errores de dominio | RF-17, RF-22, RF-23; CL-9, CL-11 |
| T4 | DDL idempotente, bloqueo y arranque perezoso | RF-22..RF-27; CL-4, CL-5, CL-7 |
| T5 | Repositorios de citas y eventos | RF-4, RF-6, RF-7, RF-10..RF-12, RF-14, RF-30; CL-8 |
| T6 | Servicios de reserva/disponibilidad y errores | RF-4, RF-5, RF-6, RF-14, RF-20, RF-21; CL-8 |
| T7 | Atomicidad de cancelación 010/017/018 | RF-8, RF-9, RF-13 |
| T8 | Literal coordinado `MSG_PERSISTENCE_UNAVAILABLE` | RF-20; RNF-5 |
| T9 | Errores HTTP/UX de indisponibilidad | RF-20, RF-21; RNF-6; CL-1..CL-3, CL-11 |
| T10 | Fixtures y tests de persistencia en PostgreSQL | RF-28, RF-29; RNF-5; CL-10 |
| T11 | Tests de servicios/rutas/HU y suite completa | RF-4..RF-9, RF-28; RNF-5; CL-10 |
| T12 | Pruebas nuevas de integridad, concurrencia y resiliencia | RF-10..RF-14, RF-20..RF-23, RF-30; CL-1..CL-11 |
| T13 | E2E contra Neon desde entorno controlado | RF-1; RNF-2, RNF-4 |
| T14 | Despliegue en Render y persistencia | RF-1..RF-3, RF-15; RNF-1, RNF-3, RNF-6, RNF-7 |
| T15 | Rollback documentado y probado (incluye `TC-010-014` reubicada) | RF-18, RF-19; RNF-7; CL-6 |
| T16 | Actualización de planes 004/005/006/007/010 | RNF-7; trazabilidad |
| T17 | QA, evidencias y solicitud de aceptación | RNF-5, RNF-7 |
| T18 | Retirada del rollback tras aceptación | RF-18; RNF-7 |

## Tareas explícitamente fuera de la implementación autorizada

El plan y estas tareas fueron aprobados el 2026-11-08. **T1 está completada;
solo T2 está autorizada**; T3–T18 permanecen fuera de la implementación
autorizada. La autorización de una tarea no autoriza automáticamente las
siguientes ni una entrega completa. **T18** requiere además la aceptación
funcional de la migración y una autorización específica de retirada del
rollback.
