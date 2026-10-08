# Constitución del Proyecto

1. **Simplicidad del stack**: Python + Flask + HTML/CSS/JS vanilla. Prohibido añadir frameworks, ORMs o dependencias sin justificación escrita y aprobación.
2. **Spec primero**: toda funcionalidad implementada corresponde a una spec activa en `specs/`, con criterios de aceptación verificables; si código y spec divergen, se corrige en el mismo PR.
3. **Lógica ≠ interfaz**: la lógica de negocio, la persistencia y la presentación se separan; la interfaz no debe contener reglas de negocio críticas.
4. **Tests obligatorios**: todo cambio funcional incluye o ajusta pruebas y se ejecutan antes de considerar el cambio terminado.
5. **Persistencia íntegra**: reglas de integridad que garanticen datos consistentes y eviten citas duplicadas o inválidas; acceso a datos solo vía la capa de persistencia.
6. **Idioma consistente**: código, nombres técnicos y comentarios en inglés; mensajes al usuario y documentación funcional en español.
