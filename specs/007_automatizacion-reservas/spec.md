# Spec 007 — Automatización de reservas mediante n8n

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

## Fuera de alcance
- Automatizaciones que cancelen o modifiquen una reserva sin una regla de negocio aprobada.
- Convertir la automatización en requisito para confirmar una cita.
- Notificaciones específicas de correo o WhatsApp que pertenezcan a otras historias.

## Criterios de finalización
Todos los RF con test en verde, incluyendo indisponibilidad, errores, reintentos y duplicados, más demo manual de una automatización posterior a una reserva confirmada.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Definir cuáles serán las automatizaciones administrativas incluidas en el primer incremento.
- [NECESITA ACLARACIÓN] Confirmar qué datos son estrictamente necesarios para cada automatización.

> Nota de trazabilidad: el backlog histórico v2.0 identificaba HU-007 como cancelación de cita; la actualización posterior del mismo documento redefine HU-007 como automatización mediante n8n. Esta especificación toma la definición más reciente como vigente.
