# Spec 019 — Migración a PostgreSQL

Estado: aprobada

> **Spec de habilitador técnico, no de funcionalidad de usuario nueva.** No
> introduce pantallas, roles ni flujos nuevos: preserva el comportamiento ya
> aprobado en las Specs 004–018 y traslada el almacenamiento a una base de datos
> PostgreSQL gestionada para que los datos dejen de perderse.
>
> **Aprobada por la usuaria el 2026-11-07**; las decisiones de aprobación se
> registran en la sección «Decisiones de aprobación (2026-11-07)». `plan.md` y
> `tasks.md` **aprobados el 2026-11-08**; la implementación autorizada se limita
> por ahora a la tarea T1. Este documento no modifica
> ninguna otra spec: las enmiendas coordinadas de las Specs 004/005/006/010 se
> registran en la trazabilidad y se tramitan por separado.

## Contexto y objetivo

Hoy el consultorio persiste citas y eventos de automatización en un fichero
SQLite dentro del servicio web de Render. El sistema de archivos de ese servicio
es efímero: **cada redespliegue y cada apagado por inactividad (spin-down)
borran la base de datos**. En producción ya se perdió una reserva de prueba por
un redespliegue y la pérdida es estructural, no un accidente puntual. En un
consultorio real eso significa perder citas confirmadas, cancelaciones
registradas y trazas de notificaciones.

Mantener SQLite con un disco persistente exige pasar al servicio web de pago
(~$7.25/mes), lo que rompe el presupuesto aprobado. La evaluación técnica de
2026-11 (spike, `docs/spikes/postgresql-evaluacion-2026-11.md`) demostró que el
código actual funciona sobre PostgreSQL 16 sin cambios en la lógica de negocio:
307/307 pruebas en verde con backend PostgreSQL, índice único parcial operativo,
concurrencia con exactamente un ganador, atomicidad de la cancelación de la
Spec 010 y deduplicación de eventos por `UNIQUE(event_id)`.

**Objetivo:** que la aplicación desplegada en Render persista citas y eventos en
una base PostgreSQL gestionada, con paridad funcional y de integridad respecto
de los flujos aprobados, dentro de un coste de **$0** y con una vía de repliegue
documentada.

### Decisiones ya aprobadas por la usuaria (no se reabren en esta spec)

- **Destino:** Neon Free (plan gratuito permanente, sin tarjeta).
- **Presupuesto del MVP:** **$0**. Sin servicios de pago.
- **PII en el tier Free:** la usuaria **acepta** alojar datos personales de
  pacientes en el plan gratuito, **sin certificaciones de compliance**
  (SOC 2 / ISO / GDPR / HIPAA). Ver «Limitación asumida».
- **Sin datos reales de pacientes que migrar:** el esquema se crea desde cero;
  no hay migración de datos históricos.
- **Orden del trabajo:** esta migración se implementa **antes** de la spec de
  acceso/agenda; esa spec se redacta **después** de esta migración (la 019 ya
  está aprobada).
- **Motor objetivo:** PostgreSQL gestionado. La paridad funcional ya está
  demostrada por el spike (307/307 pruebas, índice parcial, concurrencia,
  atomicidad, deduplicación).

## Decisiones de aprobación (2026-11-07)

La usuaria aprobó esta especificación el 2026-11-07 con las siguientes
decisiones, que cierran las dudas abiertas del borrador:

1. **Fechas y horas:** `created_at` y `sent_at` se almacenan en **UTC**. La zona
   `America/Bogota` se usará solo en futuras visualizaciones, que quedan fuera
   de esta migración (RF-30).
2. **Alcance de la suite:** la suite automatizada se ejecuta **siempre contra
   PostgreSQL**. SQLite **no** es un modo de pruebas paralelo; una ejecución
   contra el almacenamiento anterior no se admite como evidencia de paridad
   (RF-28).
3. **Entorno de desarrollo y pruebas:** desarrollo y pruebas locales con
   **PostgreSQL en Docker**. La base gestionada real (Neon) se reserva para las
   pruebas extremo a extremo (E2E) (RF-29, RNF-2).
