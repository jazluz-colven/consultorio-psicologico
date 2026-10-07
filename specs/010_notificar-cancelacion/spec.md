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

## Criterios de finalización
Todos los RF con test en verde y demo manual de cancelación con notificación por los canales disponibles.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Confirmar si debe notificarse siempre por ambos canales o según preferencias del paciente.
- [NECESITA ACLARACIÓN] Definir el contenido exacto del aviso de cancelación.
