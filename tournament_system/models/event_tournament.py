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
            if record.state != 'draft':
                raise UserError(_('Only tournaments in Draft can be confirmed.'))

            if not record.category_ids:
                raise UserError(_('You cannot confirm a tournament without at least one category.'))

            record.write({'state': 'confirm'})

    def action_done(self):
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_("You can only finish tournaments that are In Progress."))

            for category in record.category_ids:
                if not category.participant_ids:
                    raise UserError(_("The category %s has no participants.") % category.display_name)

            # Agregar el modelo para calcular el porcentaje
            # here

            record.write({'state': 'done'})

            record.message_post(body=_("The tournament finished successfully. Results are ready."))
    
    def _calculate_podium(self):
        for category in self.category_ids:
            pass
