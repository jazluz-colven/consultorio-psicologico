# Spec 010 — Servicio centralizado de cancelación y notificación de citas

> **Enmienda 2026-10-23 — APROBADA por la usuaria (2026-10-23):**
> título ampliado a «Servicio centralizado de cancelación y notificación de
> citas» (el identificador `010` y la ruta `specs/010_notificar-cancelacion/`
> **no cambian**). Los identificadores RF-1..RF-4 se conservan; los
> comportamientos que solo estaban descritos en «Contratos fijados (enmienda
> 2026-10-13)» se consolidan como RF-5..RF-7; y se añaden RF-8..RF-10
> **[PENDIENTE DE IMPLEMENTACIÓN]** para el evento de negocio
> `appointment.cancelled`. Alcance completo en «Nota de enmienda 2026-10-23»
> (final del documento).

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
la automatización (aún pendiente de implementación).

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

### Requisitos nuevos — **[PENDIENTE DE IMPLEMENTACIÓN]**

> Evento de negocio `appointment.cancelled` (v1). Todavía no está implementado:
> no tiene `plan.md`, tareas ni tests asociados, y no debe implementarse hasta
> que se autorice la fase de planificación (la enmienda fue aprobada por la
> usuaria el 2026-10-23).

- RF-8 [PENDIENTE DE IMPLEMENTACIÓN]: CUANDO una cancelación quede confirmada en la base de datos, EL SISTEMA registrará y emitirá el evento de negocio `appointment.cancelled` (versión 1), independientemente del resultado del envío del correo de cancelación y de que dicho envío corresponda o no. El evento tendrá un identificador determinista con formato `appointment.cancelled:{id}:v1`, protegido por una restricción UNIQUE, y un payload versionado sin datos personales innecesarios. Este evento representará la cancelación confirmada y no el envío de una notificación.
- RF-9 [PENDIENTE DE IMPLEMENTACIÓN]: CUANDO se emita el evento `appointment.cancelled`, EL SISTEMA incluirá como campos obligatorios `event_id`, `event_type`, `event_version` (1), `occurred_at` y `appointment` con `id`, `service`, `date`, `time` y `status` (`"cancelled"`); quedarán excluidos `patient_name`, `email`, `phone`, `document_type` y `document_number`.
- RF-10 [PENDIENTE DE IMPLEMENTACIÓN]: SI la publicación del evento `appointment.cancelled` falla por un motivo técnico, ENTONCES EL SISTEMA dejará el evento trazado con estado fallido y el motivo en español, su reintento posterior no producirá duplicados y no habrá reintentos automáticos; la cancelación confirmada permanecerá intacta.

## Requisitos no funcionales
- Protección de datos personales.
- Trazabilidad del cambio y de las notificaciones.
- Claridad del mensaje para evitar interpretaciones ambiguas.
- Minimización de datos en el evento de negocio `appointment.cancelled`: payload sin datos personales innecesarios (RF-9).
- Trazabilidad y reintentabilidad de la publicación del evento de negocio: estado y motivo registrados, reintentable sin duplicados y sin infraestructura de colas (RF-8, RF-10).

## Casos límite
- Cita ya cancelada.
- Fallo de uno de los canales de notificación.
- Datos de contacto incompletos.
- Cancelación repetida.
- Fallo técnico en la publicación del evento de negocio: el evento queda trazado con estado fallido y motivo, es reintentable sin duplicados y la cancelación no se ve afectada.
- Webhook de automatización no configurado durante una cancelación: el evento queda `skipped` y la cancelación no depende de la automatización.

## Fuera de alcance
- Reprogramación automática.
- Gestión de campañas de comunicación.
- Definición de políticas de cancelación.
- Interfaz o endpoint para cancelar: corresponde a las Specs 017 (paciente) y 018 (consultorio); esta spec solo define el servicio interno.
- Notificación por WhatsApp: canal pendiente de la Spec 009.
- Tabla de auditoría de cambios de estado.
- Reintentos automáticos de la notificación fallida o de la publicación del evento de negocio, y cualquier infraestructura de colas o workers: el reproceso lo decide el administrador.
- Borrado del evento en Google Calendar y manejo del `calendar_event_id`: corresponden a la Spec 007 en un paso posterior; esta spec no los define.

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

