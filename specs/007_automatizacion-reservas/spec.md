# Spec 007 — Automatización de reservas mediante n8n

> **Enmienda 2026-10-23 — APROBADA por la usuaria (2026-10-23):**
> se añaden RF-8..RF-13 **[PENDIENTE DE IMPLEMENTACIÓN]** y la sección
> «Contratos fijados — borrado de Google Calendar (enmienda 2026-10-23)» para
> fijar el contrato de consumo del evento de negocio `appointment.cancelled`
> (Spec 010) y el borrado del evento de Google Calendar a cargo de n8n.
> RF-1..RF-7 y los contratos de la enmienda 2026-10-10 quedan **intactos**.
> El identificador `007` y la ruta `specs/007_automatizacion-reservas/` **no
> cambian**. Alcance completo en «Nota de enmienda 2026-10-23» (final del
> documento). Esta enmienda fija **contrato documental**: no se ha modificado
> `plan.md`, tareas, código ni tests.

## Contexto y objetivo
Después de confirmar una reserva existen tareas administrativas que pueden requerir seguimiento y coordinación manual. Esta funcionalidad busca automatizar procesos posteriores a una reserva confirmada para reducir trabajo repetitivo y mejorar la continuidad del seguimiento, sin convertir la automatización en una condición necesaria para que la reserva sea válida.

## Usuarios / actores
- Administrador del consultorio.
- Sistema de reservas.
- Servicios de automatización posteriores a la reserva.

## Historias de usuario
- H1: Como administrador del consultorio quiero automatizar mediante n8n los procesos posteriores a una reserva confirmada para reducir tareas manuales y mejorar el seguimiento administrativo de las citas.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO una reserva sea confirmada, EL SISTEMA generará un evento estructurado para iniciar las automatizaciones posteriores definidas.
- RF-2: SI el servicio de automatización no está disponible temporalmente, ENTONCES EL SISTEMA mantendrá válida la reserva.
- RF-3: CUANDO se genere un evento de reserva, EL SISTEMA enviará únicamente los datos necesarios para la automatización y permitirá identificar la versión del evento.
- RF-4: SI ocurre un error, timeout o respuesta no válida durante la automatización, ENTONCES EL SISTEMA registrará la incidencia sin invalidar la reserva.
- RF-5: SI una misma reserva vuelve a procesarse, ENTONCES EL SISTEMA evitará generar automatizaciones duplicadas.
- RF-6: CUANDO exista un evento válido, EL SISTEMA permitirá ejecutar las automatizaciones administrativas configuradas.
- RF-7: EL SISTEMA mantendrá las funcionalidades de agendamiento, disponibilidad y protección contra doble reserva operativas independientemente de la automatización.

### Requisitos nuevos — borrado de Google Calendar (enmienda 2026-10-23) — [PENDIENTE DE IMPLEMENTACIÓN]

> La cancelación de citas pasa por el servicio centralizado de la Spec 010, que
> (tras su enmienda aprobada el 2026-10-23) emitirá el evento de negocio
> `appointment.cancelled` (RF-8..RF-10 de la 010, aún pendientes de
> implementación). Estos requisitos definen el **contrato de consumo** de ese
> evento en el flujo de n8n de la Spec 007. La implementación (data table en
> n8n, workflow y, en su caso, backend) requerirá plan, tareas y PRs
> posteriores con sus propias aprobaciones: la Spec 007 no implementa la
> emisión del evento de la Spec 010, solo define cómo consume su resultado.

