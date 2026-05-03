from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventTournamentRegistration(models.Model):
    _inherit='res.partner'
    _description='This model is the assigned for manage the diferent rules of users'

    tournament_category_id = fields.Many2one('event.tournament.category', string='Participant')
    age = fields.Integer(string='Age', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            category_id = val.get("tournament_category_id")
            age = val.get("age", 0)
            if category_id:
                category = self.env['event.tournament.category'].browse(category_id)
                if category.exists() and not (age >= category.age_min and age <= category.age_max):
                    raise UserError(_("You cannot join this category by your age. you have to between %s to %s ages",
                                      category.age_min, category.age_max))
        return super().create(vals_list)
