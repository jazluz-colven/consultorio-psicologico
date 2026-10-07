# Spec 005 — Validar disponibilidad de horarios

## Contexto y objetivo
El paciente necesita seleccionar únicamente horarios que puedan ser reservados. La funcionalidad debe reflejar el estado vigente de la agenda para evitar selecciones inválidas, mantener coherencia después de registrar una cita y comunicar claramente cuándo no existen horarios disponibles.

## Usuarios / actores
- Paciente.

## Historias de usuario
- H1: Como paciente quiero visualizar únicamente horarios disponibles para evitar seleccionar un horario ocupado.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO el paciente consulte el calendario, EL SISTEMA mostrará como disponibles únicamente los horarios libres.
- RF-2: SI un horario ya está ocupado, ENTONCES EL SISTEMA no permitirá seleccionarlo como disponible.
- RF-3: CUANDO el paciente cambie de fecha, EL SISTEMA actualizará los horarios mostrados para corresponder exclusivamente a la fecha consultada.
- RF-4: CUANDO no existan horarios disponibles para una fecha, EL SISTEMA informará esa situación de forma clara.
- RF-5: CUANDO una cita sea registrada y el paciente vuelva a consultar la disponibilidad, EL SISTEMA reflejará el horario utilizado como no disponible.
- RF-6: EL SISTEMA mantendrá una distinción comprensible entre horarios disponibles y no disponibles.

## Requisitos no funcionales
- La disponibilidad debe actualizarse de forma consistente y perceptible para el usuario.
- Los estados no deben depender únicamente del color para ser comprendidos.

## Casos límite
- Fecha sin horarios.
- Cambio rápido entre fechas.
- Cambio de servicio con un horario previamente ocupado.
- Horario que pasa a ocupado mientras el paciente consulta.
- Reconsulta de la misma fecha después de una reserva.

## Fuera de alcance
- Prevención de concurrencia como objetivo independiente; corresponde a HU-006.
- Notificaciones posteriores a la reserva.

## Criterios de finalización
Todos los RF con test en verde, incluida actualización tras reserva y cambios de fecha/servicio, más demo manual del calendario.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Confirmar si la disponibilidad depende exclusivamente de servicio + fecha + hora o de reglas adicionales.
