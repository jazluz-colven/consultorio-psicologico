# Spec 016 — Buscar contenido del sitio

## Contexto y objetivo
El visitante necesita localizar rápidamente información de interés (servicios,
presentación institucional, secciones) sin recorrer toda la navegación. La
funcionalidad ofrece un campo de búsqueda bajo el menú principal y una página de
resultados que enlaza al contenido disponible en el sitio.

## Usuarios / actores
- Visitante del sitio web.

## Historias de usuario
- H1: Como visitante quiero buscar contenido del sitio para llegar antes a la
  información que me interesa.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO el visitante envíe un término de búsqueda, EL SISTEMA mostrará una
  página de resultados con las coincidencias encontradas, cada una con título, extracto
  y enlace a la sección correspondiente.
- RF-2: CUANDO el término no coincida con ningún contenido, EL SISTEMA informará que
  no se encontraron resultados para ese término.
- RF-3: CUANDO el término esté vacío o solo contenga espacios, EL SISTEMA solicitará
  escribir un término de búsqueda, con respuesta HTTP 200 (sin error).
- RF-4: EL SISTEMA mostrará el formulario de búsqueda en la cabecera de todas las
  páginas que usan `base.html`, debajo del menú de navegación.
- RF-5: CUANDO el visitante escriba el término con mayúsculas, minúsculas o sin
  acentos, EL SISTEMA realizará la búsqueda de forma insensible a mayúsculas y a
  acentos.

## Contenido buscable
Índice de búsqueda (contenido estático del sitio, sin base de datos):

- **Portada** (`/`): lema, párrafo de presentación, resumen de servicios y frase de
  valores.
- **Nosotros** (`/nosotros`): Misión, Visión, Experiencia profesional y Valores.
- **Servicios** (`/servicios`): nombre, descripción y beneficios de Psicología
  Integral y Psiconutrición.
- **Navegación**: enlaces del menú principal (Inicio, Nosotros, Servicios, Blog,
  Contacto, Agendar cita).

Cada resultado enlaza a la página donde se encuentra el contenido.

## Textos literales de la interfaz (contrato)

- Etiqueta del campo: `Buscar en el sitio`
- Placeholder del campo: `Buscar en el sitio…`
- Texto del botón: `Buscar`
- Título de la página de resultados: `Resultados de búsqueda`
- Consulta vacía: `Escribe un término para buscar en el sitio.`
- Sin coincidencias: `No se encontraron resultados para «{término}».`
- Con coincidencias: `{n} resultado(s) para «{término}».`

## Requisitos no funcionales
- La página de resultados debe ser legible en escritorio y móvil, con la paleta
  Serenidad Natural y la tipografía vigente (`docs/design-typography.md`).
- La búsqueda no requiere JavaScript: se resuelve con un formulario GET y una ruta
  del servidor.
- Sin dependencias nuevas: la normalización de acentos usa la librería estándar
  (`unicodedata`) — constitución #1.
- El formulario no forma parte del `<nav>` (los tests de navegación cuentan
  exclusivamente los enlaces del menú).

## Casos límite
- Consulta vacía o solo espacios.
- Consulta sin coincidencias.
- Consulta con mayúsculas/minúsculas y sin acentos (p. ej. `psiconutricion`).
- Consulta muy larga o con caracteres especiales: se procesa sin error (200).
- Secciones del menú aún no implementadas (Blog, Contacto, Agendar cita): aparecen
  como resultado con su enlace, que responde «Sección en construcción».

## Fuera de alcance
- Búsqueda en el blog (pendiente de la Spec 013).
- Filtrado en vivo con JavaScript.
- Historial de búsquedas, sugerencias y ordenación por relevancia avanzada.
- Base de datos o índice persistente.

## Criterios de finalización
Todos los RF con test en verde y demostración manual de una búsqueda con resultados,
una sin resultados y una consulta vacía.

## Dudas abiertas
- ~~[NECESITA ACLARACIÓN] Definir el alcance del buscador.~~ **CERRADA (2026-10-08):
  buscador funcional sobre el contenido actual (portada, nosotros, servicios y menú),
  ruta `GET /buscar`, sin JavaScript (decisión del usuario).**
