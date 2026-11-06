# Spec 018 — Cancelar y reprogramar citas por el consultorio

## Contexto y objetivo
La cancelación existe ya como capa de servicio sin interfaz (Spec 010) y la
cancelación por el paciente está cubierta por la Spec 017; la reprogramación
administrativa aún no existe. El consultorio necesita cancelar o reprogramar
citas por iniciativa propia (p. ej. cuando el paciente avisa por teléfono).
Esta funcionalidad ofrece una interfaz interna mínima que reutiliza la
cancelación y la liberación de horario de la Spec 010, las reglas de reserva y
disponibilidad de las Specs 004/005/006 y las notificaciones de las Specs
008/010, sin reescribirlas: reprogramar = cancelar la cita actual + reservar la
nueva.

## Usuarios / actores
- Psicóloga / consultorio (actor principal, con acceso protegido por token).
- Paciente: destinatario de las notificaciones; sin interfaz propia en esta
  spec (Spec 017).

## Historias de usuario
- H1: Como psicóloga quiero cancelar o reprogramar una cita desde el sitio
  para mantener la agenda al día cuando el paciente no podrá asistir.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO se acceda a cualquier funcionalidad de esta spec, EL SISTEMA
  exigirá el token de acceso definido en la variable de entorno
  `CONSULTORIO_ADMIN_TOKEN`; SIN él (o con uno incorrecto) no se mostrará
  información de la cita ni se procesará la funcionalidad, y la respuesta
  mostrará únicamente el mensaje de acceso denegado.
- RF-2: CUANDO el consultorio solicite gestionar una cita, EL SISTEMA
  mostrará primero un resumen de la cita (paciente, servicio, fecha, hora,
  estado) antes de permitir cancelar o reprogramar.
- RF-3: CUANDO el consultorio confirme la cancelación, EL SISTEMA pondrá la
  cita en estado Cancelada mediante el servicio de cancelación de la Spec
  010, liberará el horario y enviará la notificación de cancelación
  correspondiente.
- RF-4: CUANDO el consultorio confirme una reprogramación, EL SISTEMA
  cancelará la cita actual (RF-3) y registrará una nueva cita con los mismos
  datos del paciente y el nuevo servicio/fecha/hora, aplicando las mismas
  reglas de validación y disponibilidad de la reserva (Specs 004/005/006).
- RF-5: CUANDO una reprogramación quede registrada, EL SISTEMA informará del
  nuevo id de la cita; el paciente recibirá la notificación de cancelación
  de la anterior y la confirmación de la nueva.
- RF-6: SI el nuevo horario no está disponible (o los datos nuevos son
  inválidos), ENTONCES EL SISTEMA no registrará la cita nueva y mostrará el
  motivo; la cancelación previa (si se produjo) permanece — nunca se
  revierte una cancelación ya confirmada.
- RF-7: CUANDO el formulario interno esté en proceso de envío, EL SISTEMA
  evitará operaciones duplicadas por doble clic o doble envío.
- RF-8: SI la cita no existe, ya está cancelada o el token es inválido,
  ENTONCES EL SISTEMA mostrará un mensaje claro en español sin revelar datos
  de otras citas.
- RF-9: EL SISTEMA permitirá al consultorio cancelar o reprogramar citas del
  mismo día y pasadas, sin aplicar la restricción de 3 horas de la Spec 017.
  En una reprogramación, la fecha nueva seguirá las reglas de la Spec 004
  (lunes a viernes y no anterior a hoy).

## Requisitos no funcionales
- El token vive solo en la variable de entorno `CONSULTORIO_ADMIN_TOKEN`
  (mismo patrón de secreto que `AUTOMATION_WEBHOOK_AUTH_HEADER`): nunca en
  el repo, docs ni tests.
- Mensajes en español, literales en `consultorio/content/` espejados en
  `tests/expected_content.py`; paleta Serenidad Natural y contraste AA.
