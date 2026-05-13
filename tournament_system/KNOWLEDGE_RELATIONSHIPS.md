# Knowledge: Relaciones en el ORM de Odoo

> **Módulo de referencia:** `tournament_system` | **Versión Odoo:** 17.0

Este documento explica cómo funcionan las relaciones en el ORM de Odoo, cuándo elegir cada tipo, qué atributos controlan su comportamiento y qué genera cada una en la base de datos. Todos los ejemplos son código real del módulo `tournament_system`.

---

## Tabla de Contenidos

1. [Tipos de Relaciones](#1-tipos-de-relaciones)
   - [Many2one](#11-many2one--pertenezco-a-uno)
   - [One2many](#12-one2many--tengo-muchos)
   - [Many2many](#13-many2many--compartimos-la-relación)
   - [Related](#14-related--atajo-a-través-de-relaciones)
2. [Atributos Clave](#2-atributos-clave)
   - [ondelete](#21-ondelete)
   - [domain](#22-domain)
   - [context](#23-context)
3. [Impacto en la Base de Datos](#3-impacto-en-la-base-de-datos)
4. [Tabla de Decisión Rápida](#4-tabla-de-decisión-rápida)
5. [Errores Comunes](#5-errores-comunes)

---

## 1. Tipos de Relaciones

### 1.1 Many2one — "Pertenezco a uno"

Un `Many2one` indica que **este registro apunta a exactamente un registro de otro modelo**. Es la relación más frecuente en Odoo.

**Sintaxis:**
```python
field_name = fields.Many2one('other.model', string='Label')
```

**Cuándo usarlo:**
- Un score pertenece a un participante → usa `Many2one`
- Una categoría pertenece a un torneo → usa `Many2one`
- Un registro tiene un responsable/juez → usa `Many2one`
- La cardinalidad es **N:1** (muchos apuntan a uno)

**Ejemplo en el módulo:**

```python
# models/event_tournament_category.py
tournament_id = fields.Many2one('event.tournament', string='Tournament')
product_id = fields.Many2one('product.product', string='Product')

# models/event_tournament_score.py
participant_id = fields.Many2one('res.partner', string='Participant', required=True, ...)
judge_id = fields.Many2one('res.users', string='judge', default=lambda self: self.env.user, readonly=True)
```

**Lo que crea en la BD:**
> Una columna FK `tournament_id` (tipo `integer`) en la tabla `event_tournament_category`.

---

### 1.2 One2many — "Tengo muchos"

Un `One2many` es la **cara inversa** de un `Many2one`. No crea ninguna columna nueva; es una vista virtual que navega la FK del modelo hijo.

**Sintaxis:**
```python
field_name = fields.One2many('child.model', 'inverse_field_name', string='Label')
```

> El segundo argumento **siempre** debe ser el nombre del campo `Many2one` en el modelo hijo que apunta de vuelta al padre.

**Cuándo usarlo:**
- Cuando quieres acceder a todos los registros hijos desde el padre
- Para mostrar una lista inline en la vista form del padre (notebook/tab)
- La cardinalidad es **1:N** (uno tiene muchos)

**Ejemplo en el módulo:**

```python
# models/event_tournament.py
category_ids = fields.One2many(
    'event.tournament.category',  # modelo hijo
    'tournament_id',              # campo Many2one en el hijo que apunta aquí
    string='Categories'
)

# models/event_tournament_category.py
participant_ids = fields.One2many('res.partner', 'tournament_category_id', string='Participant')

# models/event_tournament_registration.py  (en res.partner)
score_ids = fields.One2many('event.tournament.score', 'participant_id', string='Scores')
```

**Lo que crea en la BD:**
> **Nada.** El `One2many` es una relación virtual. La información ya está en la columna FK del modelo hijo. Leer `category_ids` en un torneo es equivalente a `SELECT * FROM event_tournament_category WHERE tournament_id = X`.

**Regla de oro:** Por cada `One2many` debe existir un `Many2one` correspondiente en el modelo hijo. Sin esa FK, Odoo lanzará un error al instalar el módulo.

---

### 1.3 Many2many — "Compartimos la relación"

Un `Many2many` conecta registros donde **cada uno puede relacionarse con múltiples del otro lado**. La relación es simétrica y bidireccional.

**Sintaxis:**
```python
field_name = fields.Many2many(
    'other.model',
    'relation_table',   # opcional: nombre de la tabla intermedia
    'column1',          # opcional: nombre de la columna de este modelo
    'column2',          # opcional: nombre de la columna del otro modelo
    string='Label'
)
```

Si omites `relation_table`, Odoo genera automáticamente un nombre con el formato `model1_model2_rel`.

**Cuándo usarlo:**
- Un participante puede estar en múltiples torneos Y un torneo tiene múltiples participantes
- Tags, etiquetas, permisos compartidos
- La cardinalidad es **N:M**

**Caso especial: Many2many computado (sin tabla intermedia)**

En el módulo, `tournament_ids` en `res.partner` es un `Many2many` **computado**:

```python
# models/event_tournament_registration.py
tournament_ids = fields.Many2many(
    'event.tournament',
    string='Torneos Inscritos',
    compute='_compute_tournaments',  # <-- computado, no hay tabla
)

@api.depends('tournament_category_id', 'tournament_category_id.tournament_id')
def _compute_tournaments(self):
    for record in self:
        record.tournament_ids = record.tournament_category_id.tournament_id
```

Aquí la relación N:M es una **representación lógica** derivada del `Many2one` existente, no una tabla nueva. Se usa `Many2many` como tipo de retorno porque un partner podría —en una versión futura— tener varias categorías.

**Lo que crea en la BD:**
- `Many2many` normal → tabla intermedia (ej: `tournament_participant_rel`)
- `Many2many` computado sin `store=True` → **nada**, solo cálculo en memoria

---

### 1.4 Related — "Atajo a través de relaciones"

Un campo `related` **navega una cadena de relaciones** para exponer un valor de otro modelo directamente en el registro actual.

**Sintaxis:**
```python
field_name = fields.Many2one(
    'target.model',
    related='relation_field.next_field',
    store=True,   # opcional: materializar en BD
    index=True,   # opcional: indexar para búsquedas rápidas
    readonly=True
)
```

**Cuándo usarlo:**
- Para evitar JOINs repetitivos en vistas de lista y dominios de búsqueda
- Para mostrar información de un modelo relacionado sin recalcular
- Cuando el campo se usa frecuentemente en filtros o agrupaciones

**Ejemplo en el módulo — el caso más claro:**

```python
# models/event_tournament_score.py

# Sin related, para saber el torneo de un score necesitas:
# score → participant_id → tournament_category_id → tournament_id (3 JOINs)

tournament_category_id = fields.Many2one(
    "event.tournament.category",
    related="participant_id.tournament_category_id",
    store=True,   # guarda en la tabla del score
    index=True,   # permite búsquedas rápidas por categoría
    readonly=True,
)

tournament_id = fields.Many2one(
    "event.tournament",
    related="participant_id.tournament_category_id.tournament_id",
    store=True,   # guarda en la tabla del score
    index=True,
    readonly=True,
)
```

Con `store=True`, Odoo guarda los valores en la tabla `event_tournament_score` y los mantiene sincronizados automáticamente cuando cambia el campo origen. Esto convierte 3 JOINs en 0.

**Lo que crea en la BD:**
- Sin `store=True` → nada, se recalcula en cada lectura
- Con `store=True` → columna desnormalizada en la tabla actual (trade-off: espacio vs. velocidad)

---

## 2. Atributos Clave

### 2.1 `ondelete`

Define qué ocurre con el registro hijo cuando el registro padre (al que apunta el `Many2one`) es **eliminado**.

| Valor | Comportamiento | Cuándo usar |
|---|---|---|
| `'cascade'` | Borra el hijo automáticamente | El hijo no tiene sentido sin el padre (ej. líneas de pedido) |
| `'set null'` | Pone la FK a `NULL` | El hijo puede existir sin padre (campo opcional) |
| `'restrict'` | **Impide la eliminación** del padre si tiene hijos | Integridad estricta (ej. no puedes borrar un torneo con categorías) |

**Sintaxis:**
```python
tournament_id = fields.Many2one('event.tournament', ondelete='cascade')
```

**En el módulo** (comportamiento implícito, ya que `ondelete` no está declarado explícitamente):

```python
# event_tournament_category.py
tournament_id = fields.Many2one('event.tournament', string='Tournament')
# ondelete por defecto en Odoo es 'set null' para Many2one opcionales
# y 'restrict' cuando el campo es required=True
```

**Recomendación de diseño:**

```
¿El hijo tiene sentido sin el padre?
  No → ondelete='cascade'  (ej. score sin categoría)
  Sí → ondelete='set null' (ej. partner sin categoría)
  Necesitas auditoría → ondelete='restrict' (bloquea el borrado)
```

---

### 2.2 `domain`

Filtra qué registros están disponibles para selección en la interfaz de usuario. Puede ser **estático** (lista fija) o **dinámico** (referencia a otro campo del formulario).

**Sintaxis estática:**
```python
field = fields.Many2one('res.partner', domain=[('is_company', '=', True)])
```

**Sintaxis dinámica (referencia al registro actual):**
```python
field = fields.Many2one('res.partner', domain="[('tournament_category_id', '!=', False)]")
```

**Ejemplo real en el módulo:**

```python
# models/event_tournament_score.py
participant_id = fields.Many2one(
    'res.partner',
    string='Participant',
    required=True,
    domain="[('tournament_category_id', '!=', False)]"
    # Solo muestra partners que ya tienen una categoría asignada
    # Evita asignar scores a partners no registrados en ningún torneo
)
```

**Cuándo usar domain:**
- Para restringir opciones a registros válidos según el contexto del negocio
- Para mejorar la UX evitando que el usuario vea opciones inválidas
- Para evitar errores de validación antes de que el usuario guarde

> **Importante:** `domain` es solo una restricción de la UI. No impide que el ORM guarde valores fuera del dominio vía código Python. Para eso necesitas un `@api.constrains`.

---

### 2.3 `context`

Pasa un diccionario de contexto que afecta el comportamiento de vistas, acciones y valores por defecto cuando se abre un registro relacionado.

**Usos más comunes:**

| Clave | Efecto |
|---|---|
| `default_field_name` | Pre-rellena un campo en el formulario que se abre |
| `group_by` | Agrupa la lista por un campo al abrir la vista |
| `search_default_field` | Activa un filtro predefinido en la vista de búsqueda |
| `no_create` | Desactiva el botón "Crear" en el dropdown del Many2one |

**Ejemplo en vistas (tournament_system):**

```xml
<!-- views/event_tournament_score_views.xml -->
<field name="tournament_id" context="{'group_by': 'tournament_id'}"/>

<!-- Cuando se abre la lista de scores desde un torneo, pasa el ID como default -->
<field name="category_ids">
    <tree>
        <field name="participant_ids" 
               context="{'default_tournament_category_id': active_id}"/>
    </tree>
</field>
```

**Context en acciones de menú:**

```python
# Al hacer clic en "Panel de Juez", solo muestra scores del torneo activo
action = {
    'type': 'ir.actions.act_window',
    'res_model': 'event.tournament.score',
    'context': {
        'search_default_tournament_id': self.id,
        'default_tournament_id': self.id,
    }
}
```

---

## 3. Impacto en la Base de Datos

### Resumen visual

```
event.tournament
├── id              INTEGER  PK
├── name            VARCHAR
├── state           VARCHAR
├── start_date      DATE
├── end_date        DATE
└── company_id      INTEGER  FK → res_company.id      ← Many2one crea esta columna

event_tournament_category
├── id              INTEGER  PK
├── name            VARCHAR
├── age_min         INTEGER
├── age_max         INTEGER
├── price           INTEGER
├── tournament_id   INTEGER  FK → event_tournament.id ← Many2one crea esta columna
└── product_id      INTEGER  FK → product_product.id  ← Many2one crea esta columna
    (category_ids en event.tournament NO crea columna — es One2many virtual)

res_partner  (extendido por EventTournamentRegistration)
├── id                       INTEGER  PK
├── ... (campos nativos de Odoo)
├── tournament_category_id   INTEGER  FK → event_tournament_category.id ← Many2one
├── age                      INTEGER
    (score_ids: One2many virtual → no crea columna)
    (tournament_ids: Many2many computado sin store → no crea columna ni tabla)

event_tournament_score
├── id                       INTEGER  PK
├── score                    INTEGER
├── notes                    VARCHAR
├── participant_id           INTEGER  FK → res_partner.id              ← Many2one
├── judge_id                 INTEGER  FK → res_users.id                ← Many2one
├── tournament_category_id   INTEGER  FK → event_tournament_category.id ← related store=True
└── tournament_id            INTEGER  FK → event_tournament.id          ← related store=True
```

### 3.1 Columnas que se crean

| Tipo de campo | ¿Crea columna? | Tipo SQL |
|---|:---:|---|
| `Many2one` | Sí | `INTEGER` (FK) |
| `One2many` | No | — (virtual) |
| `Many2many` regular | No en el modelo | Tabla intermedia separada |
| `Many2many` computado | No | — (virtual) |
| `related` sin `store` | No | — (recalculado) |
| `related` con `store=True` | Sí | Mismo tipo que el campo origen |
| `compute` sin `store` | No | — (recalculado) |
| `compute` con `store=True` | Sí | Tipo del campo |

### 3.2 Tablas intermedias (Many2many)

Cuando declaras un `Many2many` estándar (no computado), Odoo genera automáticamente una tabla de relación:

```sql
-- Para un Many2many entre res.partner y event.tournament
CREATE TABLE event_tournament_res_partner_rel (
    event_tournament_id  INTEGER REFERENCES event_tournament(id),
    res_partner_id       INTEGER REFERENCES res_partner(id),
    PRIMARY KEY (event_tournament_id, res_partner_id)
);
```

Puedes controlar el nombre con el parámetro `relation`:
```python
tournament_ids = fields.Many2many(
    'event.tournament',
    relation='tournament_participant_rel',  # nombre explícito
    column1='partner_id',
    column2='tournament_id',
)
```

### 3.3 El trade-off de `store=True` en campos `related`

```
Sin store=True:
  Leer tournament_id en un score = 
    SELECT t.id FROM event_tournament t
    JOIN event_tournament_category c ON c.tournament_id = t.id
    JOIN res_partner p ON p.tournament_category_id = c.id
    WHERE p.id = score.participant_id
  → 2 JOINs extra por cada lectura

Con store=True:
  Leer tournament_id en un score = 
    SELECT tournament_id FROM event_tournament_score WHERE id = X
  → 0 JOINs extra

Costo:
  - Ocupa más espacio en disco (columna desnormalizada)
  - Odoo ejecuta un UPDATE al cambiar la categoría del participante
  - Vale la pena cuando el campo se usa en dominios, filtros o listas frecuentes
```

---

## 4. Tabla de Decisión Rápida

```
¿Cuántos registros del modelo B puede tener un registro de A?

  Solo uno → Many2one  (A tiene un campo FK hacia B)
  
  Muchos, y B pertenece exclusivamente a A → One2many  
    (requiere Many2one inverso en B)
  
  Muchos, y B puede relacionarse con otros A también → Many2many
    (Odoo crea tabla intermedia)
  
  Ya existe la relación pero quiero un "shortcut" → related
    (navega la cadena existente, opcionalmente store=True)
```

### Árbol de decisión detallado

```
¿Necesitas guardar una referencia a OTRO registro?
  │
  ├─ Sí, UNO solo
  │     └─► Many2one
  │             ¿El hijo muere con el padre?  → ondelete='cascade'
  │             ¿El hijo vive sin el padre?   → ondelete='set null'
  │             ¿No se debe borrar el padre?  → ondelete='restrict'
  │
  ├─ Sí, MUCHOS (y yo soy el dueño exclusivo)
  │     └─► One2many  (requiere Many2one en el hijo)
  │
  ├─ Sí, MUCHOS (relación compartida, bidireccional)
  │     └─► Many2many
  │             ¿Es derivado de otra relación?  → compute=, sin tabla
  │             ¿Es una relación propia?        → tabla intermedia automática
  │
  └─ No, quiero exponer un campo de un modelo relacionado
        └─► related='campo1.campo2'
                ¿Se filtra/busca frecuentemente?  → store=True, index=True
                ¿Solo para mostrar en UI?          → sin store (valor en memoria)
```

---

## 5. Errores Comunes

### Error 1: One2many sin su Many2one inverso

```python
# MAL: participant_ids apunta a 'tournament_category_id' pero ese campo no existe en res.partner
participant_ids = fields.One2many('res.partner', 'tournament_category_id')

# BIEN: el campo 'tournament_category_id' existe en res.partner
# (definido en event_tournament_registration.py)
tournament_category_id = fields.Many2one('event.tournament.category')
```

**Error que verás:** `ValueError: Field res.partner.tournament_category_id does not exist`

---

### Error 2: Many2many con nombre de tabla duplicado

Si dos modelos distintos tienen una relación Many2many entre los mismos pares de modelos sin especificar `relation`, Odoo puede reutilizar la misma tabla intermedia o lanzar un error de unicidad.

```python
# MAL: tabla se llama igual que otra relación existente
partner_ids = fields.Many2many('res.partner')

# BIEN: nombre explícito y único
partner_ids = fields.Many2many(
    'res.partner',
    relation='my_module_partner_rel',
    column1='source_id',
    column2='partner_id',
)
```

---

### Error 3: related sin `readonly=True` en campos computados

Los campos `related` con `store=False` son de solo lectura porque Odoo no sabe cómo propagar escrituras a través de la cadena de relaciones.

```python
# MAL: sin readonly, Odoo puede intentar escribir en este campo y fallar
tournament_id = fields.Many2one("event.tournament", related="participant_id.tournament_category_id.tournament_id")

# BIEN: siempre declarar readonly en campos related
tournament_id = fields.Many2one(
    "event.tournament",
    related="participant_id.tournament_category_id.tournament_id",
    store=True,
    readonly=True,
)
```

---

### Error 4: domain en UI vs. constraint en ORM

```python
# domain solo filtra la UI, no el ORM:
participant_id = fields.Many2one('res.partner', domain="[('tournament_category_id', '!=', False)]")

# Si alguien llama create() por código sin ese filtro, el valor se guardará igual.
# Para validación real, necesitas @api.constrains:
@api.constrains('participant_id')
def _check_participant_has_category(self):
    for record in self:
        if not record.participant_id.tournament_category_id:
            raise ValidationError("El participante debe tener una categoría asignada.")
```

---

> **Recursos de referencia:**
> - [Odoo ORM Fields Reference](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#fields)
> - [PostgreSQL FK Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK)