4. **Región y latencia:** la base gestionada debe estar en la **misma región**
   que el servicio de Render, a confirmar en el despliegue. El MVP **no** fija
   un umbral numérico de latencia (RNF-3).
5. **Permanencia del almacenamiento anterior:** SQLite queda como **rollback
   temporal** mediante un interruptor por entorno y se retira tras la
   aceptación de la migración. No es una alternativa permanente ni un modo de
   desarrollo (RF-18).
6. **Pérdida de datos en un rollback:** la usuaria **acepta** que las filas
   creadas en PostgreSQL después del corte no estén disponibles al volver al
   almacenamiento anterior. Antes de un rollback con datos reales debe
   realizarse un **snapshot manual en Neon** (RF-19, RNF-7, CL-6).
7. **Mensaje ante base de datos no disponible:** se aprueba para el MVP el
   literal «No pudimos completar tu solicitud en este momento. Inténtalo de
   nuevo en unos minutos.». Su introducción exige **enmienda coordinada** de la
   Spec 004 y/o la Spec 005 y el cambio simultáneo de su espejo en
   `tests/expected_content.py` en el mismo PR. Esta spec registra la decisión y
   **no** lo implementa (RF-20).

## Usuarios / actores

- Paciente: reserva, consulta disponibilidad y cancela; debe percibir el mismo
  comportamiento que hoy, sin enterarse del cambio de motor.
- Consultorio (psicóloga / administración): cancela y reprograma (Spec 018);
  depende de que las citas y sus trazas sobrevivan a los despliegues.
- Responsable técnico del proyecto: configura, despliega, opera y, si hace
  falta, repliega el almacenamiento.
- Servicio de automatización (n8n): recibe eventos; su deduplicación depende de
  la unicidad persistida del identificador de evento.

## Historias de usuario

- H1: Como responsable del consultorio quiero que las citas registradas
  sobrevivan a los redespliegues, reinicios y apagados del servicio web para no
  perder reservas reales de pacientes.
- H2: Como paciente quiero que reservar, consultar disponibilidad y cancelar
  sigan funcionando exactamente igual aunque cambie el almacenamiento, para no
  repetir operaciones ni desconfiar de la confirmación recibida.
- H3: Como responsable técnico quiero que el almacenamiento gestionado mantenga
  las garantías de integridad ya aprobadas (sin dobles reservas, sin eventos
  duplicados, cancelación atómica) para no degradar el producto al cambiar de
  motor.
- H4: Como responsable técnico quiero poder volver al almacenamiento anterior
  mediante un interruptor por entorno, con sus consecuencias documentadas, para
  disponer de una vía de repliegue temporal si la base gestionada falla.

## Definiciones

- **Almacenamiento anterior:** SQLite en el sistema de archivos efímero del
  servicio web (situación actual).
- **Base de datos gestionada:** servicio PostgreSQL operado por un proveedor
  externo; la aplicación no administra el servidor ni el sistema de archivos.
- **Paridad funcional:** para un mismo conjunto de entradas, los flujos de las
  Specs 004–018 producen las mismas respuestas observables y los mismos
  literales contractuales que hoy, salvo el literal de indisponibilidad aprobado
  en las decisiones de aprobación (RF-20).
- **Integridad en el punto de persistencia:** la garantía la impone el motor de
  base de datos (restricciones e índices), no solo las comprobaciones previas de
  la aplicación.
- **Cold start:** latencia adicional de la primera petición tras un periodo de
  inactividad de la base gestionada.
- **Rollback:** volver temporalmente a operar con el almacenamiento anterior
  mediante un interruptor por entorno, sin cambiar código.
- **Esquema:** conjunto de tablas, restricciones e índices que soportan citas y
  eventos.
- **PII:** datos personales del paciente ya aprobados en la Spec 004 (tipo y
  número de documento, nombre, correo y celular).

## Requisitos funcionales

### Persistencia y durabilidad

