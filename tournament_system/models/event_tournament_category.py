from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventTournamentCategory(models.Model):
    _name='event.tournament.category'
    _description='This model create the category of the tournament'

    name = fields.Char(string='Name of Category', required=True)
    tournament_id = fields.Many2one('event.tournament', string='Tournament')
    participant_ids = fields.One2many('res.partner', 'tournament_category_id', string='Participant')
    age_min = fields.Integer(string='Minimum Age', required=True)
    age_max = fields.Integer(string='Maximum Age', required=True)

    @api.constrains('age_min', 'age_max')
    def _check_age_range(self):
        for record in self:
            if record.age_min < 0 or record.age_max < 0:
                raise UserError(_("Age values cannot be negative."))
            if record.age_min >= record.age_max:
                raise UserError(_("Minimum age must be less than maximum age."))
            

