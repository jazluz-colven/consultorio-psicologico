# Spec 009 — Enviar confirmación por WhatsApp

## Contexto y objetivo
El paciente puede necesitar una confirmación accesible y cercana de su cita para recordar la reserva. Esta funcionalidad busca enviar automáticamente un mensaje de WhatsApp después de registrar una cita, manteniendo la reserva válida aunque la notificación no pueda enviarse.

## Usuarios / actores
- Paciente.

## Historias de usuario
- H1: Como paciente quiero recibir un mensaje de WhatsApp para recordar la cita agendada.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO una cita sea registrada correctamente, EL SISTEMA iniciará el envío de una confirmación al número registrado.
- RF-2: CUANDO el envío sea realizado, EL SISTEMA comunicará la información aprobada de la cita.
- RF-3: SI el servicio de mensajería no está disponible, ENTONCES EL SISTEMA mantendrá válida la cita y registrará el problema de notificación.
- RF-4: SI el envío falla o requiere reintento, ENTONCES EL SISTEMA evitará notificaciones duplicadas de la misma reserva según la regla aprobada.
- RF-5: EL SISTEMA utilizará un mensaje de confirmación previamente aprobado.

## Requisitos no funcionales
- Seguridad de datos personales y credenciales de mensajería.
- Trazabilidad de envíos y errores.
- Tolerancia a fallos del servicio externo.

## Casos límite
- Número ausente o inválido.
- Servicio externo indisponible.
- Timeout.
- Reintentos.
- Mensaje duplicado.
- Cambio de datos de la cita antes del envío.

## Fuera de alcance
- Cancelación de citas.
- Mensajería promocional.
- Conversaciones bidireccionales con pacientes.

## Criterios de finalización
Todos los RF con test en verde y demo manual de confirmación, error y reintento controlado.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Confirmar proveedor/canal de WhatsApp.
- [NECESITA ACLARACIÓN] Aprobar plantilla y contenido exacto del mensaje.
- [NECESITA ACLARACIÓN] Definir política de reintentos.
