# Spec 001 — Visualizar la página de inicio

> **Enmienda 2026-10-08:** nombre → `Carolina Gómez`, imagen representativa →
> `hero-presentacion.png` con nuevo alt, cabecera con ilustración de Contenidas y
> RF-4 acotado para admitir el buscador de la Spec 016. Justificación en
> `docs/design-identity.md` y `docs/design-typography.md`.

## Contexto y objetivo
La página de inicio es el primer punto de contacto del visitante con el consultorio. Debe comunicar de forma clara quién es el consultorio, facilitar una primera comprensión de sus servicios y orientar al visitante hacia las secciones principales, generando confianza y reduciendo la fricción para continuar la navegación.

## Usuarios / actores
- Visitante del sitio web.

## Historias de usuario
- H1: Como visitante quiero acceder a una página de inicio atractiva e informativa para conocer el consultorio y los servicios que ofrece.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO un visitante acceda a la página de inicio, EL SISTEMA mostrará una presentación clara del consultorio.
- RF-2: CUANDO un visitante consulte la página de inicio, EL SISTEMA mostrará una imagen representativa del consultorio.
- RF-3: CUANDO un visitante explore la página de inicio, EL SISTEMA ofrecerá accesos claros a las principales secciones del sitio.
- RF-4: EL SISTEMA mantendrá la página de inicio orientada a la presentación institucional y a la navegación inicial del visitante; no se mostrarán formularios de reserva ni de administración (el formulario de búsqueda de la Spec 016, bajo el menú, queda permitido).
- RF-5: CUANDO un visitante explore la página de inicio, EL SISTEMA mostrará un resumen de los servicios ofrecidos, como mínimo Psicología Integral y Psiconutrición, con un acceso a la sección Servicios.
- RF-6: CUANDO un visitante consulte la página de inicio, EL SISTEMA mostrará una frase institucional de valores que refuerce la confianza.
- RF-7: CUANDO un visitante acceda a la página de inicio, EL SISTEMA mostrará de forma visible la marca secundaria «Contenidas» junto a la identidad del consultorio.

## Contenido institucional (textos literales de la portada)
> Estos textos son contractuales. Cualquier modificación exige actualizar esta
> especificación primero y, con ella, `plan.md` y los tests (SDD).

### Identidad (RF-1, RF-7)
- Marca secundaria: `Contenidas` — visible en el bloque principal (hero), por encima del nombre; la cabecera del sitio muestra su ilustración (`static/img/hero-contenidas.png`) junto al nombre (decisión en `docs/design-identity.md`).
- Nombre: `Carolina Gómez`
- Lema: `Acompañamiento psicológico y nutricional con calidez profesional`
- Párrafo de presentación: `Un espacio de atención personalizada donde la salud mental y el bienestar alimentario se abordan con evidencia, escucha y respeto. Te acompañamos en cada etapa con un trato cercano, profesional y confidencial.`

### Imagen representativa (RF-2)
- Recurso: fotografía suministrada por el consultorio (retrato de la profesional en su consultorio con la leyenda «Salud mental»), `static/img/hero-presentacion.png` (380×511).
- Texto alternativo: `Retrato de Carolina Gómez en su consultorio con la leyenda «Salud mental»`
- El archivo se aloja bajo `static/img/`. Si no está disponible, el sistema mostrará un
  recurso sustituto con el mismo texto alternativo.

### Resumen de servicios (RF-5)
- Título del bloque: `Nuestros servicios`
- `Psicología Integral` — `Acompañamiento terapéutico para personas, parejas y familias, con un enfoque integral y basado en evidencia.`
- `Psiconutrición` — `Integración de salud mental y alimentación para construir hábitos sostenibles y una relación saludable con la comida.`
- Acceso del bloque: `Ver todos los servicios` → `/servicios`

### Frase de valores (RF-6)
`Acompañamos con profesionalismo, empatía y confidencialidad. Nuestro compromiso es tu bienestar en un espacio seguro y sin juicios.`

### Navegación (RF-3)
- `Inicio` → `/`
- `Nosotros` → `/nosotros`
- `Servicios` → `/servicios`
- `Blog` → `/articulos`
- `Contacto` → `/contacto`
- `Agendar cita` → `/citas`

## Requisitos no funcionales
- La información debe ser comprensible y legible en dispositivos de escritorio y móviles.
- La experiencia debe mantener una presentación institucional coherente.
- La imagen representativa no debe desplazar el contenido al cargarse.

## Casos límite
- Imagen representativa no disponible.
- Contenido institucional incompleto: EL SISTEMA completará los campos faltantes con
  los literales definidos en «Contenido institucional».
- Acceso a una sección desde un enlace principal no disponible: la portada solo enlaza a
  rutas existentes; una sección aún no implementada responde con un mensaje de
  «sección en construcción» y un retorno al inicio.

## Fuera de alcance
- Gestión de citas.
- Notificaciones.
- Administración de contenidos del blog.

## Criterios de finalización
Todos los RF con test en verde y demostración manual de la navegación principal y del contenido institucional.

## Dudas abiertas
- (Ninguna. Resueltas: contenido institucional adicional = resumen de servicios +
  frase de valores + marca secundaria «Contenidas»; textos por defecto = literales
  de esta sección; imagen representativa = recurso suministrado.)
