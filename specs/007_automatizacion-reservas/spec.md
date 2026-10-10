# Spec 007 — Automatización de reservas mediante n8n

## Contexto y objetivo
Después de confirmar una reserva existen tareas administrativas que pueden requerir seguimiento y coordinación manual. Esta funcionalidad busca automatizar procesos posteriores a una reserva confirmada para reducir trabajo repetitivo y mejorar la continuidad del seguimiento, sin convertir la automatización en una condición necesaria para que la reserva sea válida.

## Usuarios / actores
- Administrador del consultorio.
- Sistema de reservas.
- Servicios de automatización posteriores a la reserva.

## Historias de usuario
- H1: Como administrador del consultorio quiero automatizar mediante n8n los procesos posteriores a una reserva confirmada para reducir tareas manuales y mejorar el seguimiento administrativo de las citas.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO una reserva sea confirmada, EL SISTEMA generará un evento estructurado para iniciar las automatizaciones posteriores definidas.
- RF-2: SI el servicio de automatización no está disponible temporalmente, ENTONCES EL SISTEMA mantendrá válida la reserva.
- RF-3: CUANDO se genere un evento de reserva, EL SISTEMA enviará únicamente los datos necesarios para la automatización y permitirá identificar la versión del evento.
- RF-4: SI ocurre un error, timeout o respuesta no válida durante la automatización, ENTONCES EL SISTEMA registrará la incidencia sin invalidar la reserva.
- RF-5: SI una misma reserva vuelve a procesarse, ENTONCES EL SISTEMA evitará generar automatizaciones duplicadas.
- RF-6: CUANDO exista un evento válido, EL SISTEMA permitirá ejecutar las automatizaciones administrativas configuradas.
- RF-7: EL SISTEMA mantendrá las funcionalidades de agendamiento, disponibilidad y protección contra doble reserva operativas independientemente de la automatización.

## Requisitos no funcionales
- Seguridad y minimización de datos compartidos.
- Tolerancia a indisponibilidad temporal del servicio de automatización.
- Trazabilidad de errores y eventos.
- Consistencia ante reintentos y duplicados.

## Casos límite
- Servicio de automatización no disponible.
- Timeout.
- Respuesta no válida.
- Reintento del mismo evento.
- Evento duplicado.
- Datos incompletos o no permitidos en el evento.

## Fuera de alcance
- Automatizaciones que cancelen o modifiquen una reserva sin una regla de negocio aprobada.
- Convertir la automatización en requisito para confirmar una cita.
- Notificaciones específicas de correo o WhatsApp que pertenezcan a otras historias.

## Criterios de finalización
Todos los RF con test en verde, incluyendo indisponibilidad, errores, reintentos y duplicados, más demo manual de una automatización posterior a una reserva confirmada.

## Dudas abiertas (CERRADAS por enmienda 2026-10-10)
- ~~[NECESITA ACLARACIÓN] Definir cuáles serán las automatizaciones administrativas incluidas en el primer incremento.~~ → **CERRADA (Q1)**: webhook genérico `appointment.confirmed` hacia n8n; los flujos concretos se configuran en n8n (§Contratos fijados).
- ~~[NECESITA ACLARACIÓN] Confirmar qué datos son estrictamente necesarios para cada automatización.~~ → **CERRADA (Q2)**: payload mínimo **sin datos personales** (§Contratos fijados).

## Contratos fijados (enmienda 2026-10-10, aprobada por la usuaria)

Estos textos son contrato (AGENTS.md «Textos contractuales»); cambian junto con los
tests en el mismo PR.

### Interpretación de «reserva confirmada» (RF-1)
Alta exitosa de la cita: el INSERT se confirma y se responde con la página
`/citas/confirmada/<id>`. El estado de negocio de la cita sigue siendo `pending`;
la spec no introduce un nuevo estado.

### Evento (RF-1, RF-3)
- `event_type`: `appointment.confirmed` (único tipo del primer incremento, Q1).
- `event_version`: entero, inicia en **1**; cualquier cambio de forma del payload
  eleva la versión y el `event_id` asociado.
- `event_id` (RF-5): determinista,
  `appointment.confirmed:{appointment.id}:v{event_version}`.
- Payload en `application/json`, allowlist estricta — **sin datos personales**
  (Q2), sólo:

```json
{
  "event_id": "appointment.confirmed:34:v1",
  "event_type": "appointment.confirmed",
  "event_version": 1,
  "occurred_at": "2026-10-10 12:34:56",
  "appointment": {
    "id": 34,
    "service": "individual",
    "date": "2026-10-15",
    "time": "10:00",
    "status": "pending"
  }
}
```

Quedan excluidos `patient_name`, `email`, `phone`, `document_type`,
`document_number` y `created_at` de la cita (RNF minimización).

### Envío (RF-2, RF-4, RF-6)
- POST síncrono best-effort con la stdlib (`urllib.request`) **después** de que la
  reserva esté persistida, con timeout configurable (3 s por defecto), **1 intento**
  y **sin reintentos automáticos** (Q5): la re-ejecución la decide el
  administrador/n8n.
- URL por variable de entorno `AUTOMATION_WEBHOOK_URL`; vacía por defecto =
  automatización deshabilitada (evento registrado como `skipped`, nunca un error).
- **Cabecera de autenticación opcional** (enmienda 2, 2026-10-10): variable de
  entorno `AUTOMATION_WEBHOOK_AUTH_HEADER` con formato `Nombre: valor` (p. ej.
  `X-HU007-Token: <token>`); vacía por defecto = POST sin cabecera extra. El
  valor se envía tal cual. El token es un **secreto de entorno**: no se almacena
  en el repositorio, la documentación ni los tests (allí solo valores falsos).
- Éxito = HTTP 2xx. `URLError`, timeout, respuesta no-2xx o cualquier excepción se
  registran como incidencia y **en ningún caso invalidan la reserva**.

### Registro e idempotencia (RF-4, RF-5)
Tabla `automation_events` con `UNIQUE (event_id)` en el punto de persistencia:
- `status`: `pending` → `sent` | `skipped` | `failed` (identificadores en inglés).
- `detail` en español: `Automatización no configurada.` ·
  `Servicio de automatización no disponible.` ·
  `Tiempo de espera agotado (timeout).` ·
  `Respuesta no válida del servicio (HTTP {code}).` ·
  `Error inesperado durante la automatización.`
- El reproceso de una misma reserva choca en el `UNIQUE` y se descarta **antes** de
  reenviar: nunca dos automatizaciones duplicadas.

> Nota de trazabilidad: el backlog histórico v2.0 identificaba HU-007 como cancelación de cita; la actualización posterior del mismo documento redefine HU-007 como automatización mediante n8n. Esta especificación toma la definición más reciente como vigente.
>
> Nota de enmienda: el 2026-10-10 se cerraron las dos dudas [NECESITA ACLARACIÓN]
> y se fijaron los contratos anteriores con aprobación expresa de la usuaria; el
> diseño técnico correspondiente está en `specs/007_automatizacion-reservas/plan.md`.
