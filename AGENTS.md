# AGENTS.md — consultorio-psicologico

## Proyecto

Aplicación web en Python/Flask para la gestión de citas y la presentación de
información del consultorio.

Tecnologías y componentes principales:

* Backend: Python 3.14+, type hints en todas las funciones públicas y Flask 3.1.3+
* Persistencia: SQLite.
* Frontend: HTML, CSS y JavaScript.
* Comunicación frontend/backend: HTTP y `fetch()`.
* Plantillas: `templates/`.
* Recursos estáticos: `static/`.
* Persistencia y reglas de citas: módulos Python del proyecto.
* Punto de entrada: `app.py`.
* Código de dominio: paquete `consultorio/`.
* Ejecución: Python 3.14.8 del sistema (sin `.venv`).
* Pruebas: suite automatizada y pruebas específicas de las Historias de Usuario.
* Identificadores en inglés; mensajes de usuario en español.

Las decisiones arquitectónicas concretas deben estar respaldadas por la
especificación y su `plan.md`.

## Spec Driven Development

La prioridad documental es:

1. `AGENTS.md` — reglas permanentes.
2. `docs/constitution.md` — principios y restricciones.
3. Requisitos aprobados.
4. Especificación activa en `specs/`.
5. `plan.md` asociado a la especificación.
6. Implementación.
7. Tests y evidencias.
8. `MEMORY.md` — contexto resumido.

### Reglas

- No implementar una funcionalidad que no esté suficientemente especificada. Preguntar primero.
- Lee `docs/constitution.md` y la spec activa en `specs/` antes de tocar código.
- No añadas dependencias, ni modifiques nada sin actualizar antes la spec.
- No modifiques archivos dentro de `specs/` salvo petición explícita.

Antes de modificar código:

1. Identificar la RF correspondiente.
2. Leer la especificación activa.
3. Leer el `plan.md`.
4. Revisar criterios de aceptación.
5. Identificar módulos afectados.
6. Revisar modelo de datos y decisiones técnicas.
7. Revisar estrategia de tests.
8. Comprobar el estado de Git.
9. Implementar únicamente lo respaldado por la especificación.

Si existe una contradicción entre código y especificación, detener la
implementación y pregunta para resolver primero la discrepancia documental.

## Estructura documental SDD

Las especificaciones deben permanecer separadas de la implementación.

Convención:

* `specs/` → requisitos y comportamiento esperado.
* `specs/<especificación>/plan.md` → diseño técnico.
* `tests/` → validación automatizada.
* `docs/` → documentación, decisiones, evidencias y trazabilidad.
* `docs/evidencias/hu-XXX/qa-hu-XXX.md` → informe QA de la HU con capturas
  (PNG) en la misma carpeta; usar checkbox en los criterios de aceptación.
* `MEMORY.md` → memoria breve del estado del proyecto.

## Trazabilidad

Toda implementación debe poder seguir la cadena:

**HU/RF → Spec → plan.md → código → tests → evidencia → commit**

Todo cambio funcional importante debe indicar qué requisito o criterio de
aceptación lo justifica.

No introducir funcionalidades "por conveniencia" sin requisito, criterio o
decisión documentada.


## Cambios en especificaciones

* No modificar una especificación para justificar retrospectivamente una
  implementación.
* Si cambia un requisito, actualizar primero la especificación.
* Si el cambio afecta arquitectura, datos, API, UX o tests, actualizar también
  `plan.md`.
* No modificar archivos dentro de `specs/` salvo petición explícita o decisión formal.
* No eliminar requisitos o criterios sin preguntar y registrar la decisión y su justificación.

### Textos contractuales

* Los textos literales definidos en la spec son contrato: cambiar un copy
  obliga a un PR de spec primero.
* `tests/expected_content.py` es el espejo de esos textos; si cambia la spec,
  cambian juntos spec y test en el mismo PR.

## Base de datos e integridad

* La integridad de las citas debe protegerse en el punto de persistencia, no únicamente mediante validaciones del frontend.
* Las reglas de unicidad, incluyendo `servicio + fecha + hora`, deben estar
  respaldadas por la estrategia definida en la especificación.
