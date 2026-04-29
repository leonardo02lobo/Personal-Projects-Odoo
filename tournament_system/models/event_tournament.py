from odoo import fields, models, _
from odoo.exceptions import UseError


class EventTournament(models.Model):
    _name='event.tournament'
    _inherit=['mail.thread', 'mail.activity.mixin']
    _description='This model is for manager the tournament of event'
    _order='ASC'
    
    state = fields.Selection([
        ('Draft', 'Borrador'),
        ('Confirm', 'Confirmado'),
        ('In_Progress', 'En Progreso')
        ('Done', 'Realizado'),
        ('Cancel', 'Cancelado'),
    ], default='Draft', readonly=True, tracking=True)

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    category_ids = fields.One2many('event.tournament.category','tournament_id', string='Category')
    
    def action_confirm(self):
        for record in self:
            if record.state != 'Confirm':
                raise UseError(_('Only You can Confirm tournament in Draft'))
            
            if not record.category_ids:
                raise UseError(_('You cannot confirm a tournament wirhout least one category'))

    def action_done(self):
        for record in self:
            if record.state != 'In_Progress':
                raise UseError(_("You cannot Done tournament that this 'In Progress'"))
            
            for category in record.category_ids:
                if not category.participant_ids:
                    raise UseError(_("The category %s not has participant", category.name))
                

            # Agregar el modelo para calcular el porcentaje
            # here

            record.write({'state': 'Done'})

            record.message_post(body=_("The tournament finished success. Result"))
    
    def _calculate_podium(self):
        for category in self.category_ids:
            #Here used Sorted and filter by points
            pass
