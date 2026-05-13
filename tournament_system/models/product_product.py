from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    tournament_category_ids = fields.One2many(
        'event.tournament.category',
        'product_id',
        string='Tournament Categories',
    )
    tournament_category_name = fields.Char(
        string='Tournament Category',
        compute='_compute_tournament_category_name',
    )

    def _compute_tournament_category_name(self):
        for product in self:
            category = product.tournament_category_ids[:1]
            product.tournament_category_name = category.name or 'No category'