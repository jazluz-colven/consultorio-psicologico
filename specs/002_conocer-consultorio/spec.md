# Spec 002 — Conocer el consultorio

## Contexto y objetivo
Los visitantes necesitan información institucional antes de decidir si desean solicitar una cita. Esta funcionalidad concentra la misión, visión, experiencia profesional y valores del consultorio para favorecer la confianza y una decisión informada.

## Usuarios / actores
- Visitante del sitio web.

## Historias de usuario
- H1: Como visitante quiero conocer la información del consultorio para generar confianza antes de solicitar una cita.

## Requisitos funcionales (criterios de aceptación en EARS)
- RF-1: CUANDO un visitante seleccione la sección Nosotros, EL SISTEMA mostrará la misión del consultorio.
- RF-2: CUANDO un visitante consulte la sección Nosotros, EL SISTEMA mostrará la visión del consultorio.
- RF-3: CUANDO un visitante consulte la sección Nosotros, EL SISTEMA mostrará la experiencia profesional relevante.
- RF-4: CUANDO un visitante consulte la sección Nosotros, EL SISTEMA mostrará los valores del consultorio.
- RF-5: EL SISTEMA mantendrá la información institucional diferenciada de la información de servicios y citas.

## Contenido institucional (literales)

Estos textos son contrato: su reproducción en la sección Nosotros es verificada por
tests (espejo en `tests/expected_content.py`). Títulos de bloque: `Misión`, `Visión`,
`Experiencia profesional`, `Valores`.

### Misión (RF-1)
`Acompañar a cada persona, pareja o familia en el cuidado de su salud mental y su bienestar alimentario, ofreciendo atención personalizada basada en evidencia, con un trato cercano, respetuoso y confidencial en un espacio seguro y sin juicios.`

### Visión (RF-2)
`Ser un espacio de confianza donde cada persona encuentre las herramientas para comprenderse, cuidarse y sostener cambios duraderos en su bienestar, reconocido por la calidez humana y la solidez profesional con la que acompaña a su comunidad.`

### Experiencia profesional (RF-3)
`Soy profesional en el área de la Psicología, diplomada en primeros auxilios psicológicos, psiconutrición, y a través de esta formación me he dedicado a brindar acompañamiento y herramientas de apoyo emocional y espiritual.`

### Valores (RF-4)
`Profesionalismo basado en evidencia. Escucha empática y sin juicios. Confidencialidad y respeto en cada proceso. Calidez humana y compromiso con el bienestar de cada persona.`

## Requisitos no funcionales
- La información debe ser clara, legible y comprensible en escritorio y móvil.

## Casos límite
- Falta alguno de los contenidos institucionales.
- Contenido excesivamente extenso para una lectura clara.

## Fuera de alcance
- Registro de pacientes.
- Agendamiento y cancelación de citas.
- Gestión administrativa del contenido.

## Criterios de finalización
Todos los RF con test en verde y demostración manual de la consulta completa de la información institucional.

## Dudas abiertas
- (Ninguna. Resuelta el 2026-10-07: el contenido definitivo de misión, visión,
  experiencia profesional y valores fue aprobado y fijado en «Contenido institucional».)
