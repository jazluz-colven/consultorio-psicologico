# Spec 008 — Enviar confirmación por correo electrónico

## Contexto y objetivo
El paciente necesita un comprobante de su reserva para reducir incertidumbre y conservar los datos esenciales de la cita. La funcionalidad debe enviar una confirmación cuando el registro de la cita haya finalizado correctamente.

## Usuarios / actores
- Paciente.

## Historias de usuario
- H1: Como paciente quiero recibir un correo electrónico al agendar una cita para tener un comprobante de la reserva.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO una cita sea registrada correctamente, EL SISTEMA enviará una confirmación por correo electrónico.
- RF-2: CUANDO se envíe la confirmación, EL SISTEMA incluirá la fecha, hora, servicio y estado de la cita.
- RF-3: SI la cita no ha sido registrada correctamente, ENTONCES EL SISTEMA no enviará una confirmación que represente la reserva como válida.
- RF-4: EL SISTEMA asociará la confirmación a la cita que originó el envío.

## Requisitos no funcionales
- Protección de los datos personales contenidos en la comunicación.
- Entrega de información clara y legible.

## Casos límite
- Correo del paciente inválido o ausente.
- Error de envío.
- Envío duplicado para una misma reserva.
- Datos de la cita incompletos.

## Fuera de alcance
- Confirmación por WhatsApp.
- Notificación de cancelación.
- Gestión de campañas o correos masivos.
- Envío de correo directo desde la aplicación (SMTP propio): el transporte lo gestiona n8n.

## Contratos fijados (enmienda 2026-10-10)

Cierra las dudas [NECESITA ACLARACIÓN] y fija el mecanismo aprobado por la usuaria.

### Mecanismo — envío vía n8n (Q3)
- CUANDO una cita se registre correctamente, EL SISTEMA emitirá el evento estructurado `appointment.confirmation_email` (versión 1) al webhook de automatización configurado (`AUTOMATION_WEBHOOK_URL`, con `AUTOMATION_WEBHOOK_AUTH_HEADER` si existe). n8n recibirá el evento y enviará el correo al paciente con el mensaje incluido en el payload (RF-1).
- La aplicación compondrá el mensaje (asunto, texto plano y HTML); n8n solo lo transporta (RF-2). El workflow de n8n vive fuera del repositorio (ver «Contrato de integración en n8n»).
- El evento de HU-007 (`appointment.confirmed`) permanece intacto, sin datos personales e independiente de este.

### Registro y deduplicación (RF-4)
- La confirmación se registrará en la tabla `automation_events` (HU-007) con `event_id` determinista `appointment.confirmation_email:{appointment.id}:v1` y `UNIQUE(event_id)`: un solo envío por reserva, sin duplicados ante reprocesos, en el punto de persistencia.
- Estados: `pending` → `sent` | `skipped` | `failed`, con `detail` en español.

### Payload del evento (contrato)
```json
{
  "event_id": "appointment.confirmation_email:34:v1",
  "event_type": "appointment.confirmation_email",
  "event_version": 1,
  "occurred_at": "2026-10-10 12:34:56",
  "recipient": { "to": "paciente@ejemplo.com", "patient_name": "Ana Pérez" },
  "message": { "subject": "…", "text": "…", "html": "…" },
  "appointment": { "id": 34, "service": "individual", "date": "2026-10-15", "time": "10:00", "status": "pending" }
}
```
- `recipient` y `message` son exclusivos de este tipo de evento; es una excepción documentada a la minimización de datos: el correo no puede llegar sin destinatario ni mensaje.
- Campos excluidos: `document_type`, `document_number`, `phone`.

### Contenido del mensaje (cierra Q1)
- Asunto: «Confirmación de tu cita — {servicio} · {fecha legible en español} · {hora}».
- Cuerpo multipart: texto plano + HTML con la paleta Serenidad Natural, estilos inline y sin recursos remotos.
- Contenido mínimo: saludo con el nombre del paciente, servicio, fecha, hora, estado «Confirmada», Referencia #{id} y pie de comprobante.
  - **Enmienda 2026-10-11**: el estado mostrado era «Pendiente» (estado inicial
    de la cita en la spec 004 original); la spec 004 cambia el estado inicial a
    `confirmed` («Confirmada») y este copy la sigue. El campo `status` del
    payload pasa a `confirmed`; la forma del payload no cambia
    (`event_version` permanece en 1).
- Los literales son contractuales: sus valores viven en `consultorio/content/email_content.py` y se reflejan en `tests/expected_content.py`; cambiar un copy obliga a PR de spec primero.

### Fallo de entrega (cierra Q2)
- Mejor esfuerzo: SI el webhook falla (timeout, servicio no disponible o respuesta no válida), ENTONCES el evento quedará `failed` con su motivo en español, la cita permanecerá intacta y el paciente verá la confirmación de la reserva.
- Sin reintentos automáticos; la re-ejecución la decide el administrador y el `UNIQUE(event_id)` impide el duplicado.

### Contrato de integración en n8n (fuera del repositorio)
- El workflow enrutará por `event_type == "appointment.confirmation_email"` y enviará un correo con: To = `recipient.to`, Subject = `message.subject`, cuerpo texto = `message.text` y alternativa HTML = `message.html`.
- La autenticación del webhook es la misma de HU-007 (`AUTOMATION_WEBHOOK_AUTH_HEADER`; el token es secreto de entorno).
- La configuración del workflow y del servidor SMTP de n8n vive en n8n, no en el repositorio.

## Criterios de finalización
Todos los RF con test en verde y demo manual de una reserva con confirmación por correo (evento emitido y correo recibido vía n8n).

## Dudas abiertas
- [RESUELTA — Q1] Contenido completo y formato del mensaje → fijado en «Contratos fijados» (multipart texto + HTML con paleta).
- [RESUELTA — Q2] Comportamiento ante un fallo de entrega → fijado en «Contratos fijados» (best-effort, sin reintentos).

## Enmienda 2026-10-13 — enlace de cancelación en el correo (Spec 017)

Por decisión de la usuaria (Q7 de la Spec 017, 2026-10-13), el correo de
confirmación incluirá un **enlace directo a la cancelación de la cita**. El
formato literal del enlace (ruta y copy) se fija en el `plan.md` de la Spec
017 junto con el resto de literales del flujo de cancelación. Esta enmienda
no altera los literales ya contractuales de esta spec (asunto, cabecera, pie,
estado); se implementará junto con la HU-017 y los tests de HU-008 siguen
vigentes tal como están.
