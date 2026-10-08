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

## Datos y literales aprobados (enmienda 2026-10-09)

### Datos obligatorios del paciente (duda Q1 cerrada)
El formulario de `/citas` contiene exactamente 8 campos obligatorios. No se piden
otros datos (dirección, motivo de consulta ni teléfono fijo están fuera de alcance):

| Campo (`name`) | Regla |
|---|---|
| `service` | Clave de un servicio ofrecido por el consultorio (RF-5) |
| `date` | ISO `YYYY-MM-DD`; de lunes a viernes; no anterior a hoy |
| `time` | Una de las horas de `BOOKING_HOURS` |
| `document_type` | Uno de: CC, TI, CE, PASSPORT, RC |
| `document_number` | Solo dígitos, entre 4 y 20 |
| `patient_name` | Nombre y apellido, 3–120 caracteres |
| `email` | Correo electrónico válido |
| `phone` | Solo dígitos, entre 7 y 15 (celular) |

Si el paciente es menor de edad, registra los datos del representante con su
documento; si es extranjero, puede usar pasaporte o cédula de extranjería
(texto auxiliar del formulario).

### Estado inicial de la cita (duda Q2 cerrada)
- `pending`, etiqueta visible «Pendiente».

### Catálogo de horas
Bloques de 30 minutos; solo lunes a viernes. La mañana termina a las 12:00 y la
tarde comienza a las 14:00 (12:00–14:00 libre). Las 14 horas exactas son:
`08:00`, `08:30`, `09:00`, `09:30`, `10:00`, `10:30`, `11:00`, `11:30`,
`14:00`, `14:30`, `15:00`, `15:30`, `16:00`, `16:30`.

### Literales de mensaje (contrato textual)
| Literal | Texto |
|---|---|
| Servicio ausente | Selecciona un servicio. |
| Servicio inválido | Selecciona un servicio válido. |
| Fecha ausente | Selecciona una fecha. |
| Fecha inválida | Selecciona una fecha válida de lunes a viernes, no anterior a hoy. |
| Hora ausente | Selecciona una hora. |
| Hora inválida | Selecciona una hora válida. |
| Tipo de documento ausente | Selecciona un tipo de documento. |
| Número de documento ausente | Ingresa el número de documento. |
| Número de documento inválido | El número de documento debe tener entre 4 y 20 dígitos. |
| Nombre ausente | Ingresa tu nombre y apellidos. |
| Nombre inválido | El nombre debe tener entre 3 y 120 caracteres. |
| Correo ausente | Ingresa tu correo electrónico. |
| Correo inválido | Ingresa un correo electrónico válido. |
| Celular ausente | Ingresa tu celular. |
| Celular inválido | Ingresa un celular válido (entre 7 y 15 dígitos). |
| Horario ocupado (RF-3) | Ese horario ya no está disponible. Selecciona otro horario. |
| Fecha sin horas | No hay horarios disponibles para esta fecha. |
| Confirmación (título) | Cita registrada |
| Estado inicial | Pendiente |

## Criterios de finalización
Todos los RF con test en verde, incluyendo datos inválidos y pérdida de disponibilidad, más demo manual del flujo completo de reserva.

## Dudas abiertas
- ~~[NECESITA ACLARACIÓN] Confirmar los datos obligatorios definitivos del paciente.~~
  **Cerrada 2026-10-09**: tipo y número de documento (solo dígitos), nombre y
  apellido, correo electrónico y celular (solo dígitos), más servicio, fecha y hora.
- ~~[NECESITA ACLARACIÓN] Confirmar el estado inicial definitivo de una cita.~~
  **Cerrada 2026-10-09**: `pending` («Pendiente»).
