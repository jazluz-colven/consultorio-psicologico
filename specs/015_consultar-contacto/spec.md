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

## Dudas abiertas
- [NECESITA ACLARACIÓN] Confirmar cuáles son los datos de contacto definitivos y cuáles son opcionales.
- [NECESITA ACLARACIÓN] Confirmar las redes sociales oficiales que deben mostrarse.