- RF-8 [PENDIENTE DE IMPLEMENTACIÓN]: CUANDO el flujo de automatización reciba el evento de negocio `appointment.cancelled` emitido por el backend al confirmarse la cancelación de una cita (Spec 010), EL SISTEMA identificará la cita original mediante su `appointment_id`, recuperará el `calendar_event_id` guardado en el registro de creación correspondiente y eliminará el evento asociado de Google Calendar, registrando el resultado del borrado para trazabilidad.
- RF-9 [PENDIENTE DE IMPLEMENTACIÓN]: EL SISTEMA conservará, en el registro de creación del data table, tanto `appointment_id` como `calendar_event_id`, y localizará el evento de Google Calendar mediante esa correspondencia (búsqueda por `appointment_id`); el `event_id` de un evento de cancelación o de correo (p. ej. `appointment.cancelled:{id}:v1` o `appointment.cancellation_email:{id}:v1`) no servirá para localizar directamente el evento de Google Calendar.
- RF-10 [PENDIENTE DE IMPLEMENTACIÓN]: SI un reintento del borrado detecta que el evento de Google Calendar ya fue eliminado, ENTONCES EL SISTEMA reconocerá esa situación como borrado ya completado y no la tratará como una nueva eliminación exitosa susceptible de repetirse indefinidamente.
- RF-11 [PENDIENTE DE IMPLEMENTACIÓN]: SI una cita cancelada no tiene un `calendar_event_id` asociado (p. ej. creada antes de que el flujo guardara el ID) o su `appointment_id` no tiene fila de creación registrada, ENTONCES EL SISTEMA registrará el caso y lo gestionará de forma controlada, sin registrar ni dar por hecho que el evento de Google Calendar fue eliminado.
- RF-12 [PENDIENTE DE IMPLEMENTACIÓN]: EL SISTEMA registrará el estado del procesamiento de la cancelación (borrado de Google Calendar) de manera separada del estado histórico de creación y del estado del correo de cancelación, manteniendo tres estados independientes y no fusionados.
- RF-13 [PENDIENTE DE IMPLEMENTACIÓN]: EL SISTEMA distinguirá el evento de negocio `appointment.cancelled` («la cita fue cancelada», Spec 010) de la acción técnica `appointment.cancellation_email` («enviar correo de cancelación», Spec 010): serán dos eventos distintos con `event_id` distintos, y el borrado de Google Calendar se activará únicamente por el evento de negocio.

## Requisitos no funcionales
- Seguridad y minimización de datos compartidos.
- Tolerancia a indisponibilidad temporal del servicio de automatización.
- Trazabilidad de errores y eventos.
- Consistencia ante reintentos y duplicados.

## Casos límite
- Servicio de automatización no disponible.
- Timeout.
- Respuesta no válida.
- Reintento del mismo evento.
- Evento duplicado.
- Datos incompletos o no permitidos en el evento.
- Cita cancelada sin `calendar_event_id` registrado (creada antes de que el flujo guardara el ID): el caso se registra y se gestiona de forma controlada, sin dar por hecho el borrado (RF-11).
- `appointment_id` sin fila de creación en el data table (cita desconocida para el flujo de creación): no hay `calendar_event_id` recuperable; el caso se registra y se gestiona de forma controlada (RF-11).
- Evento de Google Calendar ya eliminado cuando llega un reintento del borrado: se reconoce como completada, sin una nueva eliminación (RF-10).

## Fuera de alcance
- Automatizaciones que cancelen o modifiquen una reserva sin una regla de negocio aprobada.
- Cancelar o modificar una reserva desde n8n: la cancelación la confirma el backend mediante el servicio centralizado de la Spec 010; la Spec 007 solo reacciona al evento de negocio ya confirmado (borrado del evento de Google Calendar), sin revertir ni provocar cancelaciones.
- Convertir la automatización en requisito para confirmar una cita.
- Notificaciones específicas de correo o WhatsApp que pertenezcan a otras historias.
- Persistir `calendar_event_id` en el backend: corresponde a n8n, que lo guarda por su cuenta en su data table (decisión de la usuaria 2026-10-23).
- Implementación del borrado de Google Calendar (data table en n8n, workflow y, en su caso, la emisión backend de `appointment.cancelled` — RF-8..RF-10 de la Spec 010): requiere plan, tareas y aprobaciones posteriores; esta enmienda fija solo el contrato documental.

## Criterios de finalización
- RF-1..RF-7 (enmienda 2026-10-10): todos con test en verde, incluyendo indisponibilidad, errores, reintentos y duplicados, más demo manual de una automatización posterior a una reserva confirmada — ya cumplidos con HU-007 (aceptada y cerrada el 2026-10-10).
- RF-8..RF-13 [PENDIENTE DE IMPLEMENTACIÓN] (enmienda 2026-10-23, aprobada por la usuaria): se considerarán al cerrar su implementación (plan, tareas, tests, evidencia y aceptación). Hasta entonces esta spec queda con esos RF abiertos; la implementación del borrado de Google Calendar exige, además de esta enmienda aprobada, la autorización explícita de la fase de planificación.

