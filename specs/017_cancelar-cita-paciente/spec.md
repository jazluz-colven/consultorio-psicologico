# Spec 017 — Cancelar una cita por parte del paciente

## Contexto y objetivo
El paciente puede agendar una cita (Spec 004) y recibir la confirmación por
correo (Spec 008), pero todavía no puede cancelarla por sí mismo: la
cancelación existe como servicio interno sin interfaz (Spec 010). Cuando los
planes del paciente cambian, la única vía es contactar al consultorio, lo que
retrasa la liberación del horario y la actualización de la agenda. Esta
funcionalidad permite al paciente cancelar su propia cita desde el sitio,
reutilizando la capa de cancelación, liberación de horario y notificación ya
aprobada (Spec 010) sin reescribirla.

## Usuarios / actores
- Paciente titular de la cita (actor principal, no autenticado).
- Visitante sin cita: puede acceder a las páginas del flujo, pero no puede
  cancelar una cita que no le corresponde.
- Psicóloga / consultorio: destinataria de la notificación y de la agenda
  liberada, sin interfaz propia en esta spec (Specs 011/012).

## Historias de usuario
- H1: Como paciente quiero cancelar mi propia cita desde el sitio cuando ya no
  pueda asistir, para liberar el horario y recibir la confirmación de la
  cancelación.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO el paciente solicite cancelar una cita, EL SISTEMA verificará
  que la cita exista y que el número de referencia y el número de documento
  de documento correspondan a esa cita antes de realizar cualquier cambio.
- RF-2: SI la cita no existe, ya fue cancelada o los datos de identificación
  no coinciden, ENTONCES EL SISTEMA no realizará ningún cambio y mostrará un
  mensaje claro en español, sin revelar datos de la cita.
- RF-3: CUANDO el paciente solicite cancelar una cita, EL SISTEMA mostrará
  primero una pantalla de confirmación con el resumen de la cita (servicio,
  fecha legible, hora y estado) antes de realizar cualquier cambio.
- RF-4: SI la cita comienza en menos de 3 horas (incluidas la hora ya iniciada
  y la ya pasada), ENTONCES EL SISTEMA no permitirá cancelarla desde el sitio
  y mostrará un mensaje claro que indique la restricción y remita al
  consultorio.
- RF-5: CUANDO la cancelación sea confirmada en la pantalla de resumen, EL
  SISTEMA pondrá la cita en estado Cancelada mediante el servicio de
  cancelación de la Spec 010, sin crear una segunda lógica de cancelación.
- RF-6: CUANDO una cita sea cancelada, EL SISTEMA liberá su horario (garantía
  ya establecida por la Spec 010: el hueco vuelve a estar disponible y puede
  reservarse de nuevo).
- RF-7: CUANDO la cancelación quede registrada, EL SISTEMA mostrará una
  pantalla de éxito con el estado «Cancelada», los datos de la cita cancelada
  y su referencia.
- RF-8: CUANDO una cita sea cancelada desde el sitio, EL SISTEMA enviará la
  notificación de cancelación aprobada en la Spec 010, sin duplicar la
  notificación si la cancelación se reintenta.
- RF-9: SI el paciente reintenta o recarga la cancelación de una cita ya
  cancelada, ENTONCES EL SISTEMA indicará que la cita ya está cancelada, sin
  producir una segunda cancelación ni una segunda notificación.
- RF-10: CUANDO el formulario de cancelación esté en proceso de envío, EL
  SISTEMA evitará cancelaciones duplicadas por un doble clic o un doble
  envío.
- RF-11: CUANDO el paciente visite la página de una cita ya cancelada, EL
  SISTEMA mostrará el estado «Cancelada» de la cita.
- RF-12: CUANDO el paciente visite la página de una cita confirmada, EL
  SISTEMA mostrará un botón «Cancelar cita» que inicia el flujo de
  cancelación.
- RF-13: CUANDO se envíe el correo de confirmación de una cita (Spec 008), EL
  SISTEMA incluirá un enlace directo a la cancelación de esa cita (enmienda
  coordinada de la Spec 008, registrada 2026-10-13).

## Requisitos no funcionales
- Protección de datos personales: la verificación no debe permitir descubrir
  citas ajenas ni enumerar identificadores; los mensajes de error no muestran
  nombre, correo, celular ni documento de la cita.
- Seguridad: sin cuentas ni sesiones (fuera de alcance); la defensa aprobada
  es la verificación de identificación (referencia + número de documento) más
  un comportamiento uniforme de la página ante una referencia inexistente y
  ante datos incorrectos.
- Claridad: mensajes en español, comprensibles en escritorio y móvil; los
  literales viven en `consultorio/content/` y se reflejan en
  `tests/expected_content.py` (cambiar un copy obliga a PR de spec primero).
