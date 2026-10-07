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

## Criterios de finalización
Todos los RF con test en verde y demo manual de una reserva con confirmación por correo.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Definir el contenido completo y formato del mensaje de confirmación.
- [NECESITA ACLARACIÓN] Definir el comportamiento ante un fallo de entrega.
