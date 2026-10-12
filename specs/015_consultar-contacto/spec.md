# Spec 015 — Consultar información de contacto

## Contexto y objetivo
El visitante necesita encontrar rápidamente los canales oficiales para comunicarse con el consultorio. La funcionalidad concentra la información de contacto y los horarios de atención en un único espacio, reduciendo la fricción para solicitar información o establecer comunicación.

## Usuarios / actores
- Visitante del sitio web.

## Historias de usuario
- H1: Como visitante quiero visualizar los datos de contacto del consultorio para comunicarme fácilmente.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO un visitante ingrese a la sección Contacto, EL SISTEMA mostrará los datos de contacto disponibles.
- RF-2: CUANDO la información de contacto incluya dirección, EL SISTEMA mostrará la dirección correspondiente.
- RF-3: CUANDO el consultorio disponga de teléfono, WhatsApp y correo electrónico, EL SISTEMA mostrará esos canales de comunicación.
- RF-4: CUANDO el visitante consulte la sección Contacto, EL SISTEMA mostrará los horarios de atención.
- RF-5: CUANDO existan redes sociales oficiales aprobadas, EL SISTEMA mostrará enlaces hacia ellas.
- RF-6: EL SISTEMA mantendrá diferenciados los canales de contacto y sus datos para facilitar su consulta.

## Requisitos no funcionales
- La información debe ser clara y legible en escritorio y móvil.
- Los datos de contacto deben presentarse de forma comprensible y fácil de localizar.

## Casos límite
- Dirección no aplicable.
- Algún canal de contacto no disponible.
- Horarios de atención no definidos.
- Enlace a una red social no disponible.

## Fuera de alcance
- Gestión de mensajes recibidos.
- Chat en línea.
- Administración de redes sociales.

## Criterios de finalización
Todos los RF con test en verde y demo manual de la consulta de los canales de contacto, horarios y enlaces oficiales disponibles.

## Contenido de contacto (contrato fijado 2026-10-12)

> Los literales de esta sección son contrato (Q8/D12): cambiar un copy obliga a un
> PR de spec primero y a actualizar `tests/expected_content.py` en el mismo PR.

- `CONTACT_PAGE_TITLE`: «Contacto» (h1 de la sección).
- `ADDRESS_LINES` (RF-2): «Calle 34 #29-18» / «Mejoras Públicas» / «Bucaramanga, Colombia».
- `PHONE` (RF-3): **sin teléfono disponible**. El dato es opcional y, mientras no
  exista, el sistema **no muestra** el bloque «Teléfono» (RF-3 es condicional:
  «CUANDO el consultorio disponga de teléfono, WhatsApp y correo electrónico»).
- `WHATSAPP` (RF-3): `+573168756020` (enlace `https://wa.me/573168756020`).
- `EMAIL` (RF-3): `caritogomez26@gmail.com` (enlace `mailto:caritogomez26@gmail.com`).
- `OFFICE_HOURS` (RF-4; propuesta D13 del plan 015 aprobada por la usuaria):
  - Mañana — Lunes a viernes — 8:00 a. m. – 11:30 a. m.
  - Tarde — Lunes a viernes — 2:00 p. m. – 4:30 p. m.
- `SOCIAL_LINKS` (RF-5): Instagram — etiqueta «Instagram» —
  `https://www.instagram.com/psi.carolinagomez/` (única red oficial aprobada).
- Etiquetas de bloque (RF-6): «Dirección», «Teléfono», «WhatsApp»,
  «Correo electrónico», «Horarios de atención», «Redes sociales».

## Dudas abiertas

- [RESUELTA 2026-10-12] Datos de contacto definitivos y opcionales: dirección,
  WhatsApp y correo fijados en «Contenido de contacto»; el **teléfono es opcional y
  no disponible** (bloque omitido mientras no exista).
- [RESUELTA 2026-10-12] Redes sociales oficiales: **solo Instagram**
  (`psi.carolinagomez`).
