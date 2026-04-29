from odoo import api, fields, models, _
from odoo.exceptions import UseError

class EventTournamentCategory(models.Model):
    _name='event.tournament.category'
    _description='This model create the category of the tournament'

    tournament_id = fields.Many2one('event.tournament', string='Tournament')
    participant_ids = fields.One2many('event.tournament.registration', 'participant_id', string='Participant')

    @api.constraint('participant_ids')
    def asssigned_category(self):
        for record in self.participant_ids:
            pass