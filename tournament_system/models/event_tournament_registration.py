from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventTournamentRegistration(models.Model):
    _inherit='res.partner'
    _description='This model is the assigned for manage the diferent rules of users'

    tournament_category_id = fields.Many2one('event.tournament.category', string='Participant')
    age = fields.Integer(string='Age', store=True)
    score_ids = fields.One2many(
        'event.tournament.score',
        'participant_id',
        string='Scores',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_tournament_category_age()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._check_tournament_category_age()
        return res

    def _check_tournament_category_age(self):
        for participant in self:
            category = participant.tournament_category_id
            if not category:
                continue

            if not (category.age_min <= participant.age <= category.age_max):
                raise UserError(_(
                    "You cannot join this category by your age. You have to be between %s and %s years old."
                ) % (category.age_min, category.age_max))