## Dudas abiertas (CERRADAS por enmienda 2026-10-10)
- ~~[NECESITA ACLARACIÓN] Definir cuáles serán las automatizaciones administrativas incluidas en el primer incremento.~~ → **CERRADA (Q1)**: webhook genérico `appointment.confirmed` hacia n8n; los flujos concretos se configuran en n8n (§Contratos fijados).
- ~~[NECESITA ACLARACIÓN] Confirmar qué datos son estrictamente necesarios para cada automatización.~~ → **CERRADA (Q2)**: payload mínimo **sin datos personales** (§Contratos fijados).

## Contratos fijados (enmienda 2026-10-10, aprobada por la usuaria)

Estos textos son contrato (AGENTS.md «Textos contractuales»); cambian junto con los
tests en el mismo PR.

### Interpretación de «reserva confirmada» (RF-1)
Alta exitosa de la cita: el INSERT se confirma y se responde con la página
`/citas/confirmada/<id>`. El estado de negocio de la cita sigue siendo `pending`;
la spec no introduce un nuevo estado.

### Evento (RF-1, RF-3)
- `event_type`: `appointment.confirmed` (único tipo del primer incremento, Q1).
- `event_version`: entero, inicia en **1**; cualquier cambio de forma del payload
  eleva la versión y el `event_id` asociado.
- `event_id` (RF-5): determinista,
  `appointment.confirmed:{appointment.id}:v{event_version}`.
- Payload en `application/json`, allowlist estricta — **sin datos personales**
  (Q2), sólo:

```json
{
  "event_id": "appointment.confirmed:34:v1",
  "event_type": "appointment.confirmed",
  "event_version": 1,
  "occurred_at": "2026-10-10 12:34:56",
  "appointment": {
    "id": 34,
    "service": "individual",
    "date": "2026-10-15",
    "time": "10:00",
    "status": "pending"
  }
}
```

Quedan excluidos `patient_name`, `email`, `phone`, `document_type`,
`document_number` y `created_at` de la cita (RNF minimización).

### Envío (RF-2, RF-4, RF-6)
- POST síncrono best-effort con la stdlib (`urllib.request`) **después** de que la
  reserva esté persistida, con timeout configurable (3 s por defecto), **1 intento**
  y **sin reintentos automáticos** (Q5): la re-ejecución la decide el
  administrador/n8n.
- URL por variable de entorno `AUTOMATION_WEBHOOK_URL`; vacía por defecto =
  automatización deshabilitada (evento registrado como `skipped`, nunca un error).
- **Cabecera de autenticación opcional** (enmienda 2, 2026-10-10): variable de
  entorno `AUTOMATION_WEBHOOK_AUTH_HEADER` con formato `Nombre: valor` (p. ej.
  `X-HU007-Token: <token>`); vacía por defecto = POST sin cabecera extra. El
  valor se envía tal cual. El token es un **secreto de entorno**: no se almacena
  en el repositorio, la documentación ni los tests (allí solo valores falsos).
- Éxito = HTTP 2xx. `URLError`, timeout, respuesta no-2xx o cualquier excepción se
  registran como incidencia y **en ningún caso invalidan la reserva**.

### Registro e idempotencia (RF-4, RF-5)
Tabla `automation_events` con `UNIQUE (event_id)` en el punto de persistencia:
- `status`: `pending` → `sent` | `skipped` | `failed` (identificadores en inglés).
- `detail` en español: `Automatización no configurada.` ·
  `Servicio de automatización no disponible.` ·
  `Tiempo de espera agotado (timeout).` ·
  `Respuesta no válida del servicio (HTTP {code}).` ·
  `Error inesperado durante la automatización.`
- El reproceso de una misma reserva choca en el `UNIQUE` y se descarta **antes** de
  reenviar: nunca dos automatizaciones duplicadas.

