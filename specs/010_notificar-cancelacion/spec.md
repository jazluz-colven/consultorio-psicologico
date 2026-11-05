# Spec 010 — Servicio centralizado de cancelación y notificación de citas

> **Enmienda 2026-10-23 — APROBADA por la usuaria (2026-10-23):**
> título ampliado a «Servicio centralizado de cancelación y notificación de
> citas» (el identificador `010` y la ruta `specs/010_notificar-cancelacion/`
> **no cambian**). Los identificadores RF-1..RF-4 se conservan; los
> comportamientos que solo estaban descritos en «Contratos fijados (enmienda
> 2026-10-13)» se consolidan como RF-5..RF-7; y se añaden RF-8..RF-10
> **[IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]** para el evento de negocio
> `appointment.cancelled`. Alcance completo en «Nota de enmienda 2026-10-23»
> (final del documento).

> **Enmienda 2 (2026-10-23) — APROBADA por la usuaria (2026-10-23):**
> precisiones aprobadas por la usuaria sobre el evento de negocio
> `appointment.cancelled`: (1) contrato de reproceso del evento fallido
> mediante la función de servicio `reprocess_automation_event()` (RF-13..RF-15
> y contrato de idempotencia con los cuatro estados `pending`, `sent`,
> `skipped`, `failed`); (2) atomicidad del registro del evento `pending` con
> la transición de la cita a Cancelada en la misma transacción — «sin traza
> local, sin cancelación confirmada» — (RF-11, RF-12 y matriz de fallos); y
> (3) aclaración de RF-10: su garantía de «cancelación intacta» aplica a
> fallos de publicación **posteriores** al commit, no al registro previo del
> evento. RF-8 y RF-9 se conservan sin cambios de requisito; se ajustan
> contratos, casos límite, fuera de alcance y criterios afectados. **Texto
> aprobado por la usuaria el 2026-10-23** con confirmaciones explícitas sobre:
> el comportamiento conservador del `pending` huérfano (con su limitación
> operativa aceptada y explicitada en esta spec); la desalineación del código
> ya implementado en T19/T20 como consecuencia del cambio de diseño, a
> corregir en la fase de planificación; y la ausencia de cambios en
> `tests/expected_content.py` (los literales visibles no cambian). La
> reanudación de la fase 2 queda condicionada a la reaprobación del
> `plan.md` §9 y de las tareas alineadas con esta enmienda. Alcance completo
> en «Nota de enmienda 2 — 2026-10-23 (precisiones RF-8..RF-15)»
> (final del documento).

> **Enmienda 3 (2026-10-30) — APROBADA por la usuaria (2026-10-30, DP-06):**
> incorpora **RF-16** sobre la clasificación de las respuestas HTTP no-2xx y la
> no reintentabilidad de los rechazos 4xx permanentes en el reproceso. Se
> conserva el literal vigente «Respuesta no válida del servicio (HTTP {code}).»
> (DP-01) y no se modifican las Specs/planes 007/008 ni
> `tests/expected_content.py`. Alcance completo en «Nota de enmienda 3 —
> 2026-10-30 (DP-06)» (final del documento) y en `docs/defectos/D-010-01.md`
> §11.

## Contexto y objetivo
Cuando una cita cambia a estado Cancelada, el paciente necesita conocer
oportunamente la modificación para evitar desplazamientos innecesarios y
mantener información confiable sobre su atención. Además, esa cancelación debe
aplicarse en un único punto para no duplicar lógica entre quienes pueden
provocarla (el paciente, Spec 017; el consultorio, Spec 018). Esta
funcionalidad concentra el servicio centralizado de cancelación: cambia el
estado de la cita a Cancelada una sola vez, libera el horario para que pueda
volver a reservarse, coordina la notificación por los canales aprobados y — con
la presente enmienda — define el evento de negocio `appointment.cancelled` para
la automatización (implementada y aceptada el 2026-10-30).

## Usuarios / actores
- Paciente: destinatario de la notificación de cancelación.
- Consultorio (psicóloga / administración): invoca la cancelación como
  operación interna; sus interfaces son las Specs 017 y 018.
- Servicio de automatización (n8n): destinatario de los eventos de negocio y
  transporte del correo.

## Historias de usuario
- H1: Como paciente quiero recibir una notificación cuando una cita sea cancelada para estar informado oportunamente.
- H2: Como consultorio quiero que exista un único servicio de cancelación que
  cambie el estado, libere el horario y coordine la notificación, para que las
  Specs 017 y 018 reutilicen las mismas garantías sin lógica duplicada.
- H3: Como administrador del consultorio quiero que cada cancelación confirmada
  emita un evento de negocio, para que las automatizaciones posteriores
  configuradas en n8n puedan reaccionar a la cancelación.

## Requisitos funcionales (criterios de aceptación en EARS)

### Requisitos consolidados — comportamiento implementado y aprobado (HU-010, cerrada 2026-10-13)

> RF-1..RF-4 conservan sus identificadores originales para no romper la
> trazabilidad con `plan.md`, los tests `TC-010-*` y la evidencia
> `docs/evidencias/hu-010/`. RF-5..RF-7 consolidan como requisitos de primer
> nivel los «Contratos fijados (enmienda 2026-10-13)» (justificación de la
> numeración en «Nota de enmienda 2026-10-23»).

