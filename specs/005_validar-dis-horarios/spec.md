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
Todos los RF con test en verde, incluida actualización tras reserva y cambios de fecha/servicio, más demo manual del calendario. El contrato de datos y los literales de la sección siguiente forman parte de la verificación.

## Literales y contrato (enmienda 2026-10-09, aprobada por la usuaria)

Los literales de esta tabla son contrato (AGENTS.md «Textos contractuales»): sus
claves técnicas viven en `consultorio/content/appointment_content.py` y su espejo en
`tests/expected_content.py`, y cambian junto con esta spec en el mismo PR.

| Literal | Texto | RF |
|---|---|---|
| `MSG_NO_HOURS` (reutilizado; fijado en Spec 004 como base de esta HU) | No hay horarios disponibles para esta fecha. | RF-4 |
| `MSG_OCCUPIED_HOUR` | Ocupado | RF-2, RF-6 |
| `MSG_CHECKING_HOURS` | Consultando disponibilidad… | RNF (actualización perceptible) |
| `CALENDAR_LEGEND_FREE` | Con horarios disponibles | RF-6 |
| `CALENDAR_LEGEND_FULL` | Sin horarios disponibles | RF-4, RF-6 |
| `DAY_LABEL_NO_HOURS` | «, sin horarios disponibles» (sufijo del aria-label de un día sin horarios libres) | RF-6 |

Contrato de datos que soporta los RF (el detalle de rutas, métodos y códigos vive en
el plan asociado):

- `GET /citas/horarios?service=…&date=…` → JSON con `available` (horas libres) y
  `occupied` (horas ya reservadas) para la terna servicio+fecha.
  [RF-1, RF-2, RF-5, RF-6]
- `GET /citas/disponibilidad?service=…&month=YYYY-MM` → JSON con `days` (días
  laborables ≥ hoy con al menos una hora libre para el servicio; lista vacía si no
  hay ninguno). [RF-1, RF-4]

## Dudas cerradas

- **Regla de disponibilidad (cerrada 2026-10-09, usuaria)**: la disponibilidad
  depende exclusivamente de la combinación `servicio + fecha + hora`; no se aplican
  reglas adicionales (cupos por día, anticipación máxima, etc.). Coherente con la
  Spec 006 RF-2 («la misma combinación de servicio, fecha y hora»).
