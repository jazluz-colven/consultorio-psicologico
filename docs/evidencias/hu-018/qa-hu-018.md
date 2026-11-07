# Informe QA — HU-018 / Spec 018: Cancelar y reprogramar citas por el consultorio

**Fecha:** 2026-11-06
**Rama:** `feature/hu-018`
**Commits de referencia:** `c1d53b5` (T1), `b099104` (T2), `e08c8fe` (T3),
`f3314d6` (T4), `832149e` (T5)
**Especificación:** `specs/018_cancelar-reprogramar-citas/spec.md` (enmendada y
aprobada el 2026-11-05)
**Plan y tareas:** `plan.md` y `task.md` aprobados por la usuaria el 2026-11-05
**Entorno:** Windows, Python 3.14.8, Flask 3.1.3, SQLite
**Demo local:** app en `http://127.0.0.1:5000` con base de datos temporal fuera
del repositorio y receptor webhook HTTP stdlib en `127.0.0.1:8765`
**Privacidad:** este informe no contiene token, credenciales ni datos personales
reales; la demo usó datos ficticios.

---

## Veredicto

- **Pruebas automatizadas:** `python -m pytest -q` → **320 passed / 0 failed**.
- **Demo local:** **33/34** comprobaciones superadas.
- **Única comprobación no superada:** E2E real **n8n + Google Calendar**
  (Spec 007 RF-8), marcada como **NO VERIFICADO**; no se declara PASS.
- **Aceptación funcional:** **PENDIENTE** (checkbox sin marcar; solo la usuaria
  puede marcarlo).

**Estado del cierre:** HU-018 cerrada técnicamente el 2026-11-06 por decisión de
la usuaria, con la E2E de n8n/Calendar diferida y documentada en este informe.
La pantalla admin fue revisada visualmente en local y quedó OK; esa revisión
visual no sustituye la aceptación funcional.

---

## Matriz PASS/FAIL por TC

| TC | Evidencia | Resultado |
|---|---|---|
| TC-018-001 | `tests/test_admin_routes.py::test_tc_018_001_token_ausente_incorrecto_none_no_ascii_y_config_vacia`; demo `token_invalido_403_literal_sin_datos`, `token_invalido_post_403_sin_cancelar` | **PASS** |
| TC-018-002 | `tests/test_admin_routes.py::test_tc_018_002_get_detalle_con_token_resumen_formularios_y_cancelada`; demo `admin_detalle_A_200_resumen_y_formularios`, `detalle_A_cancelada_sin_formularios` | **PASS** |
| TC-018-003 | `tests/test_admin_routes.py::test_tc_018_003_cita_inexistente_404` | **PASS** |
| TC-018-004 | `tests/test_admin_routes.py::test_tc_018_004_post_cancelar_con_cabecera_y_con_campo_oculto`; demo `cancelar_A_200_literal`, `cancelar_A_estado_cancelled_en_bd` | **PASS** |
| TC-018-005 | `tests/test_hu_018.py::test_tc_018_005_cancelar_emite_evento_cancellation_email_una_vez`; demo `cancelar_A_bd_eventos_una_vez`, `cancelar_A_receptor_eventos_una_vez` | **PASS** |
| TC-018-006 | `tests/test_admin_routes.py::test_tc_018_006_cancelar_inexistente_ya_cancelada_y_reprogramar_cancelada` | **PASS** |
| TC-018-007 | `tests/test_hu_018.py::test_tc_018_007_reprogramar_a_horario_libre_emite_cuatro_eventos`; demo `reprogramar_B_bd_cuatro_eventos_una_vez`, `reprogramar_B_confirmacion_con_enlace_cancelacion` | **PASS** |
| TC-018-008 | `tests/test_admin_routes.py::test_tc_018_008_reprogramacion_exitosa_copia_paciente_y_usa_id_real`; demo `reprogramar_B_200_id_real` | **PASS** |
| TC-018-009 | `tests/test_hu_018.py::test_tc_018_009_reprogramar_a_horario_ocupado_no_cancela`; demo `horario_ocupado_mensaje_y_vieja_intacta` | **PASS** |
| TC-018-010 | `tests/test_hu_018.py::test_tc_018_010_reprogramar_con_fecha_pasada_o_fin_de_semana_no_cancela`; demo `fecha_invalida_no_cancela_vieja` | **PASS** |
| TC-018-011 | `tests/test_hu_018.py::test_tc_018_011_cancelar_hoy_y_pasada_y_reprogramar_a_hoy`; demo `rf9_cancelar_hoy`, `rf9_reprogramar_a_hoy` | **PASS** |
| TC-018-012 | `tests/test_admin_routes.py::test_tc_018_012_dos_post_cancelar_y_reprogramar_no_duplican`; demo `doble_envio_y_refresh_sin_duplicados` | **PASS** |
| TC-018-013 | `tests/test_admin_routes.py::test_tc_018_013_guard_rf_7_en_html_y_admin_js` | **PASS** |
| TC-018-014 | `tests/test_admin_content.py::test_tc_018_014_literales_admin_coinciden_con_expected_content_y_tabla_spec` | **PASS** |
| TC-018-015 | `tests/test_admin_content.py::test_tc_018_015_sin_dependencias_nuevas` | **PASS** |
| TC-018-016 | `python -m pytest -q` → **320 passed / 0 failed** | **PASS** |
| TC-018-017 | `tests/test_hu_018.py::test_tc_018_017_carrera_tras_cancelar_create_booking_slot_taken` | **PASS** |
| TC-018-018 | `tests/test_hu_018.py::test_tc_018_018_orden_cancelar_antes_de_crear` | **PASS** |
| TC-018-019 | `tests/test_admin_routes.py::test_tc_018_019_segundo_post_identico_no_duplica_cita_ni_eventos`; demo `doble_envio_y_refresh_sin_duplicados` | **PASS** |