- RF-1: CUANDO una cita cambie a estado Cancelada y el cambio sea confirmado, EL SISTEMA enviará una notificación de cancelación.
- RF-2: CUANDO se envíe la notificación, EL SISTEMA indicará claramente que la cita fue cancelada.
- RF-3: CUANDO corresponda, EL SISTEMA enviará la notificación por correo electrónico y WhatsApp.
- RF-4: SI una cancelación ya fue notificada, ENTONCES EL SISTEMA evitará duplicar la misma notificación sin una causa válida.
- RF-5: CUANDO se solicite cancelar una cita existente en estado Confirmada, EL SISTEMA le asignará el estado Cancelada mediante una transición única confirmada en persistencia; si la cita no existe o ya está Cancelada, no se producirá ningún cambio de estado.
- RF-6: CUANDO una cita pase al estado Cancelada, EL SISTEMA liberará su horario: el horario cancelado dejará de contarse como ocupado en la disponibilidad y podrá reservarse de nuevo, manteniendo la protección de doble reserva entre citas no canceladas.
- RF-7: SI la notificación de cancelación no puede enviarse (fallo del canal, respuesta no válida o datos de contacto inválidos), ENTONCES EL SISTEMA mantendrá la cancelación confirmada, sin revertirla ni bloquearla.

### Requisitos nuevos — **[IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]**

> Evento de negocio `appointment.cancelled` (v1). **[IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]**; el plan y las
> tareas de la fase 2 están aprobados y ejecutados (HU-017). RF-8 y RF-10 se ajustan y RF-11..
> RF-15 se añaden por la enmienda 2 **aprobada (2026-10-23)**.
> Trazabilidad: RF-8..RF-15 pertenecen a
> **H3** (evento de negocio por cancelación confirmada, bajo decisión del
> administrador — incluido su reproceso). **RF-16** se añade por la enmienda 3
> **aprobada (2026-10-30, DP-06)**; implementado en el alcance de D-010-01 y
> aceptado funcionalmente el 2026-10-30.

- RF-8 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: CUANDO una cancelación quede confirmada en la base de datos, EL SISTEMA registrará y emitirá el evento de negocio `appointment.cancelled` (versión 1), independientemente del resultado del envío del correo de cancelación y de que dicho envío corresponda o no. El evento tendrá un identificador determinista con formato `appointment.cancelled:{id}:v1`, protegido por una restricción UNIQUE, y un payload versionado sin datos personales innecesarios. Este evento representará la cancelación confirmada y no el envío de una notificación.
- RF-9 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: CUANDO se emita el evento `appointment.cancelled`, EL SISTEMA incluirá como campos obligatorios `event_id`, `event_type`, `event_version` (1), `occurred_at` y `appointment` con `id`, `service`, `date`, `time` y `status` (`"cancelled"`); quedarán excluidos `patient_name`, `email`, `phone`, `document_type` y `document_number`.
- RF-10 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: SI la publicación del evento `appointment.cancelled` falla por un motivo técnico después de confirmada la cancelación, ENTONCES EL SISTEMA dejará el evento trazado con estado fallido y el motivo en español y la cancelación confirmada permanecerá intacta; esta garantía aplica a los fallos de publicación **posteriores** al commit, no al registro previo del evento (ver RF-11 y RF-12). No habrá reintentos automáticos y el reproceso posterior, si el administrador lo solicita, se regirá por RF-13, RF-14 y RF-15 sin producir duplicados.
- RF-11 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: CUANDO una cita cambie al estado Cancelada, EL SISTEMA confirmará la transición de estado y el registro del evento `appointment.cancelled` en estado `pending` de manera conjunta, como partes de una única transacción de persistencia sobre la misma conexión: o ambas quedan confirmadas o ninguna («sin traza local, sin cancelación confirmada»). El evento se registrará en estado `pending` como parte de esa transacción; la publicación se realizará después del commit (RF-8, RF-10).
- RF-12 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: SI el registro del evento `appointment.cancelled` en estado `pending` falla antes de confirmar la cancelación, ENTONCES EL SISTEMA revertirá la operación completa: la cita no quedará en estado Cancelada, no se emitirá ningún evento ni notificación derivada de esa operación, y el estado observable de la cita será el anterior a la solicitud.
- RF-13 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: CUANDO el administrador solicite reprocesar un evento `appointment.cancelled` cuyo estado sea fallido, EL SISTEMA reintentará su publicación conservando el mismo `event_id` y el mismo registro existente, sin crear una segunda fila ni cambiar el identificador determinista, y actualizará el estado y el detalle del resultado de forma trazable: `sent` si el POST tiene éxito, `skipped` si en ese momento la URL del webhook está vacía, o `failed` con el motivo en español si vuelve a fallar. No habrá reintentos automáticos: el nuevo intento solo ocurre por decisión explícita del administrador.
- RF-14 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: SI se solicita reprocesar un evento `appointment.cancelled` cuyo estado no sea fallido (`sent`, `skipped` o `pending`), ENTONCES EL SISTEMA no realizará ningún intento de publicación, no enviará ninguna petición y no modificará el registro; el comportamiento detallado por estado se describe en «Contrato de idempotencia y reproceso (RF-13..RF-15)».
- RF-15 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: MIENTRAS dos o más solicitudes de reproceso compitan sobre el mismo evento `appointment.cancelled`, EL SISTEMA permitirá que únicamente una de ellas realice el intento de publicación; las demás no producirán un intento adicional ni modificarán el registro. La exclusión se garantiza mediante una transición atómica condicionada al estado actual del evento (el diseño concreto corresponde al plan).
- RF-16 [APROBADO 2026-10-30 — DP-06]: CUANDO la publicación de un evento de automatización reciba una respuesta HTTP no-2xx, EL SISTEMA registrará el evento como `failed` con el detalle «Respuesta no válida del servicio (HTTP {code}).», donde `{code}` es el código recibido. Este detalle se aplicará de forma idéntica en la publicación inicial del evento de negocio, en su reproceso y en los eventos de correo. Un evento `appointment.cancelled` con ese detalle solo será admitido por `reprocess_automation_event()` cuando el código sea transitorio (429 o 5xx); los códigos 4xx permanentes (400, 401, 403, 404, 405, 409, 422, entre otros) no serán readmitidos. Los fallos por timeout, por error de conexión (`URLError` sin `HTTPError`) o por excepción inesperada conservarán sus detalles actuales y seguirán siendo readmitidos.