- RF-1: EL SISTEMA DEBE almacenar de forma persistente las citas y los eventos
  de automatización en una base de datos PostgreSQL gestionada, en lugar del
  almacenamiento efímero del servicio web.
- RF-2: CUANDO el servicio web se redespliegue, EL SISTEMA DEBE conservar y
  seguir sirviendo las citas y los eventos registrados antes del redespliegue.
- RF-3: CUANDO el servicio web se detenga por inactividad y vuelva a iniciarse,
  EL SISTEMA DEBE conservar y seguir sirviendo las citas y los eventos
  registrados antes de la detención.

### Paridad funcional con los flujos existentes

- RF-4: EL SISTEMA DEBE mantener sin cambios observables el flujo de reserva de
  la Spec 004: validación de los ocho campos, registro de la cita, estado
  inicial «Confirmada», página de confirmación y literales contractuales.
- RF-5: EL SISTEMA DEBE mantener sin cambios observables la consulta de
  disponibilidad de la Spec 005: horas libres y ocupadas para un servicio y una
  fecha, días con al menos un hueco y días sin horarios.
- RF-6: EL SISTEMA DEBE mantener sin cambios observables la protección contra
  doble reserva de la Spec 006: como máximo una cita válida por combinación de
  servicio, fecha y hora, con rechazo del resto y cero filas nuevas.
- RF-7: EL SISTEMA DEBE mantener sin cambios observables la emisión, el registro
  y el reproceso de los eventos de automatización de las Specs 007, 008 y 010:
  tipos de evento, versiones, campos obligatorios del payload, estados
  `pending` / `sent` / `skipped` / `failed`, detalles en español y ausencia de
  envíos duplicados.
- RF-8: EL SISTEMA DEBE mantener sin cambios observables la cancelación y la
  notificación de cancelación de las Specs 010 y 017: transición a «Cancelada»,
  liberación del horario, pantallas, mensajes y reintentos sin duplicar la
  notificación.
- RF-9: EL SISTEMA DEBE mantener sin cambios observables la cancelación y la
  reprogramación por el consultorio de la Spec 018: resumen previo, cancelación
  mediante el servicio centralizado, nueva reserva con las mismas reglas y
  resultados comunicados con los literales vigentes.

### Integridad en el punto de persistencia

- RF-10: EL SISTEMA DEBE impedir, en el propio motor de base de datos, que
  existan dos citas no canceladas con la misma combinación de servicio, fecha y
  hora.
- RF-11: CUANDO una cita pase a «Cancelada», EL SISTEMA DEBE liberar esa
  combinación de servicio, fecha y hora para que pueda reservarse de nuevo, sin
  permitir mientras tanto dos citas no canceladas en ella.
- RF-12: EL SISTEMA DEBE impedir, en el propio motor de base de datos, que se
  persistan dos eventos con el mismo identificador de evento, de modo que un
  evento repetido no genere una segunda fila ni un segundo envío.
- RF-13: CUANDO una cita pase a «Cancelada», EL SISTEMA DEBE confirmar la
  transición de estado y el registro del evento en estado `pending` de forma
  conjunta en una única transacción de persistencia: o ambas quedan confirmadas
  o ninguna, sin traza local sin cancelación ni cancelación sin traza.
- RF-14: SI dos o más solicitudes intentan registrar el mismo horario de forma
  simultánea, ENTONCES EL SISTEMA DEBE registrar como máximo una cita y
  rechazar las demás con el comportamiento y el literal ya aprobados en las
  Specs 004 y 006.

### Configuración, credenciales y conexiones

- RF-15: EL SISTEMA DEBE obtener del entorno la ubicación de la base de datos y
  sus credenciales, de modo que ningún secreto ni cadena de conexión con
  contraseña quede en el repositorio, la documentación ni las pruebas.
- RF-16: EL SISTEMA DEBE comunicarse con la base de datos gestionada
  exclusivamente mediante una conexión cifrada (TLS).