---

## Demo local §6.2 (2026-11-06)

Comprobaciones ejecutadas contra la app local y el receptor webhook:

| Comprobación | Resultado |
|---|---|
| Reserva A → 303 y confirmación 200 | PASS |
| Detalle admin A → 200 con resumen y ambos formularios | PASS |
| Cabeceras `no-store` / `no-referrer` en respuestas admin | PASS |
| Cancelación A → 200 con «Cita cancelada.» y estado `cancelled` | PASS |
| Eventos de cancelación en BD y receptor, una vez por tipo | PASS |
| Detalle A cancelada → «Cancelada» y sin formularios operativos | PASS |
| **Calendar/n8n real (Spec 007 RF-8)** | **NO VERIFICADO** |
| Reserva B → 303 y confirmación 200 | PASS |
| Reprogramación B → 200 con id real, vieja `cancelled` y nueva `confirmed` | PASS |
| Cuatro eventos de reprogramación, una vez por tipo | PASS |
| Confirmación de la nueva cita con enlace `cancellation.verify` | PASS |
| Token inválido en GET y POST → 403, literal y sin datos | PASS |
| Horario ocupado → mensaje y cita vieja intacta | PASS |
| Fecha inválida → errores y cita vieja intacta | PASS |
| Doble envío / refresh → sin citas ni eventos duplicados | PASS |
| RF-9: cancelar una cita de hoy | PASS |
| RF-9: reprogramar a hoy | PASS |

Recuento de eventos observados en el receptor local: 9 `appointment.confirmed`,
9 `appointment.confirmation_email`, 5 `appointment.cancelled` y 5
`appointment.cancellation_email`. Todos los recuentos se filtraron por
`event_type`.

---

## Pendiente de E2E en canal real: n8n + Google Calendar

**Estado: NO VERIFICADO.** No se declara PASS.

Motivo: en esta sesión no estaban disponibles la URL de producción del webhook
ni la cabecera de autenticación del workflow, y el workflow v5 aún no estaba
importado/configurado en Render. El payload `appointment.cancelled` sí salió
correctamente al receptor local (verificado en las comprobaciones anteriores).

Para completar esta verificación se requiere:

1. Importar el JSON v5
   `docs/workflows/hu-007/n8n-hu-007-integracion-citas-2026-11-02-v5.json`.
2. Configurar la credencial de Google Calendar y revisar el calendario de los
   nodos de Calendar.
3. Configurar la credencial Header Auth del nodo `Webhook` (ruta
   `hu-007-cita-creada`, POST).
4. Crear/seleccionar las tablas de los nodos Data Table.
5. Activar el workflow y usar la URL de producción (no `webhook-test`).
6. Configurar en la app `AUTOMATION_WEBHOOK_URL`, la cabecera de autenticación
   y un timeout de 10–15 s para evitar fallos por arranque en frío de Render.
7. Verificar: evento creado al reservar y eliminado al cancelar, ejecuciones de
   n8n correctas y eventos `sent` en `automation_events`.

Este pendiente no afecta a los 320 tests ni a la demo local, pero **sí** al
criterio de la Spec 007 RF-8 y a la aceptación funcional completa de HU-018.

---

## Regresión y contraste

```text
python -m pytest -q
320 passed / 0 failed

python -m pytest -q tests/test_contraste.py
5 passed
```

---

## Revisión visual

- La pantalla admin se revisó en local el 2026-11-06 y quedó OK.
- Según D8 no se generan capturas 1280/375; la paleta y el contraste se
  verificaron con `tests/test_contraste.py`.
- La revisión visual no sustituye la aceptación funcional de la usuaria.

---

## Aceptación funcional

- [ ] Aceptación funcional de la usuaria (pendiente)

---

## Riesgos y limitaciones conocidas

- E2E de Calendar/n8n pendiente (arriba).
- El token de administración es compartido: no identifica al usuario ni deja
  auditoría por persona. Se abordará en la próxima spec de acceso.
- `?token=` puede quedar en historial o logs de acceso; se mitigó con GET-only
  y cabeceras `no-store`/`no-referrer`, sin prometer eliminación del log del
  servidor.
- El literal opcional de error de persistencia no se implementó (no forma parte
  de la cifra 320).
