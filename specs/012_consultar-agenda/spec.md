# Spec 012 — Consultar la agenda por fecha

## Contexto y objetivo
La planificación profesional requiere consultar la agenda más allá del día actual. Esta funcionalidad permite seleccionar una fecha y obtener exclusivamente las citas correspondientes a ella, facilitando la organización anticipada y la revisión de jornadas anteriores.

## Usuarios / actores
- Psicólogo.

## Historias de usuario
- H1: Como psicólogo quiero consultar la agenda de cualquier fecha para planificar mi trabajo.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO el psicólogo seleccione una fecha, EL SISTEMA mostrará únicamente las citas correspondientes a ese día.
- RF-2: CUANDO el psicólogo cambie la fecha consultada, EL SISTEMA actualizará la agenda para mostrar exclusivamente la nueva fecha.
- RF-3: SI no existen citas en la fecha seleccionada, ENTONCES EL SISTEMA informará que no existen citas para ese día.
- RF-4: EL SISTEMA mantendrá el acceso a esta consulta restringido a usuarios autorizados.

## Requisitos no funcionales
- Protección de datos personales.
- Respuesta comprensible y consistente al cambiar de fecha.

## Casos límite
- Fecha sin citas.
- Fecha inválida.
- Cambio rápido entre fechas.
- Citas canceladas en la fecha consultada.

## Fuera de alcance
- Creación, modificación o cancelación de citas desde la consulta.
- Informes estadísticos de la agenda.

## Criterios de finalización
Todos los RF con test en verde y demo manual de consulta para varias fechas con y sin citas.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Confirmar si existe un límite de fechas consultables.
