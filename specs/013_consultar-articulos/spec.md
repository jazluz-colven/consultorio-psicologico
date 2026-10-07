# Spec 013 — Consultar artículos del blog

## Contexto y objetivo
El blog permite ofrecer contenido público de interés relacionado con salud mental y fortalecer la relación informativa con los visitantes. La funcionalidad debe permitir consultar un listado de publicaciones y acceder al contenido completo de cada artículo disponible.

## Usuarios / actores
- Visitante del sitio web.

## Historias de usuario
- H1: Como visitante quiero leer artículos sobre salud mental para obtener información de interés.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO existan publicaciones disponibles y el visitante ingrese al Blog, EL SISTEMA mostrará el listado de artículos.
- RF-2: CUANDO el visitante seleccione un artículo disponible, EL SISTEMA mostrará su contenido completo.
- RF-3: SI no existen publicaciones disponibles, ENTONCES EL SISTEMA informará que no hay artículos publicados.
- RF-4: EL SISTEMA mantendrá accesibles únicamente las publicaciones disponibles para consulta pública.

## Requisitos no funcionales
- Contenido legible y comprensible en escritorio y móvil.
- Navegación clara entre listado y contenido completo.

## Casos límite
- Blog vacío.
- Artículo sin contenido suficiente.
- Artículo retirado antes de ser consultado.
- Listado con muchos artículos.

## Fuera de alcance
- Creación o publicación de artículos; corresponde a HU-014.
- Comentarios públicos.
- Suscripciones o campañas de contenido.

## Criterios de finalización
Todos los RF con test en verde y demo manual del listado y lectura completa de un artículo.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Definir si el blog requiere categorías, búsqueda o paginación en esta iteración.