## Requisitos no funcionales
- Protección de datos personales.
- Trazabilidad del cambio y de las notificaciones.
- Claridad del mensaje para evitar interpretaciones ambiguas.
- Minimización de datos en el evento de negocio `appointment.cancelled`: payload sin datos personales innecesarios (RF-9).
- Trazabilidad y reintentabilidad de la publicación del evento de negocio: estado y motivo registrados, reintentable sin duplicados vía reproceso explícito y sin infraestructura de colas (RF-8, RF-10, RF-13..RF-15).
- Atomicidad de la cancelación y su traza local: sin el registro `pending` del evento `appointment.cancelled` no hay cancelación confirmada (RF-11, RF-12).
- Clasificación por código HTTP y no reintentabilidad de los rechazos 4xx permanentes: el `detail` persistido es el único criterio, sin columnas, tablas, índices ni migraciones nuevas (RF-16; DP-02, DP-05).

## Casos límite
- Cita ya cancelada.
- Fallo de uno de los canales de notificación.
- Datos de contacto incompletos.
- Cancelación repetida.
- Fallo en el registro local del evento `appointment.cancelled` dentro de la transacción de la cancelación: se revierte todo; la cita no queda Cancelada y no se emite ningún evento (RF-11, RF-12).
- Fallo técnico en la publicación del evento de negocio después del commit: el evento queda trazado con estado fallido y motivo, puede reprocesarse a petición del administrador sin duplicados (RF-13) y la cancelación no se ve afectada (RF-10).
- Webhook de automatización no configurado durante una cancelación: el evento queda `skipped` y la cancelación no depende de la automatización.
- Solicitud de reproceso sobre un evento que no está en estado fallido (`sent`, `skipped` o `pending`): sin efecto observable, sin POST y sin cambios en el registro (RF-14).
- Evento `pending` huérfano (proceso interrumpido tras el commit y antes del POST): queda trazado como `pending`; su recuperación queda fuera del alcance de `reprocess_automation_event()` y, en esta fase, **no existe vía de recuperación** (limitación operativa aceptada y documentada en el contrato de idempotencia y en «Fuera de alcance»).
- Dos reprocesos concurrentes del mismo evento: únicamente una de las solicitudes realiza el intento de publicación (RF-15).

## Fuera de alcance
- Reprogramación automática.
- Gestión de campañas de comunicación.
- Definición de políticas de cancelación.
- Interfaz o endpoint para cancelar: corresponde a las Specs 017 (paciente) y 018 (consultorio); esta spec solo define el servicio interno.
- Notificación por WhatsApp: canal pendiente de la Spec 009.
- Tabla de auditoría de cambios de estado.
- Reintentos automáticos de la notificación fallida o de la publicación del evento de negocio, y cualquier infraestructura de colas o workers: el único reproceso posible es el explícito del administrador mediante `reprocess_automation_event()` sobre eventos en estado fallido (RF-13).
- Recuperación de eventos `appointment.cancelled` en estado `pending` (incluidos los huérfanos) y promoción de eventos `skipped` a un nuevo intento de publicación: fuera del alcance de `reprocess_automation_event()` y de esta enmienda (posible enmienda futura solo si el diseño demuestra la necesidad; ver «Contrato de idempotencia y reproceso»). **Limitación operativa aceptada**: un evento `pending` huérfano puede permanecer en `pending` indefinidamente, sin vía de recuperación con el mecanismo actual de esta fase.
- Borrado del evento en Google Calendar y manejo del `calendar_event_id`: corresponden a la Spec 007 en un paso posterior; esta spec no los define.
- Cambios del literal de respuesta no-2xx o de `tests/expected_content.py` por la enmienda 3: DP-01 conserva «Respuesta no válida del servicio (HTTP {code}).» y no se modifican las Specs/planes 007/008 (RF-16).

## Contratos fijados (enmienda 2026-10-13)

Cierra las dudas [NECESITA ACLARACIÓN] y fija el mecanismo aprobado por la
usuaria (decisiones Q1–Q4 del `plan.md` §7.1). Estos contratos quedan
consolidados como RF-5 (transición), RF-6 (liberación del horario) y RF-7
(tolerancia a fallos); se conservan aquí íntegros, sin pérdida de información.

### Transición de estado y disparador (cierra Q1 → RF-5)
- La cita pasa de `confirmed` («Confirmada») a **`cancelled` («Cancelada»)** mediante el servicio interno `cancel_appointment()`; **sin endpoint ni interfaz** (fuera de alcance; la UI corresponde a las Specs 017/018).
- «El cambio sea confirmado» = el cambio de estado queda **confirmado en persistencia** (commit) antes de notificar: el sistema notifica solo si la transición se realizó.
- SI la cita no existe o ya estaba cancelada, ENTONCES el sistema no cambia nada y **no envía notificación** (RF-1, RF-4, RF-5, casos límite «Cita ya cancelada» y «Cancelación repetida»).