> Nota de trazabilidad: el backlog histórico v2.0 identificaba HU-007 como cancelación de cita; la actualización posterior del mismo documento redefine HU-007 como automatización mediante n8n. Esta especificación toma la definición más reciente como vigente.
>
> Nota de enmienda: el 2026-10-10 se cerraron las dos dudas [NECESITA ACLARACIÓN]
> y se fijaron los contratos anteriores con aprobación expresa de la usuaria; el
> diseño técnico correspondiente está en `specs/007_automatizacion-reservas/plan.md`.

## Contratos fijados — borrado de Google Calendar (enmienda 2026-10-23, aprobada por la usuaria)

Fija el contrato operativo aprobado por la usuaria (2026-10-23) para el
borrado del evento de Google Calendar cuando una cita se cancela. Estos
textos son contrato (AGENTS.md «Textos contractuales»); cambian junto con sus
pruebas en el mismo PR cuando se implementen. **Esta sección describe
contrato, no implementación**: no hay plan, tareas ni tests todavía, y la
emisión del evento `appointment.cancelled` depende de los RF-8..RF-10 de la
Spec 010, aún [PENDIENTE DE IMPLEMENTACIÓN].

### Flujo backend → n8n (RF-8)
1. **Backend (Spec 010)** confirma la cancelación de la cita (transición a
   Cancelada confirmada en persistencia y liberación del horario) y emite el
   evento de negocio `appointment.cancelled` (v1) al webhook de automatización
   (`AUTOMATION_WEBHOOK_URL`, con `AUTOMATION_WEBHOOK_AUTH_HEADER` si existe).
   La emisión de ese evento es responsabilidad de la Spec 010 (RF-8..RF-10,
   pendientes de implementación); la Spec 007 no la implementa, solo define el
   contrato de consumo.
2. **n8n (Spec 007)** recibe `appointment.cancelled`, identifica la cita
   original por `appointment_id`, recupera el `calendar_event_id` guardado en
   su data table y elimina el evento de Google Calendar correspondiente.
3. **Notificación y trazabilidad**: el resultado del borrado se registra, y
   los reintentos no repiten acciones ya completadas (idempotencia).

### Data table de n8n — conservar `appointment_id` y `calendar_event_id` (RF-9)
- La fila de creación (creada al procesar el evento `appointment.confirmed`
  de HU-007) debe conservar `appointment_id` y `calendar_event_id`.
- Decisión de la usuaria (2026-10-23): el `calendar_event_id` lo guarda y
  gestiona **n8n por su cuenta en su data table**; el backend **no persiste**
  `calendar_event_id`.

### Búsqueda del evento de Google Calendar (RF-9, RF-13)
- La búsqueda debe identificar el **registro original de creación**, NO el
  evento de correo ni el evento de cancelación.
- El `event_id` de cancelación (p. ej. `appointment.cancelled:{id}:v1`) o de
  correo (`appointment.cancellation_email:{id}:v1`) **NO sirve** para localizar
  directamente el evento de Google Calendar: el evento de cancelación puede
  tener un `event_id` distinto del evento original de creación.
- n8n debe buscar por **`appointment_id`** (identificador de la cita) y usar
  el `calendar_event_id` previamente almacenado en la fila de creación.

### Idempotencia de reintentos (RF-10)
- Los reintentos deben ser **idempotentes**: si el evento ya fue eliminado,
  n8n debe reconocer esa situación y no tratarla como una nueva eliminación
  exitosa que deba repetirse indefinidamente.

### Ausencia controlada de `calendar_event_id` (RF-11)
- Si no existe un `calendar_event_id` asociado (p. ej. cita antigua creada
  antes de que el flujo guardara el ID, o `appointment_id` sin fila de
  creación), el caso se debe **registrar y gestionar de forma controlada**,
  sin fingir que el evento fue eliminado.

### Estados separados: creación, cancelación y correo (RF-12)
- El estado del procesamiento de la cancelación en n8n debe **distinguirse**
  del estado histórico de creación y del estado del correo: **tres estados
  separados, no uno fusionado**.

