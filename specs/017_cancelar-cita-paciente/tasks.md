# Tareas — Spec 017: Cancelar una cita por parte del paciente

Estado: aprobado por la usuaria (2026-10-25, junto con `plan.md`).

> Trazabilidad: **HU-017 → Spec 017 (`spec.md`, aprobada 2026-10-13, RF-1..RF-13) →
> `plan.md` → estas tareas → código → tests → evidencia → commit.**
> Rama: **`feature/hu-017`** (HEAD `223a43c`). Comandos: `python -m pytest -q`,
> `python app.py`.
> **10 tareas** (máximo permitido): ordenadas por dependencias (contenido → servicio →
> plantillas → rutas → RF-11/12 → RF-13 → regresión → evidencia), de 20–30 min cada una,
> todas **sin marcar**. El alcance cabe en una sola entrega; no se propone división.
> Restricciones transversales: no se modifica `spec.md` ni otras specs; no se tocan los
> cambios sin commitear de la **Spec 010 fase 2A (T22)** en el working tree (ver plan §8).

- [x] **T1. Crear `consultorio/content/cancellation_content.py` con los 11 literales contractuales de la tabla de la spec más las etiquetas funcionales y `EMAIL_CANCEL_LINK_LABEL`, y añadir su espejo en `tests/expected_content.py` con test nuevo.** RF-2, RF-3, RF-4, RF-7, RF-9, RF-12, RF-13
  - Hecho cuando: `python -m pytest -q tests/test_cancellation_content.py` queda en verde; los 11 literales coinciden carácter a carácter con la tabla de la spec; «Cancelada» se reutiliza desde `appointment_content.STATUS_CANCELLED_LABEL` (sin duplicar texto) y el espejo en `expected_content.py` cubre también las etiquetas nuevas.

- [x] **T2. Implementar con TDD la verificación de propiedad y la ventana de 3 horas en `consultorio/services/cancellation_flow_service.py` (`verify_cancellation_request`, con parámetro `now` explícito).** RF-1, RF-2, RF-4
  - Hecho cuando: los tests unitarios de `tests/test_cancellation_flow_service.py` pasan con `now` fijo y cubren: borde exacto de 3 horas → permitido; 2 h 59 min, hora iniciada y hora pasada → `TOO_SOON`; referencia inexistente y documento incorrecto → un único resultado `FAILED` sin datos de la cita en la salida.

- [x] **T3. Implementar con TDD la ejecución `cancel_verified_request()` delegando en `cancel_appointment()` de la Spec 010, con mapeo de resultados SUCCESS / ALREADY_CANCELLED / FAILED / TOO_SOON.** RF-5, RF-8, RF-9
  - Hecho cuando: `cancellation_flow_service.py` no contiene UPDATE, transiciones ni envíos propios (solo importa y llama a `cancel_appointment()`), y los tests prueban que un segundo intento devuelve `ALREADY_CANCELLED` con exactamente 1 fila `appointment.cancellation_email` y 0 POST adicionales al webhook.

- [x] **T4. Crear las plantillas `templates/cancellation/{verify,summary,success}.html` con identidad Serenidad Natural, contraste AA y párrafos justificados, más el guard de doble envío RF-10 en `static/js/cancellation.js` y sus estilos mínimos en `static/css/main.css`.** RF-3, RF-7, RF-10
  - Hecho cuando: el HTML contiene los literales contractuales y las etiquetas del contenido; la pantalla de verificación muestra el aviso previo, la referencia y el campo de documento; el resumen incluye servicio, fecha legible, hora, estado y los botones «Sí, cancelar mi cita» y «No, volver»; el éxito muestra «Cita cancelada», el mensaje, «Cancelada» y la referencia; el script aplica el patrón HU-006 (flag de envío + `preventDefault` + botón `disabled`/`aria-busy`) verificado por test; no se introducen colores fuera de la paleta y `python -m pytest -q tests/test_contraste.py` sigue en verde.

