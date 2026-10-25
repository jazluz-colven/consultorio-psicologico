# Plan Técnico — Spec 017: Cancelar una cita por parte del paciente

Estado: aprobado por la usuaria (2026-10-25; incluye las decisiones Q-A…Q-F de §10)

> Trazabilidad: **HU-017 → Spec 017 (`specs/017_cancelar-cita-paciente/spec.md`, versión
> aprobada 2026-10-13, RF-1..RF-13) → este plan → `tasks.md` → código → tests →
> evidencia → commit.**
> Constitución: `docs/constitution.md` (6 principios). Reglas permanentes: `AGENTS.md`.
> Rama de trabajo: **`feature/hu-017`** (HEAD `223a43c`).
> Baseline de la suite: **fijar con `python -m pytest -q` al iniciar la implementación**;
> no se fija aquí porque el working tree contiene cambios sin commitear de la **Spec 010
> fase 2A (T22)** (ver §8).
>
> **Sustituye por completo** al `plan.md` anterior, que fue generado contra una versión
> equivocada de la spec (numeración RF-1..RF-9 y mapeo de requisitos incorrecto). Este
> plan no modifica `spec.md` ni ninguna otra spec.

---

## 0. Alcance

Implementa la interfaz del paciente para cancelar su propia cita (H1 de la spec):

- Verificación de identificación (**referencia `#id` + número de documento**) antes de
  cualquier cambio (RF-1, RF-2).
- Pantalla de resumen previa antes de cancelar (RF-3).
- Restricción de **mínimo 3 horas de antelación**, con borde exacto permitido (RF-4, Q2).
- Ejecución **delegando en `cancel_appointment()` de la Spec 010**, sin una segunda lógica
  de cancelación (RF-5), con la liberación del horario que esa spec ya garantiza (RF-6).
- Pantalla de éxito con «Cancelada» y datos de la cita (RF-7).
- Notificación única, sin duplicados ante reintentos (RF-8, RF-9) y guard de doble
  clic/envío (RF-10).
- Estado «Cancelada» y botón «Cancelar cita» en `/citas/confirmada/<id>` (RF-11, RF-12).
- Enlace directo a la cancelación en el correo de confirmación (RF-13; enmienda
  coordinada de la Spec 008).

