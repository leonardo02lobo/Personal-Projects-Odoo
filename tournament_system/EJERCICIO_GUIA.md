# Ejercicio Guía: Sistema de Gestión de Torneos en Odoo 17

> **Nivel:** Medio | **Módulo:** `tournament_system` | **Versión Odoo:** 17.0

Este documento es una guía de estudio que explica, paso a paso, cómo está construido el addon `tournament_system`. Sirve tanto como referencia técnica como ejercicio de aprendizaje para dominar los conceptos clave del desarrollo en Odoo.

---

## Tabla de Contenidos

1. [Visión General](#1-visión-general)
2. [Estructura de Archivos](#2-estructura-de-archivos)
3. [Arquitectura y Relaciones entre Modelos](#3-arquitectura-y-relaciones-entre-modelos)
4. [El Manifiesto (`__manifest__.py`)](#4-el-manifiesto)
5. [Modelos](#5-modelos)
   - [EventTournament](#51-eventtournament---el-torneo)
   - [EventTournamentCategory](#52-eventtournamentcategory---la-categoría)
   - [EventTournamentRegistration](#53-eventtournamentregistration---el-participante)
   - [EventTournamentScore](#54-eventtournamentscore---la-puntuación)
6. [Flujo de Estado del Torneo](#6-flujo-de-estado-del-torneo)
7. [Seguridad y Control de Acceso](#7-seguridad-y-control-de-acceso)
8. [Vistas XML](#8-vistas-xml)
9. [Controladores REST API](#9-controladores-rest-api)
10. [Reportes PDF](#10-reportes-pdf)
11. [Guía de Relaciones en el ORM](#11-guía-de-relaciones-en-el-orm)
    - [Cuándo usar cada tipo](#111-cuándo-usar-cada-tipo)
    - [Atributos clave: ondelete, domain, context](#112-atributos-clave)
    - [Impacto en la base de datos](#113-impacto-en-la-base-de-datos)
12. [Ejercicios Propuestos](#12-ejercicios-propuestos)
13. [Pendientes y Próximos Pasos](#13-pendientes-y-próximos-pasos)

---

## 1. Visión General

El módulo gestiona torneos deportivos o de competencia con las siguientes entidades:

- **Torneo** → tiene varias **Categorías** (por rango de edad)
- **Categoría** → tiene varios **Participantes** (res.partner)
- **Participante** → tiene varias **Puntuaciones** asignadas por un juez
- **Juez** → es un usuario de Odoo (`res.users`) que asigna scores

---

## 2. Estructura de Archivos

La estructura del módulo sigue las convenciones estándar de Odoo:

- `__manifest__.py` — Metadatos del módulo
- `__init__.py` — Entry point Python
- `models/` — Modelos: `event_tournament.py`, `event_tournament_category.py`, `event_tournament_registration.py`, `event_tournament_score.py`
- `views/` — Vistas XML: menú, torneos, categorías, participantes, scores
- `controllers/` — Endpoints REST API
- `security/` — Grupos (`security_groups.xml`) y permisos (`ir.model.access.csv`)
- `report/` — Acciones, layout y templates QWeb para 4 reportes PDF
- `static/` — Icono del módulo y CSS de reportes

---

## 3. Arquitectura y Relaciones entre Modelos

### Diagrama Entidad-Relación

Los modelos se relacionan de la siguiente manera:

- **`event.tournament`** tiene muchas **`event.tournament.category`** (One2many `category_ids`)
- **`event.tournament.category`** tiene muchos **`res.partner`** (One2many `participant_ids`)
- **`res.partner`** (extendido) tiene muchos **`event.tournament.score`** (One2many `score_ids`)
- **`event.tournament.score`** apunta a un participante (`participant_id`) y a un juez (`judge_id → res.users`)
- Los campos `tournament_category_id` y `tournament_id` en `event.tournament.score` son campos `related` que navegan desde el participante

### Diagrama de Herencia de Modelos

- `event.tournament` hereda los mixins `mail.thread` y `mail.activity.mixin` (activa el chatter y el seguimiento de cambios)
- `EventTournamentRegistration` usa `_inherit = 'res.partner'` → extiende el modelo existente sin crear una tabla nueva

> **Concepto clave — `_inherit` vs `_name`:**
> - `_name='nuevo.modelo'` → crea una tabla nueva en la base de datos.
> - `_inherit='modelo.existente'` → extiende un modelo ya existente, añadiendo campos/métodos a su tabla.

---

## 4. El Manifiesto

El archivo `__manifest__.py` es el punto de entrada del módulo. Define sus metadatos y qué archivos cargar.

Los campos clave son:
- `name`, `version` (convención: `<odoo_version>.<major>.<minor>.<patch>`), `category`
- `depends`: lista de módulos requeridos (`['base', 'mail', 'contacts']`)
- `data`: lista ordenada de archivos a cargar (seguridad primero, luego vistas, luego reportes)
- `assets`: CSS cargado en el contexto de reportes QWeb (`web.report_assets_common`)
- `installable`, `application`

> **Ejercicio:** ¿Por qué `security/security_groups.xml` debe cargarse antes que `ir.model.access.csv`?
> Porque el CSV referencia los grupos por su `xmlid`, y si el grupo no existe todavía, el CSV fallará al instalar.

---

## 5. Modelos

### 5.1 `EventTournament` — El Torneo

**Archivo:** [models/event_tournament.py](models/event_tournament.py)

Campos principales:
- `state`: Selection con estados `draft`, `confirm`, `in_progress`, `done`, `cancel`. Usa `tracking=True` para registrar cambios en el chatter.
- `name`: Char — nombre del torneo
- `start_date`, `end_date`: Date
- `category_ids`: One2many hacia `event.tournament.category`
- `company_id`: Many2one hacia `res.company`, con `default=lambda self: self.env.company`

#### Concepto: `_inherit` con mixins de `mail`

Al heredar `mail.thread` y `mail.activity.mixin`, el modelo gana:
- Un **chatter** (historial de mensajes y notas internas) en la vista form.
- La capacidad de que `tracking=True` en campos registre automáticamente cada cambio de valor.

La vista form muestra botones de estado en el header, una statusbar, campos en el sheet y el chatter al final.

#### Método `action_in_progress` — Creación masiva de records

Este método valida que el torneo esté en estado `confirm` y que todas las categorías tengan participantes. Luego construye una lista de dicts y llama a `self.env['event.tournament.score'].create(vals_list)` para crear todos los scores de una sola vez antes de cambiar el estado a `in_progress`.

> **Concepto clave — `self.env['model'].create(vals_list)`:**
> Pasar una lista de dicts a `create()` es más eficiente que llamar `create()` en un loop porque reduce el número de queries SQL.

#### Método `_calculate_podium` — Markup seguro en el chatter

Itera sobre las categorías, busca los scores ordenados por score descendente y construye un mensaje HTML que luego publica en el chatter con `message_post(body=message_html)`. El HTML se envuelve en `Markup()` para marcarlo como contenido de confianza.

> **Concepto — `Markup` de `markupsafe`:**
> En Odoo 17, no se puede pasar HTML crudo a `message_post`. Se usa `Markup()` para indicar que el contenido es HTML de confianza y no debe ser escapado.

---

### 5.2 `EventTournamentCategory` — La Categoría

**Archivo:** [models/event_tournament_category.py](models/event_tournament_category.py)

Campos:
- `name`: Char (required)
- `tournament_id`: Many2one hacia `event.tournament` (inverso de `category_ids`)
- `participant_ids`: One2many hacia `res.partner` (campo inverso: `tournament_category_id`)
- `age_min`, `age_max`: Integer (required)

#### `@api.constrains` — Validación de reglas de negocio

Se valida que `age_min` y `age_max` no sean negativos y que `age_min < age_max`. El decorador `@api.constrains` se ejecuta automáticamente cuando se crea o modifica el registro y alguno de los campos listados cambia. Si lanza una excepción, la transacción se revierte.

#### Override de `create` — Validación de rangos no solapados

Al crear una categoría, se buscan las categorías existentes del mismo torneo y se valida que el `age_min` de la nueva sea mayor al `age_max` de todas las existentes, evitando solapamientos. Siempre se llama a `super().create(vals_list)` al final.

**Lógica de rangos válidos:**
- Válido: rangos consecutivos sin solapamiento (ej. Sub-15: 0-14, Sub-20: 15-19, Sub-30: 20-29)
- Inválido: el `age_min` de la nueva categoría es menor al `age_max` de alguna existente

---

### 5.3 `EventTournamentRegistration` — El Participante

**Archivo:** [models/event_tournament_registration.py](models/event_tournament_registration.py)

Este modelo **extiende** `res.partner` (no crea una tabla nueva). Agrega:
- `tournament_category_id`: Many2one hacia `event.tournament.category`
- `age`: Integer (store=True)
- `score_ids`: One2many hacia `event.tournament.score`
- `tournament_ids`: Many2many computado (navega `tournament_category_id → tournament_id`)
- `tournament_count`: Integer computado

#### `@api.depends` — Campos Computados

`_compute_tournaments` depende de `tournament_category_id` y `tournament_category_id.tournament_id`. La notación con punto permite observar cambios en campos de modelos relacionados. Al cambiar la categoría del partner, el campo `tournament_ids` se recalcula automáticamente.

> **Concepto clave — `@api.depends`:**
> - El decorador le dice a Odoo: "recalcula este campo cuando cambien los campos listados".
> - La notación con punto (`tournament_category_id.tournament_id`) permite observar cambios en campos de modelos relacionados.
> - Si no usas `store=True`, el valor NO se guarda en la base de datos (se recalcula en cada lectura).

#### Validación de edad en `create` y `write`

Se sobreescriben `create` y `write` para llamar a `_check_tournament_category_age()` después de cada operación. Este método verifica que la edad del participante esté dentro del rango `[age_min, age_max]` de su categoría.

> **Por qué validar en `write` además de `create`:** Si alguien cambia el rango de edad de la categoría, ya existe validación en `EventTournamentCategory.write()`. Pero si alguien actualiza la edad del participante, esta validación en `res.partner.write()` atrapa ese caso.

---

### 5.4 `EventTournamentScore` — La Puntuación

**Archivo:** [models/event_tournament_score.py](models/event_tournament_score.py)

Campos:
- `participant_id`: Many2one hacia `res.partner` (domain: solo socios con categoría asignada)
- `judge_id`: Many2one hacia `res.users`, default al usuario actual, readonly
- `tournament_category_id`: campo `related` desde `participant_id.tournament_category_id`, con `store=True` e `index=True`
- `tournament_id`: campo `related` desde `participant_id.tournament_category_id.tournament_id`, con `store=True` e `index=True`
- `score`: Integer (required), validado con `@api.constrains` para que sea >= 0
- `notes`: Char

#### Concepto: Campos `related` con `store=True`

Sin `store=True`, leer `tournament_id` en un score requiere 3 queries encadenadas (score → participant → category → tournament). Con `store=True`, el valor se guarda directamente en la columna del score y se lee en 1 query.

> `store=True` en un campo `related` es un trade-off: usa más espacio en disco pero acelera búsquedas y filtros. Vale la pena cuando el campo se usa frecuentemente en dominios o vistas de lista.

---

## 6. Flujo de Estado del Torneo

El torneo avanza por los siguientes estados mediante métodos de acción:

`draft` → `confirm` → `in_progress` → `done`

En cualquier momento se puede cancelar (`cancel`).

### Validaciones por transición

| Transición | Validaciones |
|---|---|
| `draft → confirm` | Al menos 1 categoría, cada categoría tiene participantes |
| `confirm → in_progress` | Crea automáticamente registros de puntuación en 0 para todos los participantes |
| `in_progress → done` | Todos los participantes tienen `score > 0` y `notes != ''` |
| `done` | Publica el podium en el chatter del torneo |

---

## 7. Seguridad y Control de Acceso

### Jerarquía de Grupos

Los grupos se definen en [security/security_groups.xml](security/security_groups.xml) con una jerarquía de herencia mediante `implied_ids`:

- `base.group_user` (base de Odoo)
- `group_tournament_participant` — hereda de `base.group_user`
- `group_tournament_judge` — hereda de `group_tournament_participant`
- `group_tournament_manager` — hereda de `group_tournament_judge`

> **Concepto — `implied_ids` con `(4, id)`:**
> El comando `(4, id)` en un campo Many2many significa "añadir esta relación sin borrar las existentes". El grupo Manager hereda los permisos de Judge, quien a su vez hereda los de Participant.

### Matriz de Permisos CRUD

**Archivo:** [security/ir.model.access.csv](security/ir.model.access.csv)

| Grupo | Modelo | Crear | Leer | Escribir | Borrar |
|---|---|:---:|:---:|:---:|:---:|
| Manager | `event.tournament` | ✓ | ✓ | ✓ | ✓ |
| Manager | `event.tournament.category` | ✓ | ✓ | ✓ | ✗ |
| Judge | `event.tournament.score` | ✓ | ✓ | ✓ | ✗ |
| Participant | `event.tournament` | ✗ | ✓ | ✗ | ✗ |
| Participant | `event.tournament.category` | ✗ | ✓ | ✗ | ✗ |
| Participant | `res.partner` | ✓ | ✓ | ✗ | ✗ |

> **Nota de diseño:** Los jueces NO pueden borrar scores, solo crearlos y editarlos. Los managers NO pueden borrar categorías (para preservar la integridad del historial). Esto es una decisión consciente de negocio.

---

## 8. Vistas XML

### Menú y Acciones

**Archivo:** [views/tournament_views.xml](views/tournament_views.xml)

Se define un menú raíz con icono personalizado (`web_icon`). Los submenús usan el atributo `groups` para controlar visibilidad:
- "List of Tournament" → solo para `group_tournament_manager`
- "Judge" (panel de puntuaciones) → solo para `group_tournament_judge`

### Vista Form del Torneo

**Archivo:** [views/event_tournament_views.xml](views/event_tournament_views.xml)

La vista form incluye:
- **Header:** botones de acción con visibilidad dinámica (`invisible="state != 'draft'"`) y un widget `statusbar` con `statusbar_visible`
- **Sheet:** título con clase `oe_title`, grupos de campos y un notebook con la pestaña de categorías
- **Chatter:** activado por `mail.thread` con `message_follower_ids`, `activity_ids` y `message_ids`

### Panel de Puntuaciones (editable inline)

**Archivo:** [views/event_tournament_score_views.xml](views/event_tournament_score_views.xml)

La vista tree usa `editable="bottom"` para editar celdas directamente en la lista. Los atributos `create="0"` y `delete="0"` impiden crear o borrar registros desde esta vista. El campo `participant_id` es `readonly`.

### Vista de búsqueda con filtros y agrupaciones

La vista search del panel de scores incluye campos de búsqueda por participante, juez, torneo y categoría. Define un filtro predefinido ("In Progress Tournament") con dominio `[('tournament_id.state', '=', 'in_progress')]` y opciones de agrupación por torneo y categoría mediante `context={'group_by': ...}`.

### Herencia de Vista: Extender `res.partner`

**Archivo:** [views/event_tournament_registration_views.xml](views/event_tournament_registration_views.xml)

Se usa `inherit_id` con referencia a `base.view_partner_form`. Las expresiones XPath localizan nodos de la vista padre:
- `position="after"` sobre el campo `vat` → agrega `tournament_category_id` y `age`
- `position="after"` sobre la pestaña `internal_notes` → agrega una pestaña nueva "Tournaments" con el contador y las relaciones del torneo

> **Concepto — Herencia de Vistas con `xpath`:**
> La herencia de vistas usa expresiones XPath para localizar nodos en la vista padre y el atributo `position` para indicar dónde insertar (`before`, `after`, `inside`, `replace`, `attributes`).

---

## 9. Controladores REST API

El módulo expone una API HTTP usando el sistema de rutas de Odoo. El patrón es: el **controlador** delega la lógica al **modelo**.

### Arquitectura del controlador

El flujo es: HTTP Request → `TournamentController` (con `@http.route`) → `request.env['event.tournament'].sudo()` → método del modelo → `request.make_json_response(data)` → HTTP Response (JSON).

El uso de `.sudo()` evita restricciones de sesión al acceder al ORM.

**Archivo:** [controllers/tournament.py](controllers/tournament.py)

### Mapa de Endpoints

| Endpoint | Descripción |
|---|---|
| `GET /api/tournaments` | Todos los torneos |
| `GET /api/tournaments/<id>` | Torneo por ID |
| `GET /api/tournaments/company/<id>` | Torneos de una empresa |
| `GET /api/tournaments/category` | Torneos con sus categorías |
| `GET /api/tournaments/category/<id>` | Torneo específico con categorías |
| `GET /api/tournaments/category/participants` | Jerarquía completa |
| `GET /api/categories` | Todas las categorías |
| `GET /api/categories/<id>` | Categoría por ID |
| `GET /api/categories/participants/<id>` | Categoría con participantes |
| `GET /api/categories/participants/score/<id>` | Categoría + participantes + scores |
| `GET /api/registration` | Todos los participantes |
| `GET /api/registration/<id>` | Participante por ID |
| `GET /api/registration/scores` | Participantes con sus scores |
| `GET /api/score` | Todos los scores |

> **Nota sobre `auth='public'`:** Estos endpoints no requieren autenticación. En producción deberías considerar `auth='user'` o implementar autenticación por token para proteger datos sensibles.

---

## 10. Reportes PDF

El módulo genera 4 reportes PDF con QWeb, el motor de templates de Odoo.

### Declaración de Reportes

**Archivo:** [report/tournament_report_action.xml](report/tournament_report_action.xml)

Cada reporte se declara como un registro `ir.actions.report` con `report_type='qweb-pdf'`. El campo `report_name` referencia el template QWeb con el formato `módulo.nombre_template`. El `binding_model_id` vincula el reporte a un modelo para que aparezca en el menú de impresión.

### Layout Personalizado (Header/Footer)

**Archivo:** [report/tournament_layout.xml](report/tournament_layout.xml)

El layout define la apariencia global de todos los reportes del módulo. Incluye un header con logo y fecha de generación, el área de contenido, y un footer con datos de la empresa y número de página.

### Paleta de Colores

| Variable | Color | Uso |
|---|---|---|
| `#1C2951` | Azul oscuro (navy) | Encabezados de tablas, bordes |
| `#D4AF37` | Dorado | Acentos, separadores, footer |

### Los 4 Reportes

| Reporte | Modelo | Contenido |
|---|---|---|
| Results of Tournament | `event.tournament` | Info del torneo + tabla de participantes por categoría, ordenados por score |
| Results of Category | `event.tournament.category` | Detalles de categoría + ranking con medallas 🥇🥈🥉 + detalle de scores por juez |
| Participant Profile | `res.partner` | Info personal + torneos inscritos + historial de scores |
| Score Report | `event.tournament.score` | Todos los scores con suma total |

---

## 11. Guía de Relaciones en el ORM

> Esta sección resume los conceptos clave. Para la referencia completa con árbol de decisión, errores comunes y diagramas SQL, ver [`KNOWLEDGE_RELATIONSHIPS.md`](KNOWLEDGE_RELATIONSHIPS.md).

### 11.1 Cuándo usar cada tipo

El módulo usa los cuatro tipos de relación. Aquí están todos en contexto:

| Relación | Ejemplo en el módulo | Archivo |
|---|---|---|
| `Many2one` | `tournament_id` en categoría → apunta a su torneo padre | `event_tournament_category.py:10` |
| `Many2one` | `participant_id` en score → apunta al partner | `event_tournament_score.py:9` |
| `One2many` | `category_ids` en torneo → lista de categorías | `event_tournament.py` |
| `One2many` | `score_ids` en partner → lista de puntuaciones | `event_tournament_registration.py:11` |
| `Many2many` | `tournament_ids` en partner → computado desde categoría | `event_tournament_registration.py:17` |
| `related` | `tournament_id` en score → atajo a través de participante | `event_tournament_score.py:21` |

**Regla de decisión rápida:**

```
¿Apunta a UN registro?          → Many2one
¿Lista de registros hijos?      → One2many  (requiere Many2one inverso en el hijo)
¿Relación N:M bidireccional?    → Many2many (crea tabla intermedia)
¿Shortcut a través de relación? → related   (+ store=True si se filtra frecuentemente)
```

### 11.2 Atributos Clave

#### `ondelete` — qué pasa al borrar el padre

```python
# cascade: el hijo se borra con el padre
tournament_id = fields.Many2one('event.tournament', ondelete='cascade')

# set null: el campo queda vacío (requiere que no sea required)
tournament_category_id = fields.Many2one('event.tournament.category', ondelete='set null')

# restrict: impide borrar el padre si tiene hijos (default para required=True)
company_id = fields.Many2one('res.company', required=True)  # implícitamente restrict
```

| Valor | Cuándo usarlo |
|---|---|
| `'cascade'` | El hijo no tiene sentido sin el padre (ej. líneas de una orden) |
| `'set null'` | El hijo puede existir sin padre (campo opcional) |
| `'restrict'` | La integridad es crítica (no se puede borrar si hay dependientes) |

#### `domain` — filtrar opciones en la UI

```python
# Solo muestra partners que ya tienen categoría asignada
participant_id = fields.Many2one(
    'res.partner',
    domain="[('tournament_category_id', '!=', False)]"
)
```

> **Importante:** `domain` es una restricción de UI, no del ORM. Para validación real en código, usa `@api.constrains`.

#### `context` — pasar valores a vistas relacionadas

```python
# Pre-rellena el torneo al crear un score desde el formulario del torneo
action = {
    'res_model': 'event.tournament.score',
    'context': {
        'default_tournament_id': self.id,          # pre-rellena el campo
        'search_default_tournament_id': self.id,   # activa el filtro
    }
}
```

### 11.3 Impacto en la Base de Datos

| Tipo de campo | ¿Crea columna? | ¿Crea tabla? | Ejemplo en el módulo |
|---|:---:|:---:|---|
| `Many2one` | Sí (FK integer) | No | `tournament_id` en `event_tournament_category` |
| `One2many` | No (virtual) | No | `category_ids` en `event.tournament` |
| `Many2many` regular | No | Sí (intermedia) | — |
| `Many2many` computado | No | No | `tournament_ids` en `res.partner` |
| `related` sin `store` | No | No | — |
| `related` con `store=True` | Sí (desnormalizada) | No | `tournament_id` en `event.tournament.score` |

**El trade-off de `store=True` en campos `related`:**

Sin `store=True`, leer `tournament_id` en un score requiere navegar:
`score → participant_id → tournament_category_id → tournament_id` (2 JOINs extra).

Con `store=True` + `index=True`, el valor vive directamente en la tabla del score:

```python
tournament_id = fields.Many2one(
    "event.tournament",
    related="participant_id.tournament_category_id.tournament_id",
    store=True,   # guarda el valor en la tabla event_tournament_score
    index=True,   # crea un índice B-tree para búsquedas rápidas
    readonly=True,
)
```

Costo: espacio extra en disco + un UPDATE adicional cuando cambia la categoría del participante. Vale la pena cuando el campo se usa en dominios de búsqueda o vistas de lista frecuentes.

---

## 12. Ejercicios Propuestos

### Ejercicio 1: Agregar campo `description` al Torneo (Básico)  

**Objetivo:** Practicar la adición de campos y su uso en vistas.

1. En `event_tournament.py`, agrega un campo `description = fields.Text(string='Description')`
2. En `event_tournament_views.xml`, agrega el campo dentro del `<sheet>` con un placeholder descriptivo
3. Actualiza el módulo en Odoo con `-u tournament_system`

---

### Ejercicio 2: Constraint de fechas (Intermedio)

**Objetivo:** Practicar `@api.constrains` con múltiples campos.

Agrega una validación en `EventTournament` usando `@api.constrains('start_date', 'end_date')` que lance un `UserError` si `start_date > end_date`.

---

### Ejercicio 3: Campo Computado `total_participants` (Intermedio)

**Objetivo:** Practicar campos computados con `@api.depends` en relaciones anidadas.

Agrega un campo `total_participants = fields.Integer(compute='_compute_total_participants')` que dependa de `category_ids` y `category_ids.participant_ids`. El método debe sumar la cantidad de participantes de cada categoría. Muéstralo en la vista tree del torneo.

---

### Ejercicio 4: Wizard "Avanzar a la siguiente fase" (Avanzado)

**Objetivo:** Implementar el wizard pendiente del README.

Crea `wizards/tournament_advance_wizard.py` con un `TransientModel` llamado `tournament.advance.wizard`. El wizard debe tener los campos `tournament_id`, `top_n` (cuántos clasifican) y `next_phase_name`. El método `action_advance` debe:
1. Obtener los participantes ordenados por score descendente
2. Tomar los primeros `top_n`
3. Crear una nueva categoría con el nombre `next_phase_name`
4. Asignar los clasificados a la nueva categoría

---

### Ejercicio 5: Relaciones con atributos explícitos (Intermedio)

**Objetivo:** Practicar `ondelete`, `domain` y `context` en campos relacionales.

1. En `event_tournament_score.py`, agrega `ondelete='cascade'` a `participant_id`. Verifica que al borrar un partner (desde SQL o shell Odoo) sus scores se borren en cascada.
2. En `event_tournament_category.py`, agrega `ondelete='restrict'` a `tournament_id`. Verifica que no puedes borrar un torneo que tenga categorías.
3. En la vista form del torneo, agrega `context="{'default_tournament_id': active_id}"` al botón que abre la lista de scores, para que el torneo se pre-rellene al crear uno nuevo.

> **Pregunta de reflexión:** ¿Por qué `judge_id` en `EventTournamentScore` no necesita `ondelete='cascade'`? ¿Qué pasa si un usuario juez es eliminado del sistema?

---

### Ejercicio 6: Endpoint POST para crear torneos (Avanzado)

**Objetivo:** Extender la API REST con métodos de escritura.

Agrega una ruta `POST /api/tournaments` con `auth='user'` y `type='json'`. El método debe leer el body JSON, crear un torneo con los campos recibidos y retornar el ID del nuevo registro.

> **Considera:** ¿Qué validaciones necesitas? ¿Qué pasa si `name` no se proporciona?

---

## 13. Pendientes y Próximos Pasos

Según el `README.md` original, el módulo tiene estos pendientes:

### Wizard (No implementado)

El wizard de "Avanzar a la siguiente fase" no existe aún. Ver [Ejercicio 4](#ejercicio-4-wizard-avanzar-a-la-siguiente-fase-avanzado) como punto de partida.

El wizard debería:
- Mostrar los participantes clasificados (filtrado por score mínimo o top-N)
- Generar automáticamente los nuevos emparejamientos
- Ser un `TransientModel` (tabla temporal, se limpia automáticamente)

### Mejoras sugeridas

| Área | Mejora |
|---|---|
| Seguridad | Cambiar `auth='public'` a `auth='user'` en los endpoints sensibles |
| Validación | Agregar constraint de fechas (inicio < fin) |
| Reportes | El botón "Generate Report PDF" en `action_report_pdf` está vacío (`pass`) — conectarlo al reporte real |
| Vista | Añadir vista Kanban para ver el estado de equipos (mencionado en README) |
| Vista | Añadir vista Pivot para estadísticas (mencionado en README) |
| Score | Un participante puede tener múltiples scores (uno por juez). Considerar si `score` en `action_done` debería ser el promedio o la suma |
| API | Agregar endpoints POST/PUT/DELETE para una API REST completa |

---

> **Recursos de referencia:**
> - [Odoo 17 ORM Documentation](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html)
> - [Odoo 17 Views](https://www.odoo.com/documentation/17.0/developer/reference/backend/views.html)
> - [QWeb Reports](https://www.odoo.com/documentation/17.0/developer/reference/backend/reports.html)
> - [HTTP Controllers](https://www.odoo.com/documentation/17.0/developer/reference/backend/http.html)
