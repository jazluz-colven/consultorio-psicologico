# Spec 006 — Evitar doble reserva de citas

## Contexto y objetivo
Una doble reserva sobre el mismo horario genera conflictos de agenda y deteriora la confianza del paciente y del consultorio. Esta funcionalidad garantiza que un horario no pueda quedar reservado por más de una cita válida, incluso cuando dos intentos ocurran de forma concurrente, y que el paciente reciba una respuesta clara cuando el horario ya no esté disponible.

## Usuarios / actores
- Paciente.
- Psicólogo.

## Historias de usuario
- H1: Como psicólogo quiero que el sistema impida registrar dos citas en el mismo horario para evitar conflictos en la agenda.
- H2: Como paciente quiero recibir una respuesta clara cuando mi horario deje de estar disponible para poder seleccionar otra opción.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO un paciente intente reservar un horario libre, EL SISTEMA permitirá registrar una única cita válida.
- RF-2: SI un horario ya está reservado, ENTONCES EL SISTEMA impedirá registrar otra cita sobre la misma combinación de servicio, fecha y hora.
- RF-3: SI dos intentos concurrentes buscan registrar la misma combinación de servicio, fecha y hora, ENTONCES EL SISTEMA permitirá como máximo una reserva válida y rechazará las restantes.
- RF-4: SI el horario deja de estar disponible después de haber sido mostrado como libre, ENTONCES EL SISTEMA rechazará el intento posterior e informará que el horario ya no está disponible.
- RF-5: MIENTRAS se procesa una solicitud de reserva, EL SISTEMA mostrará un estado que indique que la operación está en curso y evitará acciones duplicadas del usuario.
- RF-6: EL SISTEMA mantendrá la integridad de las reservas frente a duplicados y solicitudes concurrentes.

## Requisitos no funcionales
- Integridad y consistencia de las reservas.
- Respuesta clara ante conflictos.
- Experiencia usable durante el procesamiento de una reserva.

## Casos límite
- Dos o más intentos simultáneos sobre el mismo horario.
- Horario ocupado después de mostrarse disponible.
- Registros históricos duplicados.
- Reintento de una misma solicitud.
- Cambio de servicio después de consultar un horario.

## Fuera de alcance
- Automatizaciones posteriores a la reserva; corresponden a la funcionalidad vigente de HU-007.
- Notificaciones por correo o WhatsApp.
- Cancelación de citas.

## Criterios de finalización
Todos los RF con test en verde, incluida concurrencia y regresión de disponibilidad/agendamiento, más demo manual del flujo antes-durante-después de una reserva.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Confirmar la política definitiva para tratar duplicados históricos si aparecen antes del cierre.