- Separación lógica e interfaz (constitución #3): la interfaz delega en
  `cancel_appointment()` y `create_booking()`; sin lógica duplicada.
- Estados de operación coherentes con el backend (disponible, validando,
  procesando, éxito, conflicto, error) y botón sin doble envío.
- Sin dependencias nuevas (constitución #1). Sin PII en logs.

## Casos límite
- Token ausente o incorrecto (todas las rutas internas).
- Referencia de cita inexistente o ya cancelada.
- Reprogramar a un horario ocupado por otra cita.
- Reprogramar a un horario inválido (fin de semana, hora fuera de agenda,
  fecha pasada).
- Fallo del webhook: cancelación y reserva intactas, eventos `failed`.
- Doble clic en cancelar o reprogramar.
- Reprogramar una cita y que la nueva reserva falle tras cancelar (RF-6).

## Fuera de alcance
- Login, cuentas, sesiones y roles múltiples (solo un token compartido).
- Agenda diaria/por fecha (Specs 011/012, siguen siendo solo lectura).
- Reprogramación o cancelación por el propio paciente (Spec 017).
- Registro del actor (`initiated_by`) en BD.
- Notificación por WhatsApp (Spec 009).
- Historial visual de citas anteriores/reprogramadas.

## Textos de interfaz (contractuales)
Viven en `consultorio/content/` y se espejan en `tests/expected_content.py`.

| Literal | Texto |
|---|---|
| Título | Gestión de citas |
| Título de cancelación | Cancelar cita |
| Aviso de cancelación | La cita quedará Cancelada, el horario se liberará y el paciente recibirá la notificación. |
| Botón de cancelación | Sí, cancelar cita |
| Título de reprogramación | Reprogramar cita |
| Aviso de reprogramación | Se cancelará la cita actual y se registrará una nueva. El paciente recibirá la cancelación y la nueva confirmación. |
| Botón de reprogramación | Sí, reprogramar |
| Botón de volver | Volver |
| Éxito de cancelación | Cita cancelada. |
| Éxito de reprogramación | Cita reprogramada. Nueva cita #{id}. |
| Acceso denegado | No tienes acceso a la gestión de citas. |
| Cita no encontrada | No encontramos esa cita. Revisa la referencia. |
| Cita ya cancelada | La cita ya estaba cancelada. |
| Horario no disponible | Ese horario ya está ocupado. Elige otro. |

El mecanismo de entrega exacto del token en cada request (cabecera o campo
del formulario) se fija en el `plan.md` de esta spec.

## Criterios de finalización
Todos los RF con test en verde y sin regresiones; demo manual completa
(cancelar una cita creada en `/citas`, reprogramar otra a un horario libre,
verificar correos de cancelación + confirmación, token inválido, horario
ocupado y doble envío); evidencia QA con PASS/FAIL por TC y aceptación de la
usuaria.

## Dudas resueltas
- [RESUELTA — Q1] Variable de entorno del token → **`CONSULTORIO_ADMIN_TOKEN`**
  (propuesta aprobada por la usuaria 2026-10-13); la entrega exacta
  (cabecera vs campo) se fija en el plan.

## Enmienda 2026-11-05

Enmienda mínima autorizada por la usuaria el 2026-11-05. Aplica cuatro cambios:

1. **Contexto y objetivo**: la reprogramación deja de atribuirse a la Spec 010;
   se reutilizan la cancelación y la liberación de horario de la Spec 010, las
   reglas de reserva y disponibilidad de las Specs 004/005/006 y las
   notificaciones de las Specs 008/010.
2. **Tabla de textos de interfaz**: se añade el literal «Cita ya cancelada» con
   el texto «La cita ya estaba cancelada.».
3. **RF-9**: se explicita que la fecha nueva de una reprogramación sigue las
   reglas de la Spec 004 (lunes a viernes y no anterior a hoy).
4. **RF-1**: se explicita que, sin token válido, no se muestra información de la
   cita ni se procesa la funcionalidad y la respuesta muestra únicamente el
   mensaje de acceso denegado.

Esta enmienda no altera el modelo A (cancelar primero y después registrar la
nueva, sin reversión) ni los requisitos RF-3, RF-4, RF-5 y RF-6. El literal «ya
cancelada» es el Q2 aprobado el 2026-10-13.
