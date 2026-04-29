from odoo import api, fields, models, _
from odoo.exceptions import UseError


class EventTournamentRegistration(models.Model):
    _name='event.tournament.registration'
    _inherit='res.partner'
    _description='This model is the assigned for manage the diferent rules of users'

    participant_id = fields.Many2one('event.tournament.category', string=f'Participant')
    age = fields.Integer(string='Age', store=True)