## Contratos fijados — evento de negocio `appointment.cancelled` (enmienda 2026-10-23, pendiente de implementación)

Fija el mecanismo aprobado por la usuaria para RF-8..RF-10. Mismo modelo de
fiabilidad que las automatizaciones existentes (HU-007/008/010); **esta sección
describe contrato, no implementación**: no hay plan, tareas ni tests todavía.

### Emisión independiente del correo (RF-8)
- El evento se registra y se emite **independientemente** del resultado del envío del correo de cancelación: también si el correo falla, se omite o los datos de contacto son inválidos. Representa la **cancelación confirmada**, no el envío de una notificación.
- Se registra **después** del commit de la cancelación, en la tabla `automation_events` (HU-007), con `event_id` determinista `appointment.cancelled:{appointment.id}:v1` y `UNIQUE(event_id)`: el reproceso choca en el INSERT y se descarta **antes** de cualquier envío.
- Estados: `pending` → `sent` | `skipped` | `failed`, con `detail` en español (mismo modelo que `appointment.confirmed` y `appointment.cancellation_email`).

### Envío y fiabilidad (RF-8, RF-10)
- Un solo POST best-effort al mismo webhook de automatización (`AUTOMATION_WEBHOOK_URL`, con `AUTOMATION_WEBHOOK_AUTH_HEADER` si existe y el timeout ya configurado), tras el commit de la cancelación.
- **Sin reintentos automáticos** (sin colas ni workers): el reproceso lo decide el administrador y el `UNIQUE(event_id)` impide duplicados.
- SI `AUTOMATION_WEBHOOK_URL` está vacío, ENTONCES el evento queda `skipped` y **la cancelación no depende de la automatización**.
- SI la publicación falla (timeout, servicio no disponible o respuesta no válida), ENTONCES el evento queda `failed` con su motivo en español, es reintentable sin producir duplicados y **la cancelación permanece confirmada**.

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
RF-8..RF-10 [PENDIENTE DE IMPLEMENTACIÓN]: se considerarán al cerrar su
implementación (plan, tareas, tests, evidencia y aceptación); hasta entonces
esta spec queda con esos RF abiertos (la enmienda que los introduce fue
aprobada por la usuaria el 2026-10-23).

## Dudas abiertas
- [RESUELTA — Q2] Confirmar si debe notificarse siempre por ambos canales o según preferencias del paciente → fijado en «Contratos fijados» (correo vía webhook; WhatsApp pendiente de Spec 009; «cuando corresponda» = canal implementado y configurado).
- [RESUELTA — Q3] Definir el contenido exacto del aviso de cancelación → fijado en «Contratos fijados» (asunto «Cita cancelada», estado «Cancelada», pie de reagendado, literales contractuales).
- [RESUELTA — 2026-10-23] ¿Renumerar los RF tras consolidar los «Contratos fijados»? → **no**: se conservan RF-1..RF-4 para mantener la trazabilidad con `plan.md`, los tests `TC-010-*` y la evidencia de HU-010 ya cerrada; los RF consolidados y nuevos se añaden con números libres (RF-5..RF-10).
- [RESUELTA — 2026-10-23] Enmienda de esta spec (título ampliado, RF-5..RF-7 consolidados y RF-8..RF-10 nuevos) → **aprobada por la usuaria el 2026-10-23**. El comportamiento vigente es RF-1..RF-7 (implementados); RF-8..RF-10 quedan [PENDIENTE DE IMPLEMENTACIÓN] y no deben implementarse hasta autorización de la fase de planificación.

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
3. **Nuevo requisito pendiente**: el evento de negocio `appointment.cancelled`
   (v1) en RF-8..RF-10, marcados **[PENDIENTE DE IMPLEMENTACIÓN]**. El texto
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