**Lo que NO cambia**: la transición de estado, la liberación del horario, la
deduplicación de eventos y la notificación viven en la Spec 010 (`cancel_appointment()`);
el contenido del correo de confirmación, salvo el enlace, vive en la Spec 008. Esta spec
solo consume esos servicios (constitución #2 y #3).

## 1. Enfoque técnico

Flujo de cuatro pasos, coherente con RF-1..RF-13:

```text
(1) VALIDACIÓN             (2) CONFIRMACIÓN           (3) EJECUCIÓN           (4) ÉXITO
GET/POST de verificación → pantalla de resumen      →  POST confirmación   →  303 → GET éxito
referencia + documento      servicio · fecha legible   delegar en            «Cita cancelada»
sin ningún cambio           hora · estado              cancel_appointment()  estado «Cancelada»
ventana de 3 h comprobada   botones «Sí…» / «No…»     (Spec 010)            datos + referencia
```

Reglas transversales:

1. **Ningún cambio de estado antes de la confirmación en la pantalla de resumen**
   (RF-3): la validación y la ventana de 3 h son solo lectura.
2. **La identificación se comprueba dos veces**: en el POST de verificación *y* en el
   POST de confirmación (campo oculto con el documento), porque sin sesiones el segundo
   paso debe seguir demostrando la propiedad de la cita (RF-1, RNF seguridad).
3. **La ventana de 3 h se comprueba dos veces** (al mostrar el resumen y al ejecutar),
   porque el tiempo puede pasar entre ambos pasos (RF-4).
4. **La cancelación es una llamada, no una implementación**: la capa de servicio solo
   orquesta verificación + ventana y **delega** en `cancel_appointment()` (RF-5); la
   transición, la liberación del horario y la notificación (correo y evento) son
   garantías de la Spec 010 (RF-6, RF-8).
5. **Idempotencia heredada**: un reintento llega a `cancel_appointment()`, que devuelve
   el centinela `ALREADY_CANCELLED` sin segunda transición ni segunda notificación
   (RF-9); el guard de doble envío evita el segundo envío en el navegador (RF-10).

## 2. Requisitos → diseño (matriz RF)

| RF | Diseño | Prueba clave |
|---|---|---|
| RF-1 | `verify_cancellation_request()` en la capa de servicio, invocada en el POST de verificación y de nuevo en el POST de confirmación (referencia por URL + documento del formulario) | TC-017-001 |
| RF-2 | Un único resultado `FAILED` para «cita inexistente» y «datos que no coinciden», con el mismo literal, el mismo código HTTP (200) y **sin datos de la cita** en la respuesta | TC-017-001, TC-017-010 |
| RF-3 | El POST de verificación **renderiza** la pantalla de resumen (servicio, fecha legible, hora, estado); no hay endpoint GET intermedio ni cambio previo | TC-017-002 |
| RF-4 | Regla `inicio_cita − ahora ≥ 3 h` (borde exacto permitido; iniciada o pasada → rechazada) en la capa de servicio, con `now` explícito para tests deterministas; se comprueba en verificación y en confirmación | TC-017-003 |
| RF-5 | `cancel_verified_request()` llama a `cancel_appointment()` de la Spec 010; el módulo nuevo **no contiene** UPDATE ni transiciones propias | TC-017-004, TC-017-011 |
| RF-6 | Heredado de la Spec 010: tras cancelar, `/citas/horarios` marca el hueco libre y la re-reserva devuelve 303 | TC-017-004 |
| RF-7 | GET de éxito (303 PRG) con «Cita cancelada», mensaje, estado «Cancelada», datos de la cita y referencia `#id` | TC-017-004 |
| RF-8 | La notificación sale de `cancel_appointment()` (correo `appointment.cancellation_email`); el test cuenta **exactamente 1** fila y 1 POST; fallo del webhook → cancelación intacta (contrato Spec 010) | TC-017-005 |
| RF-9 | Reenvío o recarga del POST de confirmación → centinela `ALREADY_CANCELLED` → literal «Esta cita ya fue cancelada.», sin segunda fila ni segundo POST | TC-017-006 |
| RF-10 | Guard en el navegador (patrón HU-006: flag de envío + `preventDefault` + botón `disabled`/`aria-busy`) **más** idempotencia del backend como red de seguridad | TC-017-007, TC-017-012 |
| RF-11 | `/citas/confirmada/<id>` muestra la etiqueta de estado real (`STATUS_CANCELLED_LABEL` cuando `cancelled`) | TC-017-008 |
| RF-12 | `/citas/confirmada/<id>` muestra el botón «Cancelar cita» **solo** cuando la cita está confirmada; enlaza al paso (1) | TC-017-008 |
| RF-13 | El correo de confirmación incluye un enlace absoluto a `/citas/cancelar/<id>` con etiqueta «Cancelar cita» (formato fijado en §3-D9, como exige la enmienda de la Spec 008) | TC-017-009 |

## 3. Decisiones técnicas

- **D1 — Módulo de servicio nuevo** `consultorio/services/cancellation_flow_service.py`:
  contiene la verificación de propiedad y la ventana de 3 h, y **delega** la cancelación
  importando `cancel_appointment()` de `appointment_service` (RF-5, constitución #3).
  *Alternativa descartada*: añadir estas funciones al propio `appointment_service.py` —
  ese fichero está siendo modificado por los cambios sin commitear de la Spec 010 (T22);
  mezclar ambos trabajos añadiría riesgo de conflicto y de romper la fase en curso.

- **D2 — Rutas** (formato fijado aquí por mandato de la spec: *«El formato exacto de las
  rutas y del enlace del correo se fija en el `plan.md` de esta spec»*):

  | Método | Ruta | Comportamiento | Éxito |
  |---|---|---|---|
  | GET | `/citas/cancelar/<int:cita_id>` | Formulario de verificación (título «Cancelar cita», aviso previo, referencia visible + campo de documento). **200 siempre**, también para id inexistente | 200; 404 si el id no es numérico (converter `<int>`) |
  | POST | `/citas/cancelar/<int:cita_id>` | Verifica; renderiza el **resumen** o el mensaje de error/restricción/ya cancelada | 200 en todos los casos (0 cambios) |
  | POST | `/citas/cancelar/<int:cita_id>/confirmar` | Re-verifica, re-chequea la ventana y ejecuta vía `cancel_appointment()` | 303 → `/citas/cancelar/<int:cita_id>/exito` |
  | GET | `/citas/cancelar/<int:cita_id>/exito` | Pantalla de éxito (RF-7); si la cita no está cancelada o no existe → 303 al paso (1) | 200 |

  Justificación: paralela a la ruta ya existente `/citas/confirmada/<id>` (mismo prefijo
  `/citas/` + segmento estático antes del id, sin ambigüedad con `/citas/horarios` ni
  `/citas/disponibilidad`), claramente distinta de la superficie interna
  `/admin/citas/<id>/cancelar` de la Spec 018, y con un único URL de entrada para el
  botón (RF-12) y para el enlace del correo (RF-13).
  *Alternativa descartada*: resumen como GET intermedio con URL propia — expondría el
  resumen de la cita a cualquiera con el enlace, sin sesión ni token que lo proteja.

- **D3 — Identificación**: número de referencia (id de la URL) + **número de documento**
  (Q1 aprobada). Se compara `document_number` exacto tras `strip()`; **no** se compara el
  tipo de documento (la decisión de la usuaria fue «referencia + número de documento»).
  El documento nunca va en la URL ni en logs (solo en el cuerpo del POST).

- **D4 — Uniformidad sin fugas (RNF protección de datos)**:
  - GET de verificación: **200 con el mismo formulario** exista o no la cita (evita
    enumerar ids por código de estado).
  - POST: «cita inexistente» y «documento que no coincide» producen **el mismo literal,
    el mismo estado (200) y una respuesta sin nombre, correo, celular, documento, servicio
    ni fecha** de la cita.
  - El estado «ya cancelada» y la restricción de 3 h **solo** se muestran tras una
    verificación correcta (revelarlos sin documento permitiría descubrir citas ajenas).
  - Id no numérico → 404 estándar de Flask (URL mal formada; no informa sobre la
    existencia de citas).

- **D5 — Literales (contractuales y funcionales)**:
  - Módulo nuevo `consultorio/content/cancellation_content.py` con los **11 literales de
    la tabla de la spec** (identificadores en inglés, textos en español):
    `CANCEL_PAGE_TITLE`, `CANCEL_NOTICE`, `CANCEL_CONFIRM_BUTTON`, `CANCEL_BACK_BUTTON`,
    `CANCEL_SUCCESS_TITLE`, `CANCEL_SUCCESS_MESSAGE`, `MSG_VERIFICATION_FAILED`,
    `MSG_ALREADY_CANCELLED`, `MSG_NOTICE_PERIOD`, `CANCEL_BUTTON_LABEL`.
  - El literal «Cancelada» **se reutiliza** de
    `appointment_content.STATUS_CANCELLED_LABEL` (ya existe y ya está espejado); no se
    duplica el texto.
  - `CANCEL_PAGE_TITLE` y `CANCEL_BUTTON_LABEL` tienen el mismo valor («Cancelar cita»)
    porque la spec los lista como dos literales distintos con igual texto.
  - Etiquetas funcionales del formulario y del resumen («Referencia de la cita»,
    «Número de documento», «Servicio», «Fecha», «Hora», «Estado») también en el módulo de
    contenido, al estilo del plan 018 (D6); **ningún texto nuevo fuera de este módulo**.
  - Campo vacío o con formato inválido → **reutiliza** los literales ya contractuales de
    la Spec 004: `MSG_REQUIRED_DOC_NUMBER` y `MSG_INVALID_DOC_NUMBER` (cero copy nuevo).
  - **Espejo obligatorio** en `tests/expected_content.py` (RNF claridad; cambiar un copy
    obliga a PR de spec primero).
  - *Descartado*: añadir un literal de estado «Procesando/Cancelando tu cita…» — la tabla
    de la spec no lo incluye y añadir copy excedería este plan; el estado de proceso se
    expresa solo con `disabled` + `aria-busy` (D8).

- **D6 — Regla de ventana (Q2)** con tiempo de referencia explícito:

  ```text
  inicio = datetime.combine(date.fromisoformat(cita.date), time.fromisoformat(cita.time))
  permitido = (inicio - now) >= timedelta(hours=3)     # borde exacto 3 h: permitido
  ```

  `now: datetime | None = None` (por defecto `datetime.now()`, hora local naive, la misma
  base que `date.today()` ya usada por la reserva). Recibir `now` explícito hace
  deterministas los tests del borde. La cita iniciada o pasada da diferencia negativa →
  **el mismo literal** `MSG_NOTICE_PERIOD` (RF-4 incluye ambos casos; la spec no define un
  literal aparte para «cita pasada», y este plan no inventa copy).

- **D7 — Ejecución e idempotencia (RF-5, RF-8, RF-9, RF-10)**:
  - `cancel_verified_request(...)` → verificación + ventana → `cancel_appointment(id, db,
    AUTOMATION_WEBHOOK_URL, AUTOMATION_TIMEOUT_SECONDS, AUTOMATION_WEBHOOK_AUTH_HEADER)`
    (misma configuración que ya pasa `consultorio/web/appointments.py:129-131`).
  - Mapeo de resultados: `Appointment` → éxito (303); `ALREADY_CANCELLED` → literal
    «Esta cita ya fue cancelada.» (200); `APPOINTMENT_NOT_FOUND` o verificación fallida →
    «No pudimos verificar tu cita…» (200); ventana insuficiente → `MSG_NOTICE_PERIOD`
    (200).
  - Segundo envío (recarga o doble clic residual): la transición condicional de la Spec
    010 devuelve `ALREADY_CANCELLED` y el `UNIQUE(event_id)` impide el duplicado — **una
    sola cancelación, una sola notificación**.
  - Si la Spec 010 altera la firma de `cancel_appointment()` en su fase 2, se ajusta solo
    la llamada; no se reimplementa nada.

- **D8 — Frontend (identidad, estados, RF-10)**:
  - Plantillas en `templates/cancellation/`: `verify.html`, `summary.html`,
    `success.html`; heredan `base.html`; reutilizan las clases `.appointment__*`
    existentes y añaden solo los estilos mínimos que falten en `static/css/main.css`.
  - Paleta Serenidad Natural (`#789B8A`, `#B8D8CE`, `#F7F3EA`, `#D99A7A`, `#E8D5B5`,
    `#30454B`, funcionales `#3D5A4E`/`#7F4527`), contraste AA
    (`docs/design-contrast.md`), párrafos justificados con `hyphens: none`
    (`docs/design-typography.md`), foco visible.
  - Estados de operación coherentes con el backend: **disponible** (formulario);
    **validando/procesando** (botón `disabled` + `aria-busy` durante el envío, sin texto
    nuevo); **éxito** (pantalla de éxito); **conflicto** («Esta cita ya fue cancelada.» y
    restricción de 3 h); **error** («No pudimos verificar tu cita…»).
  - Guard de doble envío (RF-10): patrón HU-006 — flag `submitting` + `preventDefault()`
    en el primer `submit` + `button.disabled = true`, en `static/js/cancellation.js`,
    cargado solo por `summary.html`.
  - Ubicación del **aviso previo** («Si cancelas tu cita, este horario quedará
    libre…»): en la pantalla de verificación (paso 1), para que el paciente lea la
    consecuencia antes de empezar; el resumen no lo repite (decisión de este plan, a
    aprobar).

- **D9 — Enlace del correo de confirmación (RF-13)** — *el formato y el copy se fijan
  aquí, como exige la enmienda 2026-10-13 de la Spec 008*:
  - Ruta destino: `<host>/citas/cancelar/<id>` — construida en la capa web con
    `url_for("cancellation.verify", cita_id=..., _external=True)` durante el
    `POST /citas` (hay contexto de petición) y pasada como **parámetro opcional al final
    de la firma**: `create_booking(..., cancellation_url: str = "")` →
    `send_confirmation(...)` → `build_confirmation_message(appointment,
    cancellation_url: str = "")`.
    Si la cadena está vacía (llamadas de test antiguas u otras vías), **no se añade el
    enlace**: los tests de HU-008 siguen vigentes sin cambios y `EMAIL_FOOTER`, asunto,
    cabecera y estado quedan intactos (exigencia de la propia enmienda de la Spec 008).
  - Etiqueta del enlace: **`EMAIL_CANCEL_LINK_LABEL = "Cancelar cita"`** (reutiliza el
    texto del literal «Botón en la página de la cita»; vive en `cancellation_content.py`
    y se importa desde `email_service`). Se añade como fila/botón nuevo al final del
    cuerpo de texto y del HTML.
  - `EMAIL_HTML_TEMPLATE` gana un marcador opcional de fila de enlace que ambos
    constructores de mensaje pasan (cadena vacía = sin fila); la plantilla no está
    espejada ni es afirmada por ningún test existente (comprobado en el árbol).
  - *Alternativa descartada*: variable de entorno `SITE_BASE_URL` — añade configuración
    de despliegue y puede desincronizarse del host real; `url_for(_external=True)` usa el
    host de la propia petición sin configuración nueva. *También descartada*:
    `url_for` dentro de `email_service` — rompería el test TC-008-014 (stdlib-only de ese
    módulo).
  - **Riesgo asumido y acotado**: esta es la única tarea que edita
    `consultorio/services/appointment_service.py` (ver §8).

- **D10 — Blueprint y registro**: módulo nuevo `consultorio/web/cancellation.py` con
  `bp = Blueprint("cancellation", __name__)` y una línea de registro en
  `create_app()` (`consultorio/__init__.py`), al estilo del blueprint `admin` de la
  Spec 018. *Alternativa descartada*: añadir las rutas a `web/appointments.py` —
  agrandaría un fichero que ya concentra formulario, disponibilidad y confirmación y
  mezclaría dominios (reserva vs. cancelación).

- **D11 — Fecha legible**: el resumen y la pantalla de éxito usan
  `email_service.format_spanish_date()` («martes, 15 de octubre de 2026»), ya existente
  y usada por los correos; sin duplicar lógica de formato.

- **D12 — Datos mostrados**: el resumen (RF-3) y el éxito (RF-7) muestran **solo**
  servicio, fecha legible, hora, estado y referencia `#id`. No se muestran nombre,
  correo, celular ni documento en los pasos del flujo de cancelación (mínima exposición).

- **D13 — Ramas y fases**: `feature/hu-017` desde HEAD `223a43c`; commits por fases
  (contenido → servicio → web/plantillas → RF-11/12 → RF-13 → tests → evidencia), sin
  tocar los cambios sin commitear de la Spec 010.

## 4. Componentes afectados

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `consultorio/content/cancellation_content.py` | nuevo | 11 literales contractuales + etiquetas funcionales + `EMAIL_CANCEL_LINK_LABEL` (D5) |
| `consultorio/services/cancellation_flow_service.py` | nuevo | Verificación de propiedad, ventana de 3 h (`now` explícito) y delegación en `cancel_appointment()` (D1, D6, D7) |
| `consultorio/web/cancellation.py` | nuevo | Blueprint con las 4 rutas del flujo (D2) |
| `templates/cancellation/verify.html`, `summary.html`, `success.html` | nuevos | Pantallas de validación, resumen y éxito (D8) |
| `static/js/cancellation.js` | nuevo | Guard de doble envío RF-10 (D8) |
| `consultorio/__init__.py` | modificado | Registro del blueprint (1 línea) |
| `consultorio/web/appointments.py` | modificado | Estado dinámico + botón «Cancelar cita» (RF-11/12); pasar `cancellation_url` al crear la reserva (RF-13) |
| `templates/appointments/confirmation.html` | modificado | Etiqueta de estado real y botón de cancelación (RF-11/12) |
| `consultorio/services/appointment_service.py` | modificado | Solo el parámetro opcional final `cancellation_url` en `create_booking()` (RF-13; ver riesgo §8) |
| `consultorio/services/email_service.py` | modificado | Añadir el enlace cuando `cancellation_url` no esté vacío (RF-13) |
| `static/css/main.css` | modificado | Estilos mínimos de las pantallas nuevas (D8) |
| `tests/expected_content.py` | modificado | Espejo de los literales nuevos (D5) |
| `tests/test_cancellation_content.py`, `tests/test_cancellation_flow_service.py`, `tests/test_hu_017.py` | nuevos | Espejo, unidad (TDD) y rutas/flujo (§6) |

**No se modifica**: `spec.md`, specs 008/010, la persistencia (sin migraciones: la
liberación del horario y el índice parcial ya existen), `cancel_appointment()` ni
`create_booking()` más allá del parámetro opcional descrito.

## 5. Algoritmo de los handlers (pseudocódigo)

```text
GET /citas/cancelar/<id>:
    → render verify.html (200) siempre — uniforme aunque la cita no exista
    (id no numérico → 404 del converter <int>)

POST /citas/cancelar/<id>:
    doc = strip(form["document_number"])
    vacío        → verify.html + MSG_REQUIRED_DOC_NUMBER      (200, 0 cambios)
    formato malo → verify.html + MSG_INVALID_DOC_NUMBER       (200, 0 cambios)
    r = verify_cancellation_request(id, doc, db, now)
    FAILED            → verify.html + MSG_VERIFICATION_FAILED (200, sin datos de la cita)
    ALREADY_CANCELLED → verify.html + MSG_ALREADY_CANCELLED    (200)
    TOO_SOON          → verify.html + MSG_NOTICE_PERIOD        (200)
    READY             → summary.html con resumen (200); el formulario
                        de confirmación lleva oculto id + documento

POST /citas/cancelar/<id>/confirmar:
    doc = strip(form["document_number"])          # re-verificación (RF-1)
    r = verify_cancellation_request(id, doc, db, now)   # re-chequea ventana (RF-4)
    FAILED/TOO_SOON          → mismos literales que arriba (200, 0 cambios)
    ALREADY_CANCELLED        → verify.html + MSG_ALREADY_CANCELLED (200; RF-9)
    resultado = cancel_verified_request(...)      # delega en cancel_appointment() (RF-5)
    SUCCESS           → 303 → GET .../exito
    ALREADY_CANCELLED → verify.html + MSG_ALREADY_CANCELLED   (200; RF-9, carrera/reintento)

GET /citas/cancelar/<id>/exito:
    cita existe y status == cancelled → success.html (RF-7)
    en otro caso                      → 303 → GET /citas/cancelar/<id>
```

## 6. Estrategia de pruebas

Suite del proyecto: **`python -m pytest -q`** (pytest; sin dependencias nuevas).
TDD en contenido, servicio y rutas (prueba roja → implementación mínima → verde); la
tarea de evidencia es documental y se verifica por revisión.

Archivos: `tests/test_cancellation_content.py` (espejo), 
`tests/test_cancellation_flow_service.py` (unidad con `now` explícito),
`tests/test_hu_017.py` (rutas y flujo completo).

| TC | RF | Qué comprueba | Resultado esperado |
|---|---|---|---|
| TC-017-001 | RF-1, RF-2 | GET verificación id existente/inexistente; POST con id desconocido y con documento incorrecto; id no numérico | 200 uniforme y mismo literal «No pudimos verificar tu cita…»; 0 cambios en BD; sin nombre/correo/celular/documento/servicio/fecha en la respuesta; no numérico → 404 |
| TC-017-002 | RF-3 | POST de verificación correcto | 200 con servicio, fecha legible (día de la semana), hora y estado; cita **sin cambiar** en BD |
| TC-017-003 | RF-4 | Unidad con `now` fijo: 3 h exactas, 2 h 59 min, hora iniciada, hora pasada; ruta con cita a 2 h y a 6 h | 3 h exactas → permitido; el resto → «Solo puedes cancelar tu cita desde el sitio con al menos 3 horas…»; en ruta, 0 cambios |
| TC-017-004 | RF-5, RF-6, RF-7 | Flujo feliz completo: verificación → resumen → confirmación → éxito; `/citas/horarios` y re-reserva | 303 a `/citas/cancelar/<id>/exito` con «Cita cancelada», «Cancelada», datos y `#id`; BD `cancelled`; el hueco aparece libre y la re-reserva da 303 |
| TC-017-005 | RF-8 | Notificación de la cancelación y fallo del canal | Exactamente **1** fila `appointment.cancellation_email` (`sent`) y 1 POST; con webhook caído → evento `failed` y **cancelación intacta** |
| TC-017-006 | RF-9 | Reenvío/recarga del POST de confirmación y visita del enlace del correo sobre cita cancelada | Literal «Esta cita ya fue cancelada.»; 1 sola fila de notificación y 0 POST adicionales |
| TC-017-007 | RF-10 | Guard en el HTML del resumen + doble POST secuencial | Patrón presente (flag + `disabled`/`aria-busy`); el segundo POST no produce segunda cancelación ni segunda notificación |
| TC-017-008 | RF-11, RF-12 | `/citas/confirmada/<id>` en estado confirmado y cancelado | Confirmada → «Confirmada» **con** botón «Cancelar cita»; cancelada → «Cancelada» **sin** botón; desconocida → 404 |
| TC-017-009 | RF-13 | Payload `appointment.confirmation_email` de una reserva hecha por `POST /citas` y uso del enlace | El texto y el HTML contienen el enlace absoluto `…/citas/cancelar/<id>` con etiqueta «Cancelar cita»; `EMAIL_FOOTER` intacto; tests HU-008 **sin cambios** y en verde; abierto sobre cita cancelada → «Esta cita ya fue cancelada.» |
| TC-017-010 | RNF claridad | Espejo de los 11 literales + etiquetas + `EMAIL_CANCEL_LINK_LABEL` en `expected_content.py` | Iguales carácter a carácter; «Cancelada» reutilizado de `appointment_content` |
| TC-017-011 | Constitución #1/#3, RNF separación | Imports y delegación | Sin dependencias nuevas (solo stdlib + Flask ya usado); `cancellation_flow_service` sin UPDATE/transiciones propias (delega en `cancel_appointment()`); sin reglas de negocio en plantillas |
| TC-017-012 | RNF estados UX | Estados del botón y mensajes | Mientras envía: botón `disabled` + `aria-busy`; cada mensaje mostrado corresponde a un literal de la spec y a la respuesta real del backend |
| TC-017-013 | Regresión | `python -m pytest -q` completo | **0 FAIL** con la suite previa intacta (cifra baseline fijada al iniciar) |
| TC-017-014 | Criterios de finalización | Demo manual §criterios de la spec | Reserva → apertura desde el correo → cancelación con documento → resumen → «Cancelada» → hueco libre → re-reserva → correo de notificación; más reintentos, referencia inexistente, documento incorrecto y restricción de 3 h |

**Demo manual y QA (AGENTS.md)**: servidor `python app.py` en marcha al cerrar cada
tarea visible; evidencia en `docs/evidencias/hu-017/qa-hu-017.md` con PASS/FAIL por TC,
checkbox de aceptación, revisión de consola y red, y capturas CDP de escritorio (1280) y
móvil (375) sin desbordamientos (`Emulation.setDeviceMetricsOverride`; no concluir
desbordes con `--window-size=375`).

## 7. Trazabilidad RF ↔ tareas ↔ pruebas

| RF | Tareas (`tasks.md`) | Pruebas |
|---|---|---|
| RF-1 | T2, T5, T6 | TC-017-001, TC-017-004 |
| RF-2 | T1, T2, T5 | TC-017-001, TC-017-010 |
| RF-3 | T1, T4, T5 | TC-017-002 |
| RF-4 | T2, T5, T6 | TC-017-003 |
| RF-5 | T3, T6 | TC-017-004, TC-017-011 |
| RF-6 | T6, T9 | TC-017-004 |
| RF-7 | T1, T4, T6 | TC-017-004 |
| RF-8 | T3, T9 | TC-017-005 |
| RF-9 | T1, T3, T6 | TC-017-006 |
| RF-10 | T4, T9 | TC-017-007, TC-017-012 |
| RF-11 | T7 | TC-017-008 |
| RF-12 | T1, T7 | TC-017-008 |
| RF-13 | T1, T8 | TC-017-009 |
| RNF (claridad/espejo) | T1 | TC-017-010 |
| RNF (separación/const. #1) | T3, T8 | TC-017-011 |
| RNF (estados de operación) | T4 | TC-017-012 |
| Regresión / finalización | T9, T10 | TC-017-013, TC-017-014 |

> Nota: la columna «Tareas» lista las tareas que **implementan** cada RF; T9 (regresión)
> y T10 (evidencia) recorren además todos los RF al cierre.

## 8. Riesgos, dependencias y restricciones

1. **⚠️ Working tree con cambios sin commitear de la Spec 010 fase 2A (T22)**: este plan
   **no los toca ni los sobrescribe**. T1–T7 y T9–T10 no modifican
   `appointment_service.py`; **T8 sí** (parámetro opcional de `create_booking`). Si T22
   sigue sin commitear al llegar T8, se pospone y se comunica al coordinador; no se
   mezclan ambos cambios en el mismo commit.
2. **Dependencia de la Spec 010** (servicio centralizado): `cancel_appointment()`,
   transición condicional `confirmed → cancelled`, liberación del horario (índice
   único parcial), `UNIQUE(event_id)` y notificación best-effort. RF-5, RF-6, RF-8 y
   RF-9 de esta spec se apoyan íntegramente en esas garantías: si su fase 2 altera
   firmas o comportamiento, se reajusta solo la llamada (nunca duplicando lógica).
3. **Dependencia de la Spec 008** (correo de confirmación): la enmienda 2026-10-13
   autoriza el enlace y fija que su copy lo determine este plan. Restricción asumida:
   no alterar asunto, cabecera, pie ni estado del correo, y mantener los tests de HU-008
   **sin modificaciones**. Si la Spec 008 cambia, se re-planifica T8.
4. **Baseline por fijar**: la suite puede estar en movimiento por T22; la cifra exacta de
   partida se registra en `tasks.md`/evidencia al iniciar. Objetivo inamovible:
   **0 FAIL**.
5. **URL absoluto del enlace**: depende del `Host` de la petición (`url_for(_external=True)`).
   Detrás de proxy o en Render usa el host público de la petición; si se detectara un host
   incorrecto, deberá elevarse a decisión (eventual `SERVER_NAME`/`ProxyFix`), fuera de
   este plan salvo autorización.
6. **Privacidad**: ni URLs, ni logs, ni mensajes muestran documento, nombre, correo o
   celular; el resumen y el éxito solo muestran servicio, fecha, hora, estado y
   referencia (D12).
7. **UX ante doble clic concurrente**: la segunda respuesta puede mostrar «Esta cita ya
   fue cancelada.»; es el comportamiento previsto por RF-9 y el guard JS minimiza el
   caso. Aceptado, no es defecto.
8. **Observación fuera de este plan (no se toca `spec.md`)**: la revisión de 2026-10-23
   señaló la errata «número de documento de documento» en RF-1 (ítem P-2). Se comunica
   al coordinador para decidir la enmienda; este plan no corrige la spec.
9. **Constitución**: sin dependencias nuevas (#1), spec primero (#2), lógica ≠ interfaz
   (#3), tests obligatorios (#4), integridad en persistencia (#5, heredada de la Spec
   010), textos en español (#6).

## 9. Fuera de alcance

De la spec, sin cambios: login/sesiones/tokens; reprogramación; políticas de
cancelación adicionales; gestión de la notificación (la coordina la Spec 010); WhatsApp
(Spec 009); agenda interna (Specs 011/012); cancelación por el consultorio (Spec 018);
tabla de auditoría adicional.

## 10. Decisiones de este plan pendientes de aprobación

Este documento estaba en borrador. Las siguientes decisiones fueron **aprobadas
expresamente por la usuaria el 2026-10-25** junto con el plan y las tareas:

- **Q-A — Formato de las rutas** (D2): `/citas/cancelar/<id>`, `…/confirmar`,
  `…/exito` (la spec delega su fijación en este plan).
- **Q-B — Copy del enlace del correo** (D9): etiqueta «Cancelar cita» reutilizando el
  literal existente, construido con `url_for(_external=True)` en la capa web.
- **Q-C — Ubicación del aviso previo** (D8): pantalla de verificación.
- **Q-D — Destino de «No, volver»**: enlace a `/citas/confirmada/<id>` (el paciente
  vuelve a su cita, donde puede reintentar); descartado `history.back()` por
  impredecible.
- **Q-E — Id no numérico** (D4): 404 del converter, frente a una respuesta 200
  uniforme con validación de formato en ruta.
- **Q-F — Orden con la Spec 010/T22** (§8.1): posponer T8 si T22 sigue sin commitear.

**Estado: aprobado (2026-10-25) — plan, tareas y decisiones Q-A…Q-F autorizados; la
implementación inicia por T1 en `feature/hu-017`.**
