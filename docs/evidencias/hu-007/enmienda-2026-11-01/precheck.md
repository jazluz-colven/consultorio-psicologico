# T16 — Pre-check del workflow base (enmienda 2026-11-01, RF-8..RF-13)

- **Tarea**: T16 de `specs/007_automatizacion-reservas/task.md`
- **Fecha**: 2026-11-01
- **Rol**: coordinador
- **Resultado**: **PASS estructural** (con un punto pendiente de confirmación en la UI, ver final)

## 1. Archivo base recibido

| Dato | Valor |
|---|---|
| Ruta | `C:\Users\Jaz\Downloads\HU-007 - Integración de citas con n8n.json` |
| Bytes | 122 993 |
| SHA-256 | `885ff822381a18b4ca95e423ffa695a055b86171de1ce2425f5d048a59ef3f21` |
| Fecha del archivo | 2026-10-30 01:08 |

## 2. Metadatos del workflow

| Dato | Valor |
|---|---|
| Nombre | `HU-007 - Integración de citas con n8n` |
| Workflow id | `v0WykUcKCzccxfyI` |
| versionId | `279f3ea1-f444-410a-afc8-24f492ca18dc` |
| `active` en el export | `false` (artefacto de serialización; no prueba inactividad) |
| `pinData` | vacío |
| `settings` | `executionOrder: v1`, `binaryMode: separate` |
| `tags` / `nodeGroups` | `[]` / `0` |
| `webhookId` | `8889e9dd-ca30-4548-9505-95336cc04b51` |
| Webhook | `POST hu-007-cita-creada`, `headerAuth`, `responseMode: responseNode` |
| Data table | `HU007EventosProcesados` (`t4GENwUkjVodM5cg`) |

## 3. Comprobaciones estructurales

| Comprobación | Resultado |
|---|---|
| Nodos | **42**, nombres únicos (42/42) |
| Conexiones rotas (origen o destino inexistente) | **0** |
| Nodos con data table `t4GENwUkjVodM5cg` | 21 |
| Nodo `Create a data table` | sin `dataTableId` (huérfano, **no se toca**) |
| Nodos objetivo de eliminación (T18) | **7/7 presentes** |
| Nodos nuevos del plan §9.5.1 | **0/9 presentes** (correcto: los crea T18) |

## 4. Credenciales (solo referencias, sin secretos)

| Credencial | id | Nodos |
|---|---|---|
| `Header Auth account` | `HI3XJ7eIcCOH0EKd` | 1 (Webhook) |
| `SMTP account` | `S3brsIm3k9YUh9K0` | 2 (envío de correo) |
| `Google Calendar account` | `Jzc9xfMvMH5AeRBN` | 4 (crear/borrar) |

## 5. Escaneo de secretos y PII

| Patrón | Coincidencias |
|---|---|
| `x-hu007-token` | 0 |
| `authorization` | 0 |
| `bearer <token>` | 0 |
| `api_key` / `apikey` | 0 |
| `password` / `passwd` | 0 |
| JWT (`eyJ…`) | 0 |
| Literal del token de sesión | 0 |
| Campos PII (`patient_name`, `email`, `phone`, `document_type`, `document_number`) | ninguno |

## 6. Propiedades críticas para el diseño §9.5

| Nodo | Propiedad | Valor | Relevancia |
|---|---|---|---|
| `Consulta` | `alwaysOutputData` | `true` | Sin esto, el caso D (sin fila de creación) moriría en silencio: el IF no recibiría ítems |
| `Elimina cita` | `onError` | `continueErrorOutput` | Necesario para clasificar 404/410 |
| `Elimina cita` | `retryOnFail` | ausente (≈ `false`) | Evita que n8n consuma el 404 antes de clasificarlo |
| `Update row(s)2` | `onError` | `continueErrorOutput` | Salida de error → `Update row(s)3` |
| `Get row(s)1` | `alwaysOutputData` | `true` | (Nodo a eliminar en T18) |

## 7. `typeVersion` disponibles en el export

`webhook 2.2` · `set 3.5` · `if 2.3 y 2.4` · `dataTable 1.1` · `switch 3.4` ·
`emailSend 2.1` · `respondToWebhook 1.5` · `googleCalendar 1.3`.

**No existe ningún nodo `Code` previo**: el clasificador de §9.5.5 introduce
`n8n-nodes-base.code` por primera vez. Verificar en T19 que la versión importa
sin avisos (riesgo R5 del plan).

## 8. Conclusión

El export es estructuralmente coherente, no contiene secretos ni PII y soporta
todas las precondiciones del plan §9.5 (en particular `Consulta.alwaysOutputData`).
Se usa como base de **T18**.

## 9. Confirmación en la UI (T16) — 2026-11-01

- [x] **Confirmado por la usuaria**: en la UI de n8n el workflow
      `HU-007 - Integración de citas con n8n` (`v0WykUcKCzccxfyI`) estaba
      **desactivado** por las modificaciones en curso, y el export del
      2026-10-30 01:08 (`versionId 279f3ea1…`) **era el vigente**, sin cambios
      posteriores.

**Consecuencia operativa**: `active:false` en el export refleja el estado real,
no solo un artefacto de serialización. La automatización **no ha estado
publicando eventos** desde esa desactivación; el backlog debe revisarse en el
entorno de producción antes de reactivar (ver nota en la respuesta del
coordinador). El export sigue siendo válido como base de T18.