### Canales de notificación (cierra Q2, RF-3)
- **Correo electrónico**: notificación funcional mediante el **mismo webhook de automatización de HU-007/HU-008** (`AUTOMATION_WEBHOOK_URL`, con `AUTOMATION_WEBHOOK_AUTH_HEADER` si existe). La aplicación compone el mensaje y emite el evento estructurado; n8n solo transporta.
- **WhatsApp**: canal **pendiente de la Spec 009**; no se emite ni se registra evento de WhatsApp en esta funcionalidad.
- «Cuando corresponda» = **canal implementado y configurado**: hoy el correo; si el webhook no está configurado, el evento de correo queda `skipped` y el sistema opera igual (la cancelación no depende de la notificación).

### Registro y deduplicación (RF-4)
- Cada notificación de correo se registra en la tabla `automation_events` (HU-007) con `event_id` determinista `appointment.cancellation_email:{appointment.id}:v1` y `UNIQUE(event_id)`: una sola notificación por cancelación, sin duplicados ante reprocesos, en el punto de persistencia.
- La cancelación repetida no vuelve a notificar: la transición condicional `confirmed → cancelled` solo dispara la notificación la primera vez.
- Estados: `pending` → `sent` | `skipped` | `failed`, con `detail` en español.

### Payload del evento de correo de cancelación (contrato)
```json
{
  "event_id": "appointment.cancellation_email:34:v1",
  "event_type": "appointment.cancellation_email",
  "event_version": 1,
  "occurred_at": "2026-10-13 12:34:56",
  "recipient": { "to": "paciente@ejemplo.com", "patient_name": "Ana Pérez" },
  "message": { "subject": "…", "text": "…", "html": "…" },
  "appointment": { "id": 34, "service": "individual", "date": "2026-10-15", "time": "10:00", "status": "cancelled" }
}
```
- `recipient` y `message` son exclusivos de este tipo de evento; es una excepción documentada a la minimización de datos: el aviso no puede llegar sin destinatario ni mensaje.
- Campos excluidos: `document_type`, `document_number`, `phone`.

### Contenido del mensaje (cierra Q3, RF-2)
- Asunto: «Cita cancelada — {servicio} · {fecha legible en español} · {hora}».
- Cabecera del cuerpo: «Tu cita ha sido cancelada. Estos son los datos de la cita cancelada:».
- Contenido mínimo: saludo con el nombre del paciente, servicio, fecha, hora, **estado «Cancelada»**, Referencia #{id} y pie que invita a agendar una nueva cita.
- Formato: texto plano + HTML con la misma plantilla, paleta Serenidad Natural y reglas de HU-008 (estilos inline, sin recursos remotos).
- Los literales son contractuales: sus valores viven en `consultorio/content/email_content.py` y `consultorio/content/appointment_content.py`, y se reflejan en `tests/expected_content.py`; cambiar un copy obliga a PR de spec primero.

### Fallo de entrega (→ RF-7)
- Mejor esfuerzo: SI el webhook falla (timeout, servicio no disponible o respuesta no válida), ENTONCES el evento quedará `failed` con su motivo en español y **la cancelación permanece confirmada** (nunca se revierte ni se bloquea por un fallo de notificación).
- Sin reintentos automáticos; la re-ejecución la decide el administrador y el `UNIQUE(event_id)` impide el duplicado.

### Liberación del horario (cierra Q4 → RF-6)
- CUANDO una cita sea cancelada, EL SISTEMA **liberá su horario**: la disponibilidad (`/citas/horarios` y `/citas/disponibilidad`) no contará las citas canceladas y el horario podrá reservarse de nuevo.
- La unicidad de `servicio + fecha + hora` se mantiene **entre citas no canceladas**: se sustituye el `UNIQUE` de la tabla por un **índice único parcial** `WHERE status <> 'cancelled'`, con migración idempotente de las bases existentes, respaldo previo del fichero y aborto si existieran duplicados entre citas no canceladas.
- La protección contra doble reserva de las citas no canceladas permanece intacta.

## Contratos fijados — evento de negocio `appointment.cancelled` (enmienda 2026-10-23, implementado — aceptado funcionalmente 2026-10-30)

Fija el mecanismo aprobado por la usuaria para RF-8..RF-10 y, con la
enmienda 2 (2026-10-23), para RF-11..RF-15 (atomicidad y reproceso). Mismo
modelo de fiabilidad que las automatizaciones existentes (HU-007/008/010).
Los RF están **[IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]**, con plan,
tareas, tests, evidencia y aceptación (HU-017).

### Atomicidad del registro con la cancelación (RF-11, RF-12)
- **Principio: «sin traza local, sin cancelación confirmada».** La transición de la cita al estado `cancelled` y el registro del evento `appointment.cancelled` en estado `pending` se confirman **o se revierten de manera conjunta**, utilizando la misma conexión y transacción de persistencia de SQLite. No puede existir una cancelación confirmada sin su evento `pending` correspondiente.
- El registro en `pending` forma parte de la transacción de la cancelación; la publicación (POST al webhook) se realiza **después** del commit, por separado y sin posibilidad de revertir la cancelación (RF-10).
- Mismo modelo de deduplicación en el punto de persistencia: `event_id` determinista `appointment.cancelled:{appointment.id}:v1` en la tabla `automation_events` (HU-007) con `UNIQUE(event_id)`.