- RF-17: MIENTRAS el servicio web atiende peticiones, EL SISTEMA DEBE reutilizar
  las conexiones y liberarlas al terminar cada operación, de modo que no supere
  el límite de conexiones del proveedor ni lo agote.

### Rollback al almacenamiento anterior

- RF-18: CUANDO el interruptor de entorno active el almacenamiento anterior, EL
  SISTEMA DEBE operar con él sin cambios de código y con las mismas reglas de
  negocio e integridad. Ese rollback es temporal y se retira tras la aceptación
  de la migración; no es una alternativa permanente ni un modo de pruebas.
- RF-19: EL SISTEMA no trasladará automáticamente al almacenamiento anterior las
  filas registradas en PostgreSQL tras el cambio de motor; la selección del
  almacenamiento determina qué datos resultan visibles. La pérdida de las filas
  creadas después del corte está aceptada por la usuaria.

### Comportamiento ante indisponibilidad de la base de datos

- RF-20: SI la base de datos no está disponible o no responde, ENTONCES EL
  SISTEMA no registrará la cita, no mostrará una confirmación de reserva y
  comunicará al paciente el literal de indisponibilidad aprobado para el MVP
  («No pudimos completar tu solicitud en este momento. Inténtalo de nuevo en
  unos minutos.»). La incorporación de ese literal al contrato de contenido de
  las Specs 004 y/o 005 y su espejo en `tests/expected_content.py` se realiza
  mediante enmienda coordinada; esta spec registra la decisión y no modifica ese
  contrato.
- RF-21: SI la base de datos no está disponible, ENTONCES EL SISTEMA no
  presentará el fallo como un horario ocupado, como una cita inexistente ni como
  una cita cancelada.
- RF-22: SI la base de datos no está disponible durante el arranque, ENTONCES EL
  SISTEMA DEBE iniciarse y seguir sirviendo las secciones que no requieren
  persistencia; el proceso no debe terminar ni requerir un reinicio manual para
  recuperarse cuando la base vuelva a estar disponible.
- RF-23: CUANDO la base de datos vuelva a estar disponible, EL SISTEMA DEBE
  reanudar la reserva y la consulta de disponibilidad sin intervención manual.

### Creación y evolución del esquema

- RF-24: CUANDO el sistema arranque contra una base de datos vacía, EL SISTEMA
  DEBE crear el esquema completo —tablas, restricciones e índices— sin
  intervención manual.
- RF-25: CUANDO el sistema arranque contra una base de datos que ya contiene el
  esquema, la creación o actualización DEBE ser idempotente: sin duplicar
  objetos, sin eliminar datos existentes y sin fallar por objetos ya presentes.
- RF-26: CUANDO se aplique un cambio de esquema sobre una base con datos, EL
  SISTEMA DEBE preservar los datos existentes y las garantías de integridad, sin
  pasos manuales no documentados.
