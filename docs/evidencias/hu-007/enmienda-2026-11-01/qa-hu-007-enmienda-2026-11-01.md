# QA — Spec 007, enmienda 2026-11-01 (RF-8..RF-13)

**Fecha de ejecución:** 2026-11-04
**Alcance:** borrado del evento de Google Calendar al recibir `appointment.cancelled`
(RF-8..RF-13) y registro separado del estado de cancelación.
**Ejecutor:** coordinación SDD con la usuaria (n8n Cloud + app Flask local).
**Resultado global:** **PASS funcional (5/5 escenarios)**. La revisión técnica
emitió `CAMBIOS NECESARIOS` por motivos documentales, cerrados en este informe,
`ejecuciones.md`, `D-007-01` y el commit de cierre.

---

## 1. Artefactos y versiones

| Elemento | Valor |
|---|---|
| Workflow vigente | `docs/workflows/hu-007/n8n-hu-007-integracion-citas-2026-11-02-v5.json` |
| Nodos | 48 |
| sha256 | `8918306709c0e13132861cea04cc2d7ff98dded6d7f005c94e4f5e02f3dfb766` |
| Workflow n8n Cloud | `HU-007 - Integración de citas con n8n`, activo |
| Webhook | `POST /webhook/hu-007-cita-creada` (Header Auth) |
| Data table | `HU007EventosProcesados` (14 columnas) |
| Backend | sin cambios (`python -m pytest -q` → **302 passed**) |
| Spec | `specs/007_automatizacion-reservas/spec.md` — enmienda 2026-10-23, RF-8..RF-13 |
| Plan | `specs/007_automatizacion-reservas/plan.md` §9 (correcciones 1–4) |
| Tareas | `specs/007_automatizacion-reservas/task.md` T16–T22 |
| Defecto | `docs/defectos/D-007-01.md` |

**Versionado:** las cinco versiones están en `docs/workflows/hu-007/` (v1 y v2
recuperadas de la papelera el 2026-11-04; su contenido es coherente con el
historial: v1→v5 solo añade los 4 nodos finales y cambia el `jsCode` del
clasificador).

| Versión | Nodos | sha256 |
|---|---|---|
| v1 `...-2026-11-01.json` | 44 | `E69483C96EFFC22AEE48FC2575B615338CD3961762F9D3E8391320A135598E77` |
| v2 `...-2026-11-02.json` | 44 | `EB5429CF918AD764E188054522627E1D16A1EAA82E4D619AA7030A2F4EB33C9B` |
| v3 `...-2026-11-02-v3.json` | 44 | `5E7BE441E420C5A58193E17F5373BCEBC026EEF4E98E915F55B497F446088D52` |
| v4 `...-2026-11-02-v4.json` | 47 | `E80D4EBECA7B7275671FC5AF45022CFFD31ED438630FD9F45719E02FACEE05AB` |
| v5 `...-2026-11-02-v5.json` | 48 | `8918306709C0E13132861CEA04CC2D7FF98DDED6D7F005C94E4F5E02F3DFB766` |

---

## 2. Escenarios ejecutados

Ver `ejecuciones.md` para hora, duración y evento de cada ejecución.

| ID | Escenario | Preparación | Esperado | Observado | Estado |
|---|---|---|---|---|---|
| A | Borrado real con éxito | Cita 33 con evento en Calendar; cancelar sin borrarlo | C `completed` / detalle vacío / id vacío; X `completed` | Igual | **PASS** |
| B | Evento ya borrado | Cita 32; evento borrado a mano; cancelar | C `completed` / `not_found` / id vacío; X `completed` | Igual | **PASS** |
| C | Reintento con cancelación completada | Fila X de la 33 forzada a `failed`; reenviar `appointment.cancelled:33:v1` | X vuelve a `completed`; **sin** llamada a Calendar (detalle de C sin cambios) | Igual | **PASS** |
| D | Sin fila de creación | Enviar `appointment.cancelled:999:v1` (cita inexistente) | X `completed` / `skipped` / `no_creation_record` | Igual | **PASS** |
| E | Creación sin `calendar_event_id` | Cita 34; vaciar el id en la fila C; cancelar | C `skipped` / `missing_calendar_event_id`; X `completed` | Igual | **PASS** |
| R | Regresión funcional | `python -m pytest -q` | 302 passed | 302 passed | **PASS** |

Filas exactas en los exports de evidencia:

- `datatable-e2e-A-B-v5-2026-11-04.csv` (8 filas):
  - `appointment.confirmed:32:v1` → `completed`, `completed`, `not_found`, ``.
  - `appointment.confirmed:33:v1` → `completed`, `completed`, ``, ``.
- `datatable-e2e-D-E-v5-2026-11-04.csv` (13 filas):
  - `appointment.cancelled:999:v1` → `completed`, `skipped`, `no_creation_record`.
  - `appointment.confirmed:34:v1` → `completed`, `skipped`, `missing_calendar_event_id`, ``.

---

## 3. Criterios de aceptación

