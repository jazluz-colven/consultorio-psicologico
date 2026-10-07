# Spec 004 — Agendar una cita

## Contexto y objetivo
La reserva de una cita permite convertir el interés del paciente en una atención programada. La funcionalidad debe permitir seleccionar un horario disponible, registrar los datos necesarios y confirmar la reserva, evitando registrar citas inválidas o sobre horarios que hayan dejado de estar disponibles.

## Usuarios / actores
- Paciente.

## Historias de usuario
- H1: Como paciente quiero seleccionar un horario disponible y registrar mis datos para agendar una cita con el psicólogo.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO existan horarios disponibles y el paciente complete los datos obligatorios, EL SISTEMA registrará la cita y mostrará la confirmación.
- RF-2: SI falta un dato obligatorio o existe un dato inválido, ENTONCES EL SISTEMA no registrará la cita e indicará la información que debe corregirse.
- RF-3: SI el horario seleccionado deja de estar disponible antes de confirmar, ENTONCES EL SISTEMA rechazará la reserva e indicará que debe seleccionarse otro horario.
- RF-4: CUANDO una cita sea registrada correctamente, EL SISTEMA la asociará al paciente, servicio, fecha, hora y estado correspondiente.
- RF-5: EL SISTEMA verificará que el servicio seleccionado corresponda a un servicio ofrecido por el consultorio.

## Requisitos no funcionales
- La información solicitada al paciente debe limitarse a los datos necesarios para el flujo aprobado.
- El flujo debe ser comprensible y usable en escritorio y móvil.

## Casos límite
- Datos obligatorios vacíos.
- Datos inválidos.
- Horario que cambia de disponible a ocupado antes de confirmar.
- Dos intentos de reserva sobre el mismo horario.
- Servicio no válido.

## Fuera de alcance
- Confirmaciones por correo o WhatsApp.
- Cancelación de citas.
- Agenda interna del psicólogo.

## Criterios de finalización
Todos los RF con test en verde, incluyendo datos inválidos y pérdida de disponibilidad, más demo manual del flujo completo de reserva.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Confirmar los datos obligatorios definitivos del paciente.
- [NECESITA ACLARACIÓN] Confirmar el estado inicial definitivo de una cita.
