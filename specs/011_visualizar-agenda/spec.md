# Spec 011 — Visualizar la agenda diaria

## Contexto y objetivo
El psicólogo necesita una visión consolidada de las citas del día para organizar la atención y conocer qué pacientes debe atender. La funcionalidad debe presentar las citas correspondientes al día con la información necesaria para la gestión de la jornada.

## Usuarios / actores
- Psicólogo.

## Historias de usuario
- H1: Como psicólogo quiero consultar mi agenda diaria para organizar la atención de los pacientes.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO el psicólogo acceda a la agenda diaria, EL SISTEMA mostrará las citas del día.
- RF-2: CUANDO una cita sea mostrada en la agenda, EL SISTEMA mostrará el nombre del paciente, hora, servicio y estado.
- RF-3: SI no existen citas para el día consultado, ENTONCES EL SISTEMA informará que la agenda está vacía.
- RF-4: EL SISTEMA restringirá la consulta de la agenda a usuarios con autorización para visualizarla.

## Requisitos no funcionales
- Protección de datos personales y acceso restringido.
- Información legible y ordenada para facilitar la gestión de la jornada.

## Casos límite
- Día sin citas.
- Cita cancelada.
- Múltiples citas en horarios próximos.
- Datos incompletos de una cita.

## Fuera de alcance
- Consulta de fechas históricas o futuras arbitrarias; corresponde a HU-012.
- Modificación de citas.
- Creación de citas desde la agenda.

## Criterios de finalización
Todos los RF con test en verde y demo manual de una agenda con citas y una agenda vacía.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Definir qué roles adicionales, además del psicólogo, podrán consultar la agenda.