### Emisión independiente del correo (RF-8)
- El evento se registra y se emite **independientemente** del resultado del envío del correo de cancelación: también si el correo falla, se omite o los datos de contacto son inválidos. Representa la **cancelación confirmada**, no el envío de una notificación.
- El registro del evento en estado `pending` se confirma **junto con** la cancelación (misma transacción, RF-11/RF-12); la publicación se realiza **después** del commit con `event_id` determinista `appointment.cancelled:{appointment.id}:v1` y `UNIQUE(event_id)`. El identificador determinista no cambia en ningún momento del ciclo, tampoco durante el reproceso (RF-13). Si el flujo de cancelación se ejecuta de nuevo sobre una cita ya cancelada, la transición condicional no se repite (RF-5) y, en cualquier caso, el `UNIQUE(event_id)` impide una segunda fila y cualquier envío derivado de ella; el reproceso administrativo no pasa por ese INSERT, sino por `reprocess_automation_event()` (RF-13).
- Estados: `pending` → `sent` | `skipped` | `failed`, con `detail` en español (mismo modelo que `appointment.confirmed` y `appointment.cancellation_email`).

### Envío y fiabilidad (RF-8, RF-10)
- Un solo POST best-effort al mismo webhook de automatización (`AUTOMATION_WEBHOOK_URL`, con `AUTOMATION_WEBHOOK_AUTH_HEADER` si existe y el timeout ya configurado), tras el commit de la cancelación.
- **Sin reintentos automáticos** (sin colas ni workers): un segundo intento de publicación solo ocurre cuando el administrador lo solicita explícitamente mediante la función de servicio `reprocess_automation_event()` sobre un evento en estado fallido (RF-13); la unicidad por `UNIQUE(event_id)` garantiza un único registro por cancelación.
- SI `AUTOMATION_WEBHOOK_URL` está vacío, ENTONCES el evento queda `skipped` y **la cancelación no depende de la automatización**. La misma semántica se aplica durante un reproceso: si la URL está vacía en el momento del reproceso, el evento queda `skipped`.
- SI la publicación falla (timeout, servicio no disponible o respuesta no válida), ENTONCES el evento queda `failed` con su motivo en español y **la cancelación permanece intacta** (garantía de fallos de publicación posteriores al commit, RF-10; el registro previo se rige por RF-11/RF-12). El evento es reproducible a petición del administrador sin producir duplicados (RF-13).

### Contrato de idempotencia y reproceso (RF-13..RF-15)
- Reprocesar un evento es una operación de servicio `reprocess_automation_event()` — mismo patrón que `cancel_appointment()`: **sin UI ni endpoint** en esta spec, invocada únicamente por decisión explícita del administrador; **sin reintentos automáticos**.
- Solo reprocesa eventos de tipo `appointment.cancelled` cuyo estado sea **`failed`**. Recupera el registro existente, conserva el mismo `event_id`, no crea una segunda fila, no cambia el identificador determinista y realiza un único nuevo intento de publicación (RF-13).
- El resultado del reproceso se traza como el flujo normal: `sent` si el POST tiene éxito; `failed` con detalle en español si vuelve a fallar; `skipped` con su detalle si la URL del webhook está vacía en ese momento (misma semántica de URL vacía que el flujo normal, ver «Envío y fiabilidad»).
- **Exclusión ante concurrencia**: la admisión del reproceso se condiciona al estado actual del evento mediante una transición atómica (RF-15); si dos solicitudes compiten, solo una realiza el intento y la otra no modifica el registro.
- **Cuatro estados, sin excepciones**: el ciclo de publicación del evento `appointment.cancelled` usa exactamente `pending`, `sent`, `skipped` y `failed`. Esta enmienda **no añade ningún estado nuevo**; cualquier extensión exige que el diseño demuestre la necesidad y una enmienda posterior.
- Comportamiento ante una solicitud de reproceso, según el estado del evento:

| Estado actual del evento | Efecto de una solicitud de reproceso |
|---|---|
| `failed` | Se admite (RF-13): un único nuevo intento sobre el mismo registro; el estado final será `sent`, `failed` (con detalle en español) o `skipped` (URL vacía en ese momento). |
| `sent` | No-op (RF-14): sin nuevo POST y sin cambio de estado; el evento ya fue publicado y reintentarlo duplicaría la publicación aguas abajo. |
| `skipped` | No-op (RF-14): sin nuevo POST y sin cambio de estado; convertir un `skipped` en publicable queda fuera del alcance de `reprocess_automation_event()` (ver «Fuera de alcance»). |
| `pending` | No-op (RF-14): sin nuevo POST y sin cambio de estado. Un `pending` huérfano —el proceso se interrumpió tras el commit y antes del POST— permanece trazado como `pending`; su recuperación queda fuera del alcance de `reprocess_automation_event()` hoy, porque no puede distinguirse de un `pending` aún en curso sin añadir estados o marcas que la decisión aprobada posterga (elección conservadora: reprocesar un `pending` en curso duplicaría la publicación). **Limitación operativa aceptada para esta fase**: si el proceso termina después del commit y antes del POST, el evento puede permanecer en `pending` indefinidamente y, con el mecanismo actual, **no habrá vía de recuperación**; el no-op **no** es una recuperación garantizada. Podrá reconsiderarse en una fase posterior (ver «Fuera de alcance»). |

### Matriz de fallos (RF-10, RF-11, RF-12)
| Fallo | Cancelación de la cita | Evento `appointment.cancelled` |
|---|---|---|
| El registro del evento falla **antes** del commit | **No queda confirmada**: se revierte la operación completa (rollback); la cita conserva su estado anterior (RF-12). | No se crea ningún registro. |
| El commit se completa pero falla el POST al webhook | **Permanece confirmada** (RF-10). | Queda `failed` con el motivo en español; reprocesable a petición del administrador (RF-13). |
| Webhook no configurado (URL vacía) | **Permanece confirmada** (RF-8). | Queda `skipped` con su detalle. |