### Distinción de eventos: negocio frente a acción técnica (RF-13)
- **Evento de negocio**: `appointment.cancelled` (Spec 010) — «la cita fue
  cancelada». Es el que activa el borrado de Google Calendar.
- **Acción técnica**: `appointment.cancellation_email` (Spec 010) — «enviar
  correo de cancelación». Es un **evento distinto** con `event_id` distinto y
  no activa el borrado por sí mismo.

### Alcance de esta enmienda
- **Contrato documental**: la implementación (data table en n8n, workflow y,
  en su caso, backend) requerirá plan, tareas y PRs posteriores con sus
  propias aprobaciones.
- La emisión del evento `appointment.cancelled` depende de los RF-8..RF-10 de
  la Spec 010, aún pendientes de implementación: la Spec 007 no los
  implementa, solo define el contrato de consumo.
- Orden de trabajo del ciclo acordado: 010 (hecho) → referencias 017/018
  (hecho) → 007 (esta enmienda); la implementación del borrado en Google
  Calendar queda para después.

## Nota de enmienda 2026-10-23

Enmienda redactada por el planificador, revisada por el coordinador y
**aprobada por la usuaria el 2026-10-23**. No se ha modificado `plan.md`,
tareas, código ni tests. El identificador `007` y la ruta
`specs/007_automatizacion-reservas/` no cambian.

**Alcance del cambio:**

1. **RF-8..RF-13 nuevos, marcados [PENDIENTE DE IMPLEMENTACIÓN]**: contrato de
   consumo del evento de negocio `appointment.cancelled` y borrado del evento
   de Google Calendar por n8n — RF-8 (flujo de borrado tras recibir el evento),
   RF-9 (fila de creación con `appointment_id` + `calendar_event_id` y búsqueda
   por `appointment_id`, nunca por el `event_id` de cancelación/correo),
   RF-10 (idempotencia de reintentos), RF-11 (ausencia controlada de
   `calendar_event_id`), RF-12 (tres estados separados: creación, cancelación
   y correo) y RF-13 (distinción entre evento de negocio y acción técnica de
   correo).
2. **Nueva sección «Contratos fijados — borrado de Google Calendar»** con el
   detalle operativo: flujo backend→n8n, conservación de `appointment_id` +
   `calendar_event_id` en la fila de creación, búsqueda por `appointment_id`,
   idempotencia, ausencia controlada del ID y separación de estados.
3. **Actualizaciones de apoyo**: «Casos límite» (cita sin
   `calendar_event_id`, `appointment_id` desconocido/sin fila de creación,
   evento ya eliminado en un reintento), «Fuera de alcance» (n8n no cancela
   reservas; el backend no persiste `calendar_event_id`; la implementación
   requiere plan y aprobaciones posteriores) y «Criterios de finalización»
   (RF-1..RF-7 ya cumplidos con HU-007; RF-8..RF-13 abiertos).
4. **Sin cambios en lo existente**: RF-1..RF-7 y los «Contratos fijados
   (enmienda 2026-10-10, aprobada por la usuaria)» quedan intactos, sin
   relajar garantías.

**Decisiones de la usuaria reflejadas (sin cambios):** flujo Backend (Spec
010) → n8n (Spec 007) → notificación y trazabilidad; la fila de creación en el
data table de n8n conserva `appointment_id` y `calendar_event_id`; la búsqueda
identifica el registro original de creación (nunca por el `event_id` del
evento de cancelación); reintentos idempotentes; ausencia controlada de
`calendar_event_id`; tres estados separados (creación, cancelación, correo);
distinción entre `appointment.cancelled` (evento de negocio) y
`appointment.cancellation_email` (acción técnica). El backend **no persiste**
`calendar_event_id` (decisión de la usuaria 2026-10-23); n8n lo guarda por su
cuenta en su data table.

**Consecuencias pendientes:** la emisión de `appointment.cancelled`
(RF-8..RF-10 de la Spec 010) requerirá su propia autorización de planificación,
y la implementación del borrado de Google Calendar bajo esta Spec 007
requerirá plan, tareas y PRs posteriores con sus propias aprobaciones.
