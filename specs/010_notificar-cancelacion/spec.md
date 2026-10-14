# Spec 010 — Notificar la cancelación de una cita

## Contexto y objetivo
Cuando una cita cambia a estado cancelado, el paciente necesita conocer oportunamente la modificación para evitar desplazamientos innecesarios y mantener información confiable sobre su atención. La funcionalidad comunica la cancelación mediante los canales aprobados.

## Usuarios / actores
- Paciente.

## Historias de usuario
- H1: Como paciente quiero recibir una notificación cuando una cita sea cancelada para estar informado oportunamente.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO una cita cambie a estado Cancelada y el cambio sea confirmado, EL SISTEMA enviará una notificación de cancelación.
- RF-2: CUANDO se envíe la notificación, EL SISTEMA indicará claramente que la cita fue cancelada.
- RF-3: CUANDO corresponda, EL SISTEMA enviará la notificación por correo electrónico y WhatsApp.
- RF-4: SI una cancelación ya fue notificada, ENTONCES EL SISTEMA evitará duplicar la misma notificación sin una causa válida.

## Requisitos no funcionales
- Protección de datos personales.
- Trazabilidad del cambio y de las notificaciones.
- Claridad del mensaje para evitar interpretaciones ambiguas.

## Casos límite
- Cita ya cancelada.
- Fallo de uno de los canales de notificación.
- Datos de contacto incompletos.
- Cancelación repetida.

## Fuera de alcance
- Reprogramación automática.
- Gestión de campañas de comunicación.
- Definición de políticas de cancelación.
- Interfaz o endpoint para cancelar (la cancelación es un servicio interno sin UI; una interfaz sería otra historia).
- Notificación por WhatsApp: canal pendiente de la Spec 009.
- Tabla de auditoría de cambios de estado.
- Reintentos automáticos de notificación fallida.

## Contratos fijados (enmienda 2026-10-13)

Cierra las dudas [NECESITA ACLARACIÓN] y fija el mecanismo aprobado por la
usuaria (decisiones Q1–Q4 del `plan.md` §7.1).

### Transición de estado y disparador (cierra Q1)
- La cita pasa de `confirmed` («Confirmada») a **`cancelled` («Cancelada»)** mediante el servicio interno `cancel_appointment()`; **sin endpoint ni interfaz** (fuera de alcance).
- «El cambio sea confirmado» = el cambio de estado queda **confirmado en persistencia** (commit) antes de notificar: el sistema notifica solo si la transición se realizó.
- SI la cita no existe o ya estaba cancelada, ENTONCES el sistema no cambia nada y **no envía notificación** (RF-1, RF-4, casos límite «Cita ya cancelada» y «Cancelación repetida»).

### Canales de notificación (cierra Q2, RF-3)
- **Correo electrónico**: notificación funcional mediante el **mismo webhook de automatización de HU-007/HU-008** (`AUTOMATION_WEBHOOK_URL`, con `AUTOMATION_WEBHOOK_AUTH_HEADER` si existe). La aplicación compone el mensaje y emite el evento estructurado; n8n solo transporta.
- **WhatsApp**: canal **pendiente de la Spec 009**; no se emite ni se registra evento de WhatsApp en esta funcionalidad.
- «Cuando corresponda» = **canal implementado y configurado**: hoy el correo; si el webhook no está configurado, el evento de correo queda `skipped` y el sistema opera igual (la cancelación no depende de la notificación).

### Registro y deduplicación (RF-4)
- Cada notificación de correo se registra en la tabla `automation_events` (HU-007) con `event_id` determinista `appointment.cancellation_email:{appointment.id}:v1` y `UNIQUE(event_id)`: una sola notificación por cancelación, sin duplicados ante reprocesos, en el punto de persistencia.
- La cancelación repetida no vuelve a notificar: la transición condicional `confirmed → cancelled` solo dispara la notificación la primera vez.
- Estados: `pending` → `sent` | `skipped` | `failed`, con `detail` en español.

### Payload del evento (contrato)
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

### Fallo de entrega
- Mejor esfuerzo: SI el webhook falla (timeout, servicio no disponible o respuesta no válida), ENTONCES el evento quedará `failed` con su motivo en español y **la cancelación permanece confirmada** (nunca se revierte ni se bloquea por un fallo de notificación).
- Sin reintentos automáticos; la re-ejecución la decide el administrador y el `UNIQUE(event_id)` impide el duplicado.

### Liberación del horario (cierra Q4)
- CUANDO una cita sea cancelada, EL SISTEMA **liberá su horario**: la disponibilidad (`/citas/horarios` y `/citas/disponibilidad`) no contará las citas canceladas y el horario podrá reservarse de nuevo.
- La unicidad de `servicio + fecha + hora` se mantiene **entre citas no canceladas**: se sustituye el `UNIQUE` de la tabla por un **índice único parcial** `WHERE status <> 'cancelled'`, con migración idempotente de las bases existentes, respaldo previo del fichero y aborto si existieran duplicados entre citas no canceladas.
- La protección contra doble reserva de las citas no canceladas permanece intacta.

## Criterios de finalización
Todos los RF con test en verde y demo manual de cancelación con notificación por los canales disponibles.

## Dudas abiertas
- [RESUELTA — Q2] Confirmar si debe notificarse siempre por ambos canales o según preferencias del paciente → fijado en «Contratos fijados» (correo vía webhook; WhatsApp pendiente de Spec 009; «cuando corresponda» = canal implementado y configurado).
- [RESUELTA — Q3] Definir el contenido exacto del aviso de cancelación → fijado en «Contratos fijados» (asunto «Cita cancelada», estado «Cancelada», pie de reagendado, literales contractuales).