### Payload del evento (contrato, RF-9)
```json
{
  "event_id": "appointment.cancelled:34:v1",
  "event_type": "appointment.cancelled",
  "event_version": 1,
  "occurred_at": "2026-10-23 12:34:56",
  "appointment": { "id": 34, "service": "individual", "date": "2026-10-15", "time": "10:00", "status": "cancelled" }
}
```
- Campos obligatorios: `event_id`, `event_type`, `event_version` (1), `occurred_at` y `appointment { id, service, date, time, status }`.
- **Sin datos personales**: excluidos `patient_name`, `email`, `phone`, `document_type` y `document_number`. Este evento **no** incluye `recipient` ni `message` (son exclusivos del correo de cancelación, ver «Payload del evento de correo de cancelación»).
- Cualquier cambio de forma del payload eleva `event_version` y el `event_id` asociado (misma regla que la Spec 007).

## Criterios de finalización
RF-1..RF-7 (consolidados) con test en verde y demo manual de cancelación con
notificación por los canales disponibles; esos comportamientos ya están
implementados y validados con HU-010 (aceptada y cerrada el 2026-10-13).
RF-8..RF-15 [IMPLEMENTADO — ACEPTADO FUNCIONALMENTE 2026-10-30]: cerrados con
plan, tareas, tests, evidencia y aceptación (HU-017). La enmienda 1 que introduce RF-8..RF-10
fue aprobada por la usuaria el 2026-10-23; la enmienda 2 que ajusta RF-8/RF-10
y añade RF-11..RF-15 fue **aprobada por la usuaria el 2026-10-23**, y el
`plan.md` §9 y las tareas se reaprobaron y ejecutaron alineados a ella.
RF-16 (enmienda 3, aprobada 2026-10-30, DP-06): implementado en el alcance de
D-010-01 y validado (aceptado funcionalmente el 2026-10-30); sus criterios de aceptación
son CA-D010-01..CA-D010-14 del registro `docs/defectos/D-010-01.md` §5.

### Criterios de aceptación de la enmienda 2 (RF-8..RF-15)
- CA-1: Cancelación confirmada ⇒ existe un registro `appointment.cancelled` (v1) con `event_id` determinista `appointment.cancelled:{id}:v1` y se emite el POST correspondiente, con independencia del resultado del correo de cancelación (RF-8).
- CA-2: El payload emitido cumple el contrato de campos obligatorios y exclusiones de RF-9, sin `recipient` ni `message` (RF-9).
- CA-3: URL del webhook vacía ⇒ la cancelación queda confirmada y el evento termina en `skipped` con detalle (RF-8).
- CA-4: POST fallido tras el commit ⇒ la cita permanece Cancelada y el evento queda `failed` con el motivo en español; el registro y el evento no se revierten (RF-10).
- CA-5: Fallo simulado en el registro del evento dentro de la transacción ⇒ la cita no cambia a Cancelada, no se crea el registro y no se emite POST alguno; con el registro correcto, transición y evento `pending` quedan confirmados juntos (RF-11, RF-12).
- CA-6: `reprocess_automation_event()` sobre un evento `failed` ⇒ un único nuevo POST con el mismo `event_id` y sobre la misma fila; el estado resultante (`sent`, `failed` con detalle en español o `skipped` si la URL está vacía) queda actualizado de forma trazable (RF-13).
- CA-7: `reprocess_automation_event()` sobre un evento `sent`, `skipped` o `pending` ⇒ cero POST y registro sin modificación (RF-14).
- CA-8: Dos reprocesos concurrentes del mismo evento ⇒ un único intento de publicación y un único cambio de estado (RF-15).

### Criterios de aceptación de la enmienda 3 (RF-16)

| RF | Criterios de aceptación (contenido completo en `docs/defectos/D-010-01.md` §5) |
|---|---|
| RF-16 | CA-D010-01, CA-D010-02, CA-D010-03, CA-D010-04, CA-D010-05, CA-D010-06, CA-D010-07, CA-D010-08, CA-D010-09, CA-D010-10, CA-D010-11, CA-D010-12, CA-D010-13, CA-D010-14 |

> Referencia cruzada de trazabilidad: **RF-16 → CA-D010-01…CA-D010-14**. No se
> duplica aquí el contenido de los criterios; el registro del defecto es su
> fuente y contiene la evidencia asociada.

