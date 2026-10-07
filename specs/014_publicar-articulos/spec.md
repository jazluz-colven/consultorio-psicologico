# Spec 014 — Publicar artículos

## Contexto y objetivo
El consultorio necesita mantener actualizado su contenido público sin depender de modificaciones manuales del sitio. La funcionalidad permite a un administrador crear y publicar artículos para que los visitantes puedan consultarlos.

## Usuarios / actores
- Administrador.
- Visitante del sitio web como consumidor del contenido publicado.

## Historias de usuario
- H1: Como administrador quiero publicar artículos en el blog para mantener actualizado el contenido del sitio.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO un administrador autorizado cree una nueva publicación y la guarde, EL SISTEMA dejará el artículo disponible para los visitantes.
- RF-2: SI un usuario no autorizado intenta publicar un artículo, ENTONCES EL SISTEMA impedirá la acción.
- RF-3: CUANDO un artículo sea publicado, EL SISTEMA permitirá que aparezca en el listado público del blog.
- RF-4: SI el contenido obligatorio de una publicación está incompleto, ENTONCES EL SISTEMA no la publicará hasta corregirlo.
- RF-5: EL SISTEMA mantendrá diferenciada la gestión administrativa de la consulta pública del blog.

## Requisitos no funcionales
- Control de acceso para la publicación.
- Integridad y legibilidad del contenido publicado.
- Protección de la información administrativa.

## Casos límite
- Contenido vacío.
- Publicación duplicada.
- Usuario sin autorización.
- Publicación guardada parcialmente.
- Artículo retirado después de su publicación.

## Fuera de alcance
- Edición avanzada o versionado de contenido, salvo que se apruebe expresamente.
- Comentarios públicos.
- Automatización de campañas de difusión.

## Criterios de finalización
Todos los RF con test en verde, incluyendo control de acceso y validación de contenido, más demo manual de creación y publicación.

## Dudas abiertas
- [NECESITA ACLARACIÓN] Definir los campos obligatorios de un artículo.
- [NECESITA ACLARACIÓN] Confirmar si se requiere edición, borrado o despublicación en esta iteración.
