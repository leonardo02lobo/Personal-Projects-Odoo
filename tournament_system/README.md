# Proyecto 1: Sistema Avanzado de Gestión de Eventos y Torneos

Este proyecto expande los módulos base de Odoo para manejar competencias, registros de participantes y fases de evaluación. Es ideal para dominar las relaciones entre modelos y la lógica de negocio interna.

**Descripción:** Un módulo donde se puedan registrar torneos, configurar distintas categorías de competición, y gestionar la inscripción de equipos o individuos. Debe incluir un panel para que los jueces asignen puntuaciones.

## Grado de complejidad: Medio.

### Retos técnicos principales:

- Modelos Relacionales: Uso intensivo de One2many, Many2many y relaciones jerárquicas.

- Campos Computados y Constraints: Calcular la puntuación total en tiempo real usando @api.depends y validar mediante @api.constrains que un participante no exceda el límite de inscripciones.

- Wizards (Asistentes): Crear un asistente transaccional para "Avanzar a la siguiente fase" que filtre a los ganadores y genere los nuevos emparejamientos de forma automática.

- Vistas: Implementar vistas Kanban personalizadas para ver el estado de los equipos y vistas Pivot para analizar estadísticas de los participantes.