- RF-27: EL SISTEMA DEBE crear y evolucionar el esquema sin un ORM, conforme a la
  restricción de la constitución del proyecto (#1).

### Desarrollo y pruebas

- RF-28: EL SISTEMA DEBE disponer de una suite automatizada que se ejecute
  siempre contra PostgreSQL y valide los criterios de aceptación de las Specs
  004–018. SQLite no es un modo de pruebas paralelo: una ejecución únicamente
  contra el almacenamiento anterior no se considerará evidencia de paridad.
- RF-29: EL SISTEMA DEBE soportar el desarrollo y las pruebas locales contra
  PostgreSQL en un contenedor, sin depender de la base gestionada real; la base
  gestionada se reserva para las pruebas extremo a extremo (E2E).

### Fechas y horas

- RF-30: EL SISTEMA DEBE almacenar en UTC las marcas de tiempo `created_at` y
  `sent_at` de citas y eventos; la zona `America/Bogota` se usará solo para
  presentarlas en futuras visualizaciones.

## Requisitos no funcionales

- RNF-1 — **Coste $0**: la solución debe operar con planes gratuitos, sin
  tarjeta y sin complementos de pago. Verificación: revisión de la facturación y
  de los planes activos del proveedor; ningún recurso en plan de pago.
- RNF-2 — **Encaje en los límites de Neon Free**: 1 GB por proyecto, 100
  CU-hours por proyecto/mes, 5 GB de transferencia pública por proyecto/mes,
  scale-to-zero a los 5 minutos de inactividad y restauración de 6 horas. El
  desarrollo y las pruebas locales se ejecutan contra PostgreSQL en contenedor
  (RF-29), de modo que la cuota del plan gratuito no se consume en el trabajo
  diario; la base gestionada se reserva para las pruebas E2E. Verificación:
  consumo observado en la consola del proveedor dentro de esos valores en
  operación normal, y comportamiento documentado al agotarlos (ver casos límite
  CL-1 y CL-3).
- RNF-3 — **Compatibilidad de ejecución**: debe funcionar en Python 3.12.7 y en
  el despliegue actual de Render, con la base gestionada en la **misma región**
  que el servicio web (a confirmar en el despliegue). El MVP no fija un umbral
  numérico de latencia. Verificación: despliegue real en Render con un flujo
  completo de reserva y región configurada coincidente.
- RNF-4 — **Cold start asumido**: la primera petición tras un periodo de
  inactividad puede tardar más; la consulta de disponibilidad y la reserva no
  deben fallar por ello. Verificación: tras más de 5 minutos sin tráfico, una
  consulta de disponibilidad y una reserva completas terminan con éxito.
- RNF-5 — **Sin regresiones funcionales**: la suite automatizada y los criterios
  de aceptación de las Specs 004–018 siguen cumpliéndose. Verificación: suite
  completa en verde contra PostgreSQL, con 0 fallos, y sin cambios en los
  literales contractuales vigentes; el literal nuevo de indisponibilidad entra
  por la enmienda coordinada de las Specs 004/005 (decisión de aprobación 7).
- RNF-6 — **Seguridad y minimización**: TLS obligatorio, credenciales solo por
  entorno, PII limitada a los campos ya aprobados en la Spec 004 y ausencia de
  PII en registros de aplicación y en la documentación. Verificación: revisión
  de la configuración desplegada, del repositorio y de los artefactos de
  evidencia.
- RNF-7 — **Documentación operativa**: la configuración, el despliegue, la
  operación y el rollback deben quedar documentados y ser reproducibles por otra
  persona. El procedimiento de rollback debe incluir un **snapshot manual en
  Neon** antes de un rollback con datos reales y la constancia de que las filas
  posteriores al corte se pierden. Verificación: revisión de la documentación
  generada contra un despliegue real.
- RNF-8 — **Dependencias mínimas**: solo las estrictamente necesarias para el
  acceso a PostgreSQL, con justificación escrita y aprobación previa (constitución
  #1).

## Limitación asumida — PII en el plan gratuito

La usuaria **acepta explícitamente** (decisión de 2026-11-07) alojar datos
personales de pacientes en el plan gratuito de la base gestionada, que **no
ofrece certificaciones de compliance** (SOC 2 / ISO / GDPR / HIPAA). Se
documenta como limitación asumida del MVP y **debe revisarse antes de operar con
datos reales de pacientes en producción**, con su propia decisión y su propia
spec. Esta spec no resuelve compliance, cifrado en reposo gestionado, acuerdos de
tratamiento de datos ni planes de pago.

## Casos límite

- CL-1 **Cuota de CU-hours o de transferencia agotada** (compute suspendido):
  la base deja de responder; se aplica RF-20 y RF-21; el paciente ve un error
  comprensible y no una confirmación; la recuperación exige intervención
  documentada y no reiniciar el servicio.
- CL-2 **Base de datos dormida o inalcanzable durante el arranque o durante una
  reserva**: la primera petición puede tardar por el cold start (RNF-4); si no
  responde, se aplica RF-20, RF-21, RF-22 y RF-23.
- CL-3 **Cuota de 1 GB de almacenamiento alcanzada**: las escrituras fallan; el
  sistema no confirma la reserva (RF-20) y el caso queda documentado para
  operación.
- CL-4 **Inicialización del esquema sobre una base vacía y sobre una base que ya
  lo contiene**: creación completa en el primer caso e idempotencia estricta en
  el segundo (RF-24, RF-25).
- CL-5 **Cambio de esquema con datos existentes**: debe preservar los datos y las
  garantías de integridad (RF-26), incluida la unicidad de `servicio + fecha +
  hora` entre citas no canceladas.
- CL-6 **Rollback al almacenamiento anterior**: las filas creadas en PostgreSQL
  después del corte no estarán disponibles y no se trasladan (RF-19); la pérdida
  está **aceptada por la usuaria** (decisión de aprobación 6) y, con datos
  reales, el procedimiento exige un snapshot manual en Neon antes del rollback.
- CL-7 **Dos instancias arrancando a la vez sobre una base vacía**: la creación
  del esquema no debe fallar ni duplicar objetos (RF-25).
- CL-8 **Peticiones concurrentes al mismo horario**: como máximo una reserva
  válida, con el resto rechazadas y sin excepción no controlada (RF-14).
- CL-9 **Alta concurrencia de peticiones**: la gestión de conexiones no debe
  agotar el límite del proveedor ni bloquear el servicio (RF-17).
- CL-10 **Entorno local sin red o sin base de datos disponible**: la reserva y la
  disponibilidad no funcionan; el desarrollo y la suite se ejecutan contra
  PostgreSQL en contenedor (RF-29) y, sin base disponible, la suite no se ejecuta
  y no produce evidencia.
- CL-11 **Límite de conexiones del proveedor alcanzado**: el sistema no debe
  presentar la falta de conexión como un conflicto de horario (RF-17, RF-21).

## Fuera de alcance

- Spec de acceso/agenda (roles, sesión, CSRF, auditoría de usuario) y las Specs
  011/012: se redactan después de esta migración (spec ya aprobada).
- Certificación de compliance, acuerdos de tratamiento de datos, planes de pago,
  alta disponibilidad, réplica y multi-región.
- Migración de datos históricos desde SQLite (no hay datos reales de pacientes).
- Backups, retención y restauración automatizados más allá de lo que ofrece el
  plan gratuito del proveedor; el snapshot manual previo a un rollback con datos
  reales (RNF-7) es una operación puntual, no un sistema de backups.
- Cambios de UX/UI; solo se admite el comportamiento de error estrictamente
  necesario para los casos límite de indisponibilidad.
- Reintentos automáticos de reservas, colas o workers.
- Elección de frameworks, ORM o herramientas de migración (corresponde a
  `plan.md`), salvo la restricción de no usar ORM.

## Criterios de finalización

- [ ] La aplicación desplegada en Render persiste citas y eventos en la base
      gestionada.
- [ ] Las citas y los eventos sobreviven a un redespliegue y a un spin-down
      (verificado con datos creados antes del evento).
- [ ] La suite automatizada pasa contra PostgreSQL y no hay regresiones en los
      flujos de las Specs 004–018 ni cambios no aprobados en literales
      contractuales.
- [ ] Las garantías de integridad se verifican contra el motor real: unicidad de
      horario entre citas no canceladas, liberación tras cancelar, unicidad de
      identificador de evento, deduplicación y atomicidad de la cancelación.
- [ ] El comportamiento ante base indisponible está verificado (sin confirmación
      falsa, sin confundirlo con horario ocupado y con el literal de
      indisponibilidad aprobado, incorporado mediante la enmienda coordinada de
      las Specs 004 y/o 005 y su espejo en `tests/expected_content.py`).
- [ ] El rollback al almacenamiento anterior está probado y documentado, con la
      pérdida de filas aceptada y el snapshot manual en Neon antes de un rollback
      con datos reales.
- [ ] La documentación de configuración, despliegue y operación está actualizada.
- [ ] Tras la aceptación, el interruptor de rollback y el almacenamiento anterior
      se retiran.
- [ ] Aceptación funcional de la usuaria.

## Dudas abiertas

Ninguna pendiente: las siete dudas del borrador quedaron resueltas por las
decisiones de aprobación de 2026-11-07.

## Trazabilidad con las specs 004–018

Ninguna de estas specs se modifica en este documento. Se indica el impacto y si
requiere **enmienda coordinada**.

| Spec | RF afectados | Impacto de la migración | ¿Enmienda coordinada? |
|---|---|---|---|
| 004 — Agendar cita | RF-1, RF-3, RF-4 | El alta y la confirmación deben comportarse igual sobre el nuevo motor. Se añade el literal de indisponibilidad de persistencia (RF-20). | **Sí**: incorporar el literal aprobado en «Decisiones de aprobación» y su espejo en `tests/expected_content.py` en el mismo PR. |
| 005 — Validar disponibilidad | RF-1, RF-2, RF-5 | La disponibilidad depende de la unicidad y de la liberación de horarios; la consulta también puede fallar por indisponibilidad de persistencia y usa el mismo literal (RF-20). | **Sí**: incorporar el mismo literal y su espejo, coordinado con la Spec 004. |
| 006 — Evitar doble reserva | RF-2, RF-3, RF-6 | La garantía ya no puede describirse como un índice `UNIQUE` de tabla simple: debe reflejar la unicidad entre citas **no canceladas** garantizada por el motor. | **Sí**: «Contrato de datos» menciona un índice `UNIQUE (service, date, time)`; debe alinearse con la Spec 010 y esta spec. |
| 007 — Automatización de reservas | RF-1, RF-4, RF-5 | Depende de la unicidad del identificador de evento y de la preservación de eventos entre despliegues. | No en la spec (solo plan y tests). |
| 008 — Correo de confirmación | RF-1, RF-4 | Depende de la deduplicación persistida del evento de correo. | No. |
| 010 — Servicio centralizado de cancelación | RF-5, RF-6, RF-8, RF-11, RF-12, RF-13, RF-15 | La atomicidad de la transición a «Cancelada» y del registro `pending` debe mantenerse sobre el nuevo motor; el texto menciona explícitamente la transacción de persistencia de **SQLite**. | **Sí**: RF-11 y su contrato («transacción de persistencia de SQLite») deben expresarse con independencia del motor, sin relajar garantías. |
| 017 — Cancelar cita por el paciente | RF-5, RF-6, RF-8, RF-9 | Su cancelación se apoya en la Spec 010; sin cambios de contrato ni de literales. | No. |
| 018 — Cancelar y reprogramar por el consultorio | RF-3, RF-4, RF-6 | La reprogramación combina cancelación y nueva reserva; depende de la integridad y de la atomicidad. | No en la spec. **Nota de secuencia**: su implementación fue mergeada **localmente** a `main` en `8ce511f` (2026-11-07, sin push); la migración y su suite deben cubrir también ese código (cancelar y reprogramar). |

Observaciones de trazabilidad adicionales:

- Las menciones a SQLite en `plan.md` de las Specs 004, 005, 006, 007 y 010
  quedan superadas por esta migración y deberán actualizarse en sus propios
  planes **cuando se planifique esta migración** (la spec ya está aprobada); no
  se tocan aquí.
- `tests/expected_content.py` actúa como espejo de literales: esta spec **no
  cambia ningún literal contractual existente** ni modifica ese archivo. El
  literal nuevo de indisponibilidad (decisión de aprobación 7) se introduce
  mediante enmienda coordinada de las Specs 004 y/o 005 y su espejo, en el mismo
  PR; esta spec solo registra la decisión.

## Referencias

- Spike: `docs/spikes/postgresql-evaluacion-2026-11.md` (§11 comparativa, §12
  recomendación y secuencia).
- `docs/constitution.md` (#1 sin ORM ni dependencias sin aprobación, #5
  integridad en persistencia).
- `AGENTS.md` («Base de datos e integridad», «Git y control de cambios»).
