from odoo import fields, models, _
from odoo.exceptions import UserError


class EventTournament(models.Model):
    _name='event.tournament'
    _inherit=['mail.thread', 'mail.activity.mixin']
    _description='This model is for manager the tournament of event'
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', readonly=True, tracking=True)

    name = fields.Char(string="Name Tournament")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    category_ids = fields.One2many('event.tournament.category','tournament_id', string='Category')
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        required=True, 
        default= lambda self: self.env.company
    )

    def action_confirm(self):
        for record in self:
            if record.state != 'Confirmed':
                raise UserError(_('Only You can Confirmed tournament in Draft'))
            
            if not record.category_ids:
                raise UserError(_('You cannot confirm a tournament wirhout least one category'))

    def action_done(self):
        for record in self:
            if record.state != 'In Progress':
                raise UserError(_("You cannot Done tournament that this 'In Progress'"))
            
            for category in record.category_ids:
                if not category.participant_ids:
                    raise UserError(_("The category %s not has participant", category.name))
                

            # Agregar el modelo para calcular el porcentaje
            # here

            record.write({'state': 'Done'})

            record.message_post(body=_("The tournament finished success. Result"))
    
    def _calculate_podium(self):
        for category in self.category_ids:
            #Here used Sorted and filter by points
            pass