- Coherencia visual: paleta Serenidad Natural, contraste AA
  (`docs/design-contrast.md`), párrafos justificados sin guiones
  (`docs/design-typography.md`).
- Separación lógica e interfaz (constitución #3): la interfaz delega en la
  capa de servicio; la transición de estado y la notificación no se duplican
  en plantillas ni en rutas.
- Estados de la operación coherentes con el backend: disponible, validando,
  procesando, éxito, conflicto y error (AGENTS.md «Frontend y UX»).
- Sin dependencias nuevas (constitución #1).

## Casos límite
- Referencia de cita inexistente.
- Referencia con formato no válido (no numérica).
- Datos de identificación que no coinciden con la cita.
- Cita ya cancelada (recarga, reenvío o segundo intento).
- Cita cuya fecha u hora ya pasaron.
- Cita que comienza en menos de 3 horas (restricción RF-4).
- Cancelación exactamente con 3 horas de antelación (borde: permitida).
- Doble clic o doble envío del botón de cancelación.
- Fallo o ausencia del webhook de notificación: la cancelación no se revierte
  ni se bloquea (contrato de la Spec 010).
- Intento de cancelar conociendo solo el número de referencia.
- Enlace de cancelación del correo usado sobre una cita ya cancelada.

## Fuera de alcance
- Login, cuentas, sesiones, roles, tokens por correo o recuperación de citas.
- Reprogramación o cambio de fecha/hora de la cita.
- Políticas de cancelación adicionales (plazos distintos a las 3 horas,
  penalizaciones).
- Notificación por WhatsApp (pendiente de la Spec 009).
- Panel interno de agenda y visualización de cancelaciones (Specs 011/012).
- Cancelación por parte del consultorio desde una interfaz interna.
- Tabla de auditoría de cancelaciones adicional a la trazabilidad existente
  (`appointments.status` + `automation_events`).

## Textos de interfaz (contractuales)
Viven en `consultorio/content/` y se espejan en `tests/expected_content.py`.

| Literal | Texto |
|---|---|
| Título de la página de cancelación | Cancelar cita |
| Aviso previo | Si cancelas tu cita, este horario quedará libre y no podrás recuperarlo desde aquí. |
| Botón de confirmación | Sí, cancelar mi cita |
| Botón de volver | No, volver |
| Título de éxito | Cita cancelada |
| Mensaje de éxito | Tu cita ha sido cancelada. El horario ya está disponible para otra persona. |
| Estado mostrado | Cancelada |
| Verificación fallida | No pudimos verificar tu cita. Revisa los datos e inténtalo de nuevo. |
| Cita ya cancelada | Esta cita ya fue cancelada. |
| Restricción de antelación | Solo puedes cancelar tu cita desde el sitio con al menos 3 horas de anticipación. Si necesitas cancelar con menos tiempo, contáctate con el consultorio. |
| Botón en la página de la cita | Cancelar cita |

El formato exacto de las rutas y del enlace del correo se fija en el
`plan.md` de esta spec.

## Criterios de finalización
Todos los RF con test en verde y sin regresiones en la suite previa; demo
manual completa (crear una cita en el formulario, abrirla desde el correo o
desde `/citas/confirmada/<id>`, cancelarla con verificación de documento,
verificar la pantalla de resumen, la confirmación «Cancelada», la hora libre
en `/citas/horarios`, la re-reserva y el correo de notificación; probar
reintentos, referencia inexistente, documento incorrecto y la restricción de
3 horas); evidencia QA con PASS/FAIL por TC (y capturas si el criterio lo
requiere) y aceptación de la usuaria.

## Dudas resueltas
- [RESUELTA — Q1] Mecanismo de identificación del paciente → **número de
  referencia (`#id`) + número de documento** (decisión de la usuaria
  2026-10-13).
- [RESUELTA — Q2] Restricción temporal de la cancelación → **mínimo 3 horas
  de antelación** (borde exacto: permitido; menos de 3 horas, iniciada o
  pasada: rechazada con mensaje).
- [RESUELTA — Q3] Pantalla de confirmación previa → **sí, con resumen de la
  cita** (servicio, fecha, hora y estado) antes de cancelar.
- [RESUELTA — Q4] Destino tras cancelar → **pantalla de éxito propia** con
  estado «Cancelada» y datos de la cita.
- [RESUELTA — Q5] Botón en `/citas/confirmada/<id>` → **sí**, se añade
  «Cancelar cita» que inicia el flujo de verificación.
- [RESUELTA — Q6] Página de la cita cancelada → **muestra el estado
  «Cancelada»** (no 404).
- [RESUELTA — Q7] Enlace de cancelación en el correo → **sí**, enlace directo
  en el correo de confirmación; **enmienda coordinada de la Spec 008**
  registrada el 2026-10-13.
