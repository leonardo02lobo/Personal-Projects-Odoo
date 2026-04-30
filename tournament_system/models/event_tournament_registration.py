from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventTournamentRegistration(models.Model):
    _inherit='res.partner'
    _description='This model is the assigned for manage the diferent rules of users'

    participant_id = fields.Many2one('event.tournament.category', string='Participant')
    age = fields.Integer(string='Age', store=True)