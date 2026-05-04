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

    def _check_category_range(self, categories, val_age_min):
        for category in categories:
            if category.age_max >= val_age_min:
                return False
        return True

    def write(self, vals):
        res = super().write(vals)

        if 'age_min' in vals or 'age_max' in vals:
            for category in self:
                for participant in category.participant_ids:
                    if not (category.age_min <= participant.age <= category.age_max):
                        raise UserError(_(
                            "Participant %s no longer fits in this category age range."
                        ) % participant.display_name)

        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            tournament_id = vals.get("tournament_id")
            age_min = vals.get("age_min", 0)

            if not tournament_id:
                raise UserError(_("Tournament is required."))
            if not age_min:
                raise UserError(_("Minimum age is required."))

            categories_exist = self.search([("tournament_id", "=", tournament_id)])
            if not self._check_category_range(categories_exist, age_min):
                raise UserError(_(
                    "Invalid age range: the minimum age must be greater than "
                    "the maximum age of all existing categories."
                ))
        return super().create(vals_list)