* Las comprobaciones previas de disponibilidad no sustituyen la protección de persistencia ante concurrencia.
* No modificar tablas, índices, restricciones o migraciones sin actualizar
  previamente la spec y el `plan.md` correspondiente.
* Todo saneamiento de datos históricos debe contar con una decisión explícita, estrategia de respaldo/auditoría y pruebas.
* Los errores de persistencia deben traducirse a comportamientos de usuario
  definidos por la especificación.

## Frontend y UX

Los estados de una operación deben ser coherentes con el comportamiento real del sistema.

Cuando corresponda, deben contemplarse:

* disponible;
* validando;
* procesando;
* éxito;
* conflicto;
* error.

Además:

* Un botón de envío debe evitar acciones duplicadas mientras la operación esté en curso cuando así lo establezca la especificación.
* Los mensajes visibles deben corresponder al estado real del backend.
* La disponibilidad de horarios debe actualizarse correctamente al cambiar
  servicio, fecha u otros filtros.
* Un horario ocupado no debe volver a mostrarse disponible por cambiar de
  servicio si la regla de negocio indica que debe permanecer bloqueado.
* Los cambios UX/UI deben validarse funcionalmente y mediante evidencia visual cuando el criterio de aceptación lo requiera.

#### 🎨 Identidad visual y paleta de colores

La identidad visual del proyecto utiliza la paleta Serenidad Natural, basada en una estética serena, natural, profesional y cálida.

Paleta principal
Rol	         Color	               HEX	      Uso recomendado
Primario — Salvia	Verde salvia	#789B8A	Navegación, botones principales, acciones y elementos destacados
Secundario — Verde agua	Verde agua	#B8D8CE	Fondos secundarios, tarjetas, elementos de apoyo
Fondo — Marfil	Marfil	#F7F3EA	Fondo principal 
Acento — Terracota	Terracota	#D99A7A	Énfasis, llamadas de atención y elementos destacados
Apoyo — Arena	Arena	#E8D5B5	Fondos complementarios y elementos decorativos
Texto — Azul grisáceo	Azul grisáceo oscuro	#30454B	Texto principal, títulos y elementos de alta legibilidad

Reglas de aplicación
#789B8A debe ser el color principal de acciones y navegación.
#F7F3EA debe utilizarse como fondo principal cuando corresponda.
#30454B debe utilizarse como color base para textos y títulos.
#B8D8CE y #E8D5B5 deben utilizarse como colores secundarios de apoyo.
#D99A7A debe reservarse para acentos y elementos que necesiten énfasis.

No introducir nuevos colores de marca sin una decisión de diseño documentada.
Los colores nuevos necesarios para estados funcionales deben mantener
coherencia visual con la paleta y cumplir requisitos de contraste y
accesibilidad.
Los cambios de identidad visual deben actualizar la documentación de diseño antes de modificar la interfaz.

Regla SDD para diseño

La paleta es una restricción de diseño, no una sugerencia opcional.
Cualquier cambio permanente en colores, tipografía o identidad visual debe
quedar respaldado por una decisión documentada.

#### Reglas de texto (permanentes)

* Todos los párrafos y textos de contenido van **justificados y ajustados al cajón
  de texto**: `text-align: justify` + `hyphens: none`, **sin guiones visibles ni
  cortes de palabras** (los saltos de línea se hacen solo en espacios). La decisión
  se documenta antes en `docs/design-typography.md`.

#### Servidor para revisión visual

* Al finalizar cada tarea o modificación que deba ser visualizada por el usuario
  para su aprobación, dejar **el servidor en marcha** (`python app.py`) y comunicar
  la URL correspondiente.

## Git y control de cambios

Antes de modificar código:

* ejecutar `git status`;
* confirmar la rama de trabajo;
* revisar cambios locales;
* comprobar la relación con el remoto;
* actualizar la rama cuando corresponda.

Flujo recomendado:

**Revisar → Especificar → Planificar → Modificar → Testear → Validar →
Commit → Push → Verificar sincronización → QA → Evidencia → Cierre**

Para cada HU/RF:

* trabajar en su rama correspondiente;
* mantener aislados los cambios de otras HUs;
* utilizar commits descriptivos;
* verificar sincronización con el remoto;
* conservar trazabilidad entre commit y requisito.

No modificar código directamente sobre `main` cuando la HU requiera una rama de trabajo específica.

## Tests

Toda implementación debe validar, cuando corresponda:

* criterios de aceptación;
* comportamiento funcional;
* casos normales;
* casos límite;
* errores;
* persistencia;
* integridad de datos;
* concurrencia;
* interacción frontend/backend;
* regresiones;
* estados visuales.
* utilizar checkbox.

Antes de declarar una tarea terminada:

1. Ejecutar la suite automatizada disponible.
2. Ejecutar las pruebas específicas de la HU.
3. Realizar validación manual/navegador cuando corresponda.
4. Registrar resultados PASS/FAIL.
5. Revisar regresiones.
6. Registrar evidencia.
7. Documentar cualquier pendiente.
8. Utilizar checkbox.

**No declarar PASS únicamente mediante inspección del código.**

Para tareas QA (diseño y ejecución de pruebas) usar el skill `pytest-qa`.

### Evidencia visual (capturas)

* Chrome 154 headless no renderiza correctamente por debajo de 500 px:
  `--window-size=375` recorta la página y la maqueta parece desbordada.
* Para capturas exactas usar DevTools Protocol
  (`Emulation.setDeviceMetricsOverride`), no `--window-size`.

## Comandos habituales

### Ejecutar aplicación

```powershell
python app.py
```

### Tests

```powershell
python -m pytest -q
```

### Instalación de dependencias

`pip` está bloqueado por AppLocker; usar siempre el módulo:

```powershell
python -m pip install <paquete>
```

### Estado Git

```powershell
git status
```

### Ramas

```powershell
git branch -vv
```

### Sincronización

```powershell
git fetch origin
```

Los comandos deben adaptarse a la configuración real del proyecto y nunca
asumirse como disponibles sin comprobar el entorno.


## Definition of Done

Una tarea no se considera terminada únicamente porque el código funcione
localmente.

Debe cumplirse, según corresponda:

* [ ] Requisito identificado.
* [ ] Spec vigente.
* [ ] `plan.md` actualizado cuando aplique.
* [ ] Implementación realizada.
* [ ] Tests ejecutados.
* [ ] Regresión revisada.
* [ ] Validación manual realizada cuando corresponda.
* [ ] Evidencia disponible.
* [ ] Git trazable.
* [ ] Rama sincronizada.
* [ ] Documentación actualizada.
* [ ] Criterios de aceptación satisfechos.
* [ ] Solicitar la aceptación cuando corresponda.

Si existe un elemento pendiente, el estado debe declararse como:

**PENDIENTE**, **PARCIAL** o **BLOQUEADO**.

Nunca declarar **COMPLETADO** si existe un requisito de cierre pendiente.

## Regla de oro

**Primero especificar → después planificar → luego implementar → finalmente
validar.**

La implementación nunca debe convertirse en la fuente de verdad de los
requisitos.

La fuente de verdad funcional es la especificación aprobada.

Nunca reescribas código que ya funciona.

## Memoria del proyecto

* Al comenzar una tarea, leer `MEMORY.md`.
* Usar la memoria para conocer estado, decisiones, riesgos y errores conocidos.
* Al terminar una tarea, actualizar `MEMORY.md` con:
  - estado actual;
  - decisiones relevantes y su justificación;
  - problemas encontrados y cómo evitarlos;
  - pendientes para la siguiente sesión.
* Mantener `MEMORY.md` breve y evitar duplicar información que pertenezca a
  `specs/`, `plan.md` o `docs/`.
* Si una regla se convierte en permanente, proponer incorporarla a `AGENTS.md`.
* Nunca guardar claves, tokens, contraseñas, datos de pacientes u otros datos
  sensibles en la memoria o documentación.