## Dudas abiertas
- [RESUELTA — Q2] Confirmar si debe notificarse siempre por ambos canales o según preferencias del paciente → fijado en «Contratos fijados» (correo vía webhook; WhatsApp pendiente de Spec 009; «cuando corresponda» = canal implementado y configurado).
- [RESUELTA — Q3] Definir el contenido exacto del aviso de cancelación → fijado en «Contratos fijados» (asunto «Cita cancelada», estado «Cancelada», pie de reagendado, literales contractuales).
- [RESUELTA — 2026-10-23] ¿Renumerar los RF tras consolidar los «Contratos fijados»? → **no**: se conservan RF-1..RF-4 para mantener la trazabilidad con `plan.md`, los tests `TC-010-*` y la evidencia de HU-010 ya cerrada; los RF consolidados y nuevos se añaden con números libres (RF-5..RF-10).
- [RESUELTA — 2026-10-23] Enmienda de esta spec (título ampliado, RF-5..RF-7 consolidados y RF-8..RF-10 nuevos) → **aprobada por la usuaria el 2026-10-23**. El comportamiento vigente es RF-1..RF-10 (implementados y aceptados).
- [RESUELTA — 2026-10-23, enmienda 2 aprobada] Contradicción sobre el reproceso del evento fallido («choca en el INSERT y se descarta» vs. «reintento posterior sin duplicados» vs. «el reproceso lo decide el administrador») → resuelta por la enmienda 2: el reproceso explícito del administrador es la función de servicio `reprocess_automation_event()` sobre eventos `failed` (RF-13..RF-15 y «Contrato de idempotencia y reproceso»); el `UNIQUE(event_id)` garantiza la unicidad del registro y el reproceso reutiliza la fila existente sin crear duplicados.
- [RESUELTA — 2026-10-23, enmienda 2 aprobada] Atomicidad del registro de `appointment.cancelled` con la cancelación → resuelta por la enmienda 2: «sin traza local, sin cancelación confirmada»; transición y registro `pending` en la misma transacción (RF-11, RF-12 y matriz de fallos). La ventana de fallo del registro del evento de **correo** (`appointment.cancellation_email`, post-commit) no se modifica y queda como limitación técnica conocida para documentar en `plan.md` en fase posterior.
- [RESUELTA — 2026-10-23, decisión conservadora de la enmienda 2, aprobada] Reproceso de eventos en estado `pending` (incluidos huérfanos), `sent` y `skipped` → **fuera del alcance** de `reprocess_automation_event()` (no-op, RF-14): solo se reprocesa `failed`. Se eligió la opción conservadora porque un `pending` puede estar aún en curso y reprocesarlo duplicaría la publicación; los cuatro estados aprobados (`pending`, `sent`, `skipped`, `failed`) se mantienen sin añadir ninguno nuevo hasta que el diseño demuestre la necesidad. La usuaria reconoció y aceptó la consecuencia: un `pending` huérfano puede permanecer `pending` indefinidamente, sin vía de recuperación en esta fase (limitación explícita en el contrato de idempotencia, en los casos límite y en «Fuera de alcance»).
- [RESUELTA — 2026-10-30, DP-06] ¿Debe el mapeo HTTP por código vivir solo en `plan.md`? → **no**: se incorpora RF-16 a esta spec (enmienda 3 aprobada) para que la clasificación de respuestas no-2xx y la no reintentabilidad de los 4xx permanentes sean requisito trazable; el diseño concreto sigue en `plan.md` §9.3/§9.5/§9.8.1 y en `docs/defectos/D-010-01.md`.

## Nota de enmienda 2026-10-23

Enmienda redactada por el planificador, revisada por el coordinador y
**aprobada por la usuaria el 2026-10-23**. No se ha modificado `plan.md`,
`tareas.md`, código ni tests.

**Alcance del cambio:**

1. **Título ampliado** a «Servicio centralizado de cancelación y notificación de
   citas», porque las Specs 017 y 018 ya tratan la 010 como el servicio que
   cancela la cita, libera el horario y coordina la notificación. El
   identificador `010` y la ruta `specs/010_notificar-cancelacion/` no cambian.
2. **Consolidación de RF**: pasan a requisitos de primer nivel los
   comportamientos que solo estaban en «Contratos fijados (enmienda
   2026-10-13)» — transición única a Cancelada (RF-5), liberación del horario
   (RF-6) y tolerancia a fallos de canales sin revertir la cancelación (RF-7).
   La notificación posterior a la confirmación del cambio (RF-1) y la
   prevención de duplicados de la notificación (RF-4) ya eran RF y se conservan
   sin debilitar garantías.
3. **Nuevo requisito (histórico de la enmienda 1)**: el evento de negocio `appointment.cancelled`
   (v1) en RF-8..RF-10, implementados y aceptados el 2026-10-30. El texto
   propuesto por la usuaria se reparte en tres requisitos verificables por
   separado — RF-8 (emisión e identificador determinista), RF-9 (campos
   obligatorios del payload sin datos personales) y RF-10 (fallo trazado con
   motivo y reintentabilidad sin duplicados) — conservando su sentido.

**Decisiones de la usuaria reflejadas (sin cambios):** nombre del evento
`appointment.cancelled` (v1); el `calendar_event_id` de Google Calendar y su
borrado quedan fuera de esta spec (Spec 007, paso posterior); el evento se
emite independientemente del resultado del envío del correo; mismo modelo de
fiabilidad que HU-007/008/010 (registro en `automation_events`, `event_id`
determinista con `UNIQUE`, un solo POST best-effort tras el commit, estados
`pending → sent | skipped | failed`, sin reintentos automáticos); payload
versionado sin datos personales innecesarios.

**Numeración de los RF:** se preservan RF-1..RF-4 porque `plan.md` (matriz de
cobertura), los tests `TC-010-*`, el informe `docs/evidencias/hu-010/qa-hu-010.md`
y el cierre de HU-010 (2026-10-13) referencian esos identificadores; renumerar
rompería la cadena HU/RF → spec → plan → código → tests → evidencia. Los RF
consolidados RF-5..RF-7 corresponden a comportamientos ya cubiertos por el plan
(Q4, D4/D5/D7) y por los tests de HU-010, por lo que no alteran el plan ni las
tareas cerradas.

**Consecuencias pendientes:** RF-8..RF-10 requieren, tras la aprobación de esta
enmienda, una autorización explícita para la fase de planificación (`plan.md` y
`tareas.md`) antes de cualquier implementación.

## Nota de enmienda 2 — 2026-10-23 (precisiones RF-8..RF-15)