- [x] **CA-8 (RF-8):** al cancelar se intenta borrar el evento de la cita.
- [x] **CA-9 (RF-9):** la fila de creación se localiza por `appointment_id` +
      `event_type='appointment.confirmed'`, nunca por el evento de cancelación.
- [x] **CA-10 (RF-10):** 404/410 se tratan como completado; verificado con el
      evento ya cancelado (`status: "cancelled"`) y con la limpieza del
      `calendar_event_id` (escenario B).
- [x] **CA-11 (RF-11):** sin fila de creación o sin `calendar_event_id` se
      registra `skipped` con motivo, nunca `failed` (escenarios D y E).
- [x] **CA-12 (RF-12):** el estado de cancelación vive en
      `cancellation_status` / `cancellation_detail`, sin sobrescribir
      `processing_status` de la creación ni `email_processing_status`.
- [x] **CA-13 (RF-13):** el borrado solo se dispara con `appointment.cancelled`;
      `appointment.cancellation_email` termina sin tocar Calendar (series
      `...:33` y `...:34`).
- [ ] **Aceptación funcional de la usuaria:** pendiente.

---

## 4. Defecto D-007-01 — ciclos de corrección

| Ciclo | Corrección | Resultado | Causa del descarte |
|---|---|---|---|
| 1 (v1) | Nodo Calendar + clasificador simple | `http_error_unknown` | El nodo oculta el código HTTP |
| 2 (v2) | HTTP Request con credencial predefinida | `http_error_unknown` | n8n Cloud prohíbe OAuth2 de Google en nodos HTTP |
| 3 (v3) | Clasificador endurecido (campos + texto) | `calendar_http_code: null` | El mensaje es genérico y no contiene 4xx/5xx |
| 4 (v4) | Verificar existencia con `events.get` | `failed` | `events.get` devuelve el evento con `status: "cancelled"` |
| 5 (v5) | `¿Evento cancelado?` sobre `status` | **PASS** | — |

Estado del defecto: `CORREGIDO — PENDIENTE DE VALIDACIÓN`.

---

## 5. Hallazgos de la revisión técnica y su cierre

| # | Hallazgo | Cierre |
|---|---|---|
| 1 | Faltaban informe QA y `ejecuciones.md` | Creados (este documento y `ejecuciones.md`) |
| 2 | RF-10 no verificable sin IDs/ejecuciones | Registro por marca de tiempo y duración cruzado con `automation_events`; escenarios B y C documentados |
| 3 | `calendar_http_code` no asignado en los nodos `Set` | **Desviación aceptada:** el campo no se consume aguas abajo (`¿Borrado o ya eliminado?` lee `calendar_ok`). Documentado aquí y en `D-007-01` §8 |
| 4 | No están los JSON v1–v4 | **Resuelto**: recuperados v1 y v2 de la papelera el 2026-11-04; las cinco versiones están versionadas con sha256 en §1 |
| 5 | Plan/tareas sin aprobar y sin commit | Aprobaciones registradas en `plan.md` §9.11; tareas marcadas en `task.md`; commit de cierre |
| 6 | `D-007-01` §8/§10/CA-D007-03 obsoletos | Alineados con el v5 conservando el historial |
| 7 | CSV pre-reset con columnas desplazadas | `datatable-antes-reset.csv` **no** se usa como evidencia: export servido desde caché del navegador (fila con `event_type=none` y `cancellation_status=" cancellation_status"`). Las evidencias válidas son los dos CSV del v5 |
| 8 | `MEMORY.md` sin la enmienda | Actualizado en el cierre |

---

## 6. Riesgos y limitaciones

- **R5 (materializado y corregido):** el clasificador por texto no bastaba.
- **R6 (vigente, aceptado):** si `Verificar evento` falla por red o credencial, se
  registra `not_found`. El borrado exitoso no pasa por la verificación, y la
  misma credencial ya se usa para crear los eventos del flujo.
- Un evento cancelado permanece recuperable por API hasta su purga; el flujo lo
  trata como «ya no existe», conforme a RF-10.
- La data table se vació el 2026-11-02 con decisión explícita de la usuaria;
  respaldo en `datatable-antes-reset.csv` (export inválido, ver §5.7) y en el
  contenido descrito en `D-007-01`.
- Residuos de prueba: la cita 34 conservó su evento en Google Calendar (se le
  vació el `calendar_event_id` a propósito) y debe borrarse a mano.

---

## 7. Evidencia

```text
docs/evidencias/hu-007/enmienda-2026-11-01/
├── precheck.md                              (T16: auditoría estructural)
├── ejecuciones.md                           (registro de ejecuciones)
├── qa-hu-007-enmienda-2026-11-01.md         (este informe)
├── datatable-e2e-B-fallido.csv              (estado fallido inicial)
├── datatable-antes-reset.csv                (export inválido, §5.7)
├── datatable-e2e-A-B-v5-2026-11-04.csv      (escenarios A y B)
└── datatable-e2e-D-E-v5-2026-11-04.csv      (escenarios D y E)
```
