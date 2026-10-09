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
Todos los RF con test en verde, incluida concurrencia y regresión de disponibilidad/agendamiento, más demo manual del flujo antes-durante-después de una reserva. El contrato de datos y los literales de la sección siguiente forman parte de la verificación.

## Literales y contrato (enmienda 2026-10-09, aprobada por la usuaria)

Los literales de esta tabla son contrato (AGENTS.md «Textos contractuales»): sus
claves técnicas viven en `consultorio/content/appointment_content.py` y su espejo en
`tests/expected_content.py`, y cambian junto con esta spec en el mismo PR.

| Literal | Texto | RF |
|---|---|---|
| `MSG_SUBMITTING` | Registrando tu cita… | RF-5 |
| `MSG_SLOT_TAKEN` (reutilizado; fijado en Spec 004) | Ese horario ya no está disponible. Selecciona otro horario. | RF-2, RF-3, RF-4 |
| `MSG_OCCUPIED_HOUR` (reutilizado; fijado en Spec 005) | Ocupado | RF-4 |

Contrato de datos que soporta los RF (el detalle de rutas, métodos y códigos vive en
el plan asociado):

- **Clave de unicidad**: exclusivamente `servicio + fecha + hora`. Una única cita
  válida por esa combinación. [RF-1, RF-2, RF-6]
- `POST /citas` sobre un horario libre → `303` a la confirmación con exactamente
  1 fila nueva. [RF-1]
- `POST /citas` sobre una combinación ya reservada **o reintento idéntico de una
  solicitud ya registrada** → `200` re-renderizando el formulario con
  `MSG_SLOT_TAKEN`, **0 filas** nuevas y la hora servida como «Ocupado» (sin radio
  seleccionable). [RF-2, RF-3, RF-4, caso «Reintento de una misma solicitud»]
- **Concurrencia**: de N solicitudes simultáneas sobre la misma combinación, máximo
  1 registra cita (`303`) y las restantes se rechazan con el mismo literal (`200`);
  la integridad la garantiza el índice `UNIQUE (service, date, time)` en el punto de
  persistencia. [RF-3, RF-6]
- **Estado en curso**: mientras se procesa el envío, el botón de envío queda
  deshabilitado, muestra `MSG_SUBMITTING` y el formulario marca `aria-busy`; un
  envío repetido mientras está en curso se bloquea en el cliente (sin segundo
  `POST`). El estado permanece visible al menos **700 ms** (`SUBMITTING_MIN_MS`,
  enmienda 2026-10-09) antes de enviar el formulario; si el servidor tarda más,
  se mantiene hasta la navegación. La espera mínima queda cubierta por el mismo
  bloqueo de envíos repetidos. [RF-5]

## Duplicados históricos (duda cerrada 2026-10-09, usuaria)

- **Prevención**: el índice `UNIQUE (service, date, time)` impide la creación de
  nuevos duplicados desde la creación de la tabla.
- **Detección**: los tests ejecutan el diagnóstico
  `SELECT service, date, time FROM appointments GROUP BY service, date, time
  HAVING COUNT(*) > 1` y exigen 0 filas.
- **Sin saneamiento automático**: ante duplicados reales se requiere decisión
  explícita de la usuaria con respaldo/auditoría previo (AGENTS.md «Base de datos e
  integridad»); esta HU solo garantiza que no se creen nuevos ni que pasen
  desapercibidos.

## Dudas cerradas

- **Política de duplicados históricos (cerrada 2026-10-09, usuaria)**: prevenir con el
  índice `UNIQUE` y detectar mediante diagnóstico en los tests, **sin saneamiento
  automático**; cualquier limpieza exige decisión explícita de la usuaria con
  respaldo/auditoría previo. Detalle en «Duplicados históricos».
- **Duración mínima del estado en curso (cerrada 2026-10-09, usuaria; observación
  «El mensaje de «Registrando tu cita…» es muy rápido»)**: el estado debe percibirse
  incluso con respuestas casi instantáneas → mínimo **700 ms** visibles antes de
  enviar el formulario (`SUBMITTING_MIN_MS = 700`, decisión D13 del plan).