**APROBADA por la usuaria (2026-10-23).** Enmienda redactada por el planificador a partir de precisiones funcionalmente aprobadas por la usuaria, y cuyo texto completo fue aprobado posteriormente por la usuaria el 2026-10-23 con tres confirmaciones explícitas: (1) aprobación del comportamiento conservador del `pending` huérfano, con la **limitación operativa** — sin vía de recuperación en esta fase — hecha explícita en el contrato de idempotencia, en los casos límite y en «Fuera de alcance»; (2) aceptación de la desalineación entre el código ya implementado (T19/T20) y este diseño, como consecuencia del cambio y a corregir en la fase de planificación (hasta entonces no afirmar que la atomicidad está garantizada por el código); y (3) `tests/expected_content.py` **sin cambios** por esta enmienda, porque los literales visibles de correo y estados no cambian. No se ha modificado `plan.md`, `task.md`, código ni tests, y tampoco `AGENTS.md` ni otras specs.

**Alcance del cambio (solo `appointment.cancelled`):**

1. **Reproceso del evento fallido (precisión 1)**: nueva función de servicio
   `reprocess_automation_event()` (patrón de `cancel_appointment()`: sin UI ni
   endpoint; decisión explícita del administrador; sin reintentos
   automáticos). Solo reproduce eventos `failed`, reutilizando el registro y el
   `event_id` existentes sin crear una segunda fila, y traza el resultado
   (`sent`, `failed` con detalle en español, `skipped` si la URL está vacía).
   Contrato de idempotencia con exactamente cuatro estados — `pending`,
   `sent`, `skipped`, `failed` — y tabla de comportamiento por estado: sobre
   `sent`, `skipped` y `pending` la solicitud es no-op (RF-13, RF-14). El caso
   `pending` huérfano (proceso interrumpido tras el commit y antes del POST)
   queda fuera del alcance de la función por decisión conservadora, sin añadir
   estados nuevos. Exclusión de reprocesos concurrentes mediante transición
   atómica condicionada al estado (RF-15; el diseño concreto va en `plan.md`).
   Se resuelve la contradicción del texto anterior («el reproceso choca en el
   INSERT y se descarta» vs. «su reintento posterior no producirá duplicados»
   vs. «el reproceso lo decide el administrador»).
2. **Atomicidad del registro con la cancelación (precisión 2)**: la transición
   a Cancelada y el registro del evento en estado `pending` se confirman o se
   revierten conjuntamente en la misma conexión y transacción de SQLite —
   «sin traza local, sin cancelación confirmada» (RF-11, RF-12). Matriz de
   fallos reflejada como requisitos y criterios: fallo del registro antes del
   commit ⇒ rollback y cancelación no confirmada; commit correcto y POST
   fallido ⇒ cancelación intacta y evento `failed` (RF-10, se mantiene y se
   aclara); URL vacía ⇒ cancelación intacta y evento `skipped` (RF-8, se
   mantiene). RF-10 se reescribe para que su garantía de «cancelación
   intacta» se lea sin contradicción: aplica a fallos de publicación
   posteriores al commit, no al registro previo.
3. **Sin cambios en el evento de correo**: `appointment.cancellation_email`
   (HU-010, aceptada y cerrada) conserva su registro post-commit; su ventana
   de fallo conocida se documentará en `plan.md` en fase posterior. RF-8 y
   RF-9 no cambian como requisitos.

**Consecuencias pendientes:** RF-11..RF-15 y los ajustes de RF-10/contratos
exigen actualizar `plan.md` y `task.md` de esta spec (y reanudar las tareas
adaptadas) **tras la aprobación explícita de esta enmienda** — aprobación ya
concedida el 2026-10-23; el `plan.md` §9 y las tareas actualizados quedan
**pendientes de reaprobación** de la usuaria antes de reanudar la
implementación. Los textos reescritos de esta enmienda **no cambian literales
visibles** de correo ni de estados: `tests/expected_content.py` queda **sin
cambios** por esta enmienda (decisión de la usuaria, 2026-10-23). Ninguna
carpeta se renombra: el
identificador `010` y la ruta `specs/010_notificar-cancelacion/` se
mantienen.

## Nota de enmienda 3 — 2026-10-30 (DP-06)

**APROBADA por la usuaria (2026-10-30, DP-06).** Enmienda redactada en
`docs/defectos/D-010-01.md` §11 y aprobada por el coordinador para incorporarla
a esta spec. Añade **RF-16** y no modifica ningún literal visible ni
`tests/expected_content.py`.

**Texto aprobado:** RF-16 (arriba, «Requisitos funcionales»), con el literal
vigente de DP-01.

**Nota de la enmienda:**

- El `detail` persistido es el único criterio de clasificación; no se añaden columnas, tablas, índices, estados ni migraciones.
- La comprobación se aplica dentro del `UPDATE` atómico de admisión del reproceso, no mediante un `SELECT` previo, preservando la exclusión de concurrencia de RF-15.
- El literal «Respuesta no válida del servicio (HTTP {code}).» es el vigente y no cambia; no se modifican las Specs/planes 007/008 ni `tests/expected_content.py`.
- La clasificación por código es: 2xx → `sent`; 4xx permanentes (excepto 429) → `failed` no reintentable; 429 y 5xx → `failed` transitorio y reintentable mediante reproceso explícito; timeout, `URLError` y excepción inesperada → `failed` transitorio y reintentable.
- No se introducen reintentos automáticos, colas ni workers.

**Consecuencias:** se añade RF-16 a la Spec 010 y se actualizan `plan.md`
§9.3/§9.5/§9.8.1; no cambia ningún literal visible ni
`tests/expected_content.py`.
