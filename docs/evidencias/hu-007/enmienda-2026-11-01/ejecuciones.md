# Registro de ejecuciones — enmienda 2026-11-01 (Spec 007)

**Workflow:** `HU-007 - Integración de citas con n8n` (n8n Cloud,
`https://ingjazar.app.n8n.cloud`), path `hu-007-cita-creada`.
**Artefacto vigente:** `docs/workflows/hu-007/n8n-hu-007-integracion-citas-2026-11-02-v5.json`
(48 nodos, sha256 `8918306709c0e13132861cea04cc2d7ff98dded6d7f005c94e4f5e02f3dfb766`).

> **Nota sobre los ID de ejecución:** la vista *Executions* de n8n Cloud muestra
> hora, duración y estado, pero **no** el ID en la lista; el ID solo aparece en la
> cabecera del detalle (`ID #n`). El identificador único de cada ejecución en este
> registro es la **marca de tiempo**, que se ha cruzado con
> `automation_events.created_at` de `data/consultorio.db` (± 2 s de diferencia
> entre el envío del backend y la recepción en n8n).

## 1. Serie del 2026-11-02 (primer intento de E2E-B)

| Hora | Duración | Estado | Evento | Resultado |
|---|---|---|---|---|
| 19:24:45 | — | Success | `appointment.confirmed:31:v1` | Creación de la cita 31 y del evento |
| 19:32:16 | — | **Error** (ID #13) | `appointment.cancelled:31:v1` | `failed` / `http_error_unknown`; `calendar_event_id` sin limpiar. **Fallo origen D-007-01** |
| 22:14:46 | 1.896 s | Success (ID #39) | reenvío `appointment.cancelled:31:v1` (v2, HTTP Request) | Sin cambios en la tabla: la credencial está bloqueada en nodos HTTP |
| — | — | — | reenvío `appointment.cancelled:32:v1` (v3) | `calendar_http_code: null`; el nodo Calendar oculta el código |

## 2. Serie del 2026-11-04 (validación del v5)

Todas las ejecuciones terminaron en **Success**.

| Hora | Duración | Evento | Escenario | Resultado |
|---|---|---|---|---|
| 02:00:58 | 1.356 s | reenvío `appointment.cancelled:32:v1` | **E2E-B** (evento ya borrado → `status: cancelled`) | C `completed` / `not_found` / id vacío; X `completed` |
| 02:03:35 | 0.694 s | `appointment.confirmed:33:v1` | Creación cita 33 | C con `calendar_event_id`; X `completed` |
| 02:03:36 | 3.661 s | `appointment.confirmation_email:33:v1` | Correo de confirmación | X `completed` |
| 02:03:57 | 2.158 s | `appointment.cancelled:33:v1` | **E2E-A** (borrado real con éxito) | C `completed` / detalle vacío / id vacío |
| 02:03:57 | 1.338 s | `appointment.cancellation_email:33:v1` | Correo de cancelación | X `completed` |
| 02:09:05 | 0.319 s | reenvío `appointment.cancelled:33:v1` (X forzada a `failed`) | **E2E-C** (guard) | X vuelve a `completed`; detalle de C sin cambios → sin llamada a Calendar |
| 02:13:32 | 0.317 s | `appointment.cancelled:999:v1` | **E2E-D** (sin fila de creación) | X `completed` / `skipped` / `no_creation_record` |
| 02:14:02 | 0.781 s | `appointment.confirmed:34:v1` | Creación cita 34 | C con `calendar_event_id` |
| 02:14:03 | 2.600 s | `appointment.confirmation_email:34:v1` | Correo de confirmación | X `completed` |
| 02:19:29 | 0.390 s | `appointment.cancelled:34:v1` | **E2E-E** (creación sin `calendar_event_id`) | C `skipped` / `missing_calendar_event_id`; X `completed` |
| 02:19:30 | 2.206 s | `appointment.cancellation_email:34:v1` | Correo de cancelación | X `completed` |

Capturas de la lista de ejecuciones aportadas por la usuaria el 2026-11-04
(visibles en la sesión de trabajo; la lista no expone los ID).

## 3. Datos de origen

- `data/consultorio.db` → `appointments` (ids 32, 33, 34) y `automation_events`
  (ids 77–84) con sus `created_at`.
- Payloads de reenvío: `appointment.cancelled:<id>:v1` con el mismo contrato de
  10 campos que emite la Spec 010.
- Exports CSV de la data table usados como evidencia:
  `datatable-e2e-A-B-v5-2026-11-04.csv` y `datatable-e2e-D-E-v5-2026-11-04.csv`.