- [x] **T5. Crear el blueprint `consultorio/web/cancellation.py` con `GET/POST /citas/cancelar/<int:cita_id>` (formulario de verificación y pantalla de resumen) y registrarlo en `create_app()`.** RF-1, RF-2, RF-3, RF-4
  - Hecho cuando: los tests de rutas de `tests/test_hu_017.py` de este tramo pasan: GET devuelve 200 con el mismo formulario exista o no la cita (404 solo con id no numérico); POST fallido muestra «No pudimos verificar tu cita. Revisa los datos e inténtalo de nuevo.» sin datos de la cita y con 0 cambios en BD; POST correcto renderiza el resumen con servicio, fecha legible, hora y estado; cita a menos de 3 horas → literal de restricción sin cambios.

- [x] **T6. Crear `POST /citas/cancelar/<int:cita_id>/confirmar` (re-verificación de propiedad, re-chequeo de ventana y ejecución) y `GET …/exito` con redirección 303 (PRG), mapeando los mensajes de conflicto y error.** RF-1, RF-4, RF-5, RF-6, RF-7, RF-9
  - Hecho cuando: el flujo completo verificación → resumen → confirmación → éxito pasa con 303 a `/citas/cancelar/<id>/exito`, la cita queda `cancelled`, el literal «Cita cancelada» y el estado «Cancelada» aparecen en la pantalla de éxito con datos y referencia, el hueco queda libre en `/citas/horarios` y la re-reserva devuelve 303; un reenvío del POST muestra «Esta cita ya fue cancelada.» sin segundo evento de notificación.

- [ ] **T7. Actualizar `/citas/confirmada/<id>` (`web/appointments.py` + `templates/appointments/confirmation.html`) para mostrar el estado real y el botón «Cancelar cita» solo en citas confirmadas.** RF-11, RF-12
  - Hecho cuando: los tests TC-017-008 pasan: cita confirmada → etiqueta «Confirmada» y botón «Cancelar cita» que enlaza a `/citas/cancelar/<id>`; cita cancelada → etiqueta «Cancelada» y sin botón; id desconocido → 404.

- [ ] **T8. Añadir el enlace directo de cancelación al correo de confirmación (parámetro opcional `cancellation_url` al final de `create_booking()`, `send_confirmation()` y `build_confirmation_message()`, URL absoluta con `url_for(_external=True)` en la capa web).** RF-13
  - Hecho cuando: el payload `appointment.confirmation_email` de una reserva hecha por `POST /citas` contiene en texto y HTML el enlace absoluto `…/citas/cancelar/<id>` con la etiqueta «Cancelar cita»; `EMAIL_FOOTER` y los demás literales de la Spec 008 intactos; `python -m pytest -q tests/test_hu_008.py` pasa **sin haber modificado ese fichero de tests**. **Condición previa (plan §8.1): los cambios de la Spec 010/T22 están commiteados; si siguen sin commitear, posponer esta tarea y avisar al coordinador** (única tarea que edita `appointment_service.py`).

- [ ] **T9. Completar la batería de integración y regresión (`tests/test_hu_017.py`) y ejecutar la suite completa.** RF-1..RF-13
  - Hecho cuando: `python -m pytest -q` devuelve **0 FAIL** con la suite previa intacta (cifra baseline registrada al iniciar), los TC-017-001..013 de la matriz del plan §6 quedan en verde y la trazabilidad RF ↔ TC del plan §7 queda completa.

- [ ] **T10. Evidencia QA: demo manual de los criterios de finalización de la spec, informe `docs/evidencias/hu-017/qa-hu-017.md` y servidor de revisión en marcha.** RF-1..RF-13 (criterios de finalización)
  - Hecho cuando: el informe publica PASS/FAIL por TC-017-001..013 con checkbox de aceptación, incluye la demo completa de la spec (reserva → apertura desde el correo → verificación con documento → resumen → «Cancelada» → hueco libre → re-reserva → correo de notificación; reintentos, referencia inexistente, documento incorrecto y restricción de 3 h), revisa consola/red y adjunta capturas CDP de 1280 y 375 sin desbordamientos; `python app.py` queda ejecutándose y la URL de revisión queda comunicada.
