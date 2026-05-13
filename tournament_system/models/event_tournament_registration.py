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

    tournament_ids = fields.Many2many(
        'event.tournament',
        string='Torneos Inscritos',
        compute='_compute_tournaments',
    )

    tournament_count = fields.Integer(
        string='Cantidad de Torneos', 
        compute='_compute_tournament_count',
    )

    @api.depends('tournament_category_id', 'tournament_category_id.tournament_id')
    def _compute_tournament_count(self):
        for record in self:
            record.tournament_count = len(record.tournament_ids)
    
    @api.depends('tournament_category_id', 'tournament_category_id.tournament_id')
    def _compute_tournaments(self):
        for record in self:
            record.tournament_ids = record.tournament_category_id.tournament_id

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

    def get_all_partner(self):
        partners = self.search_read(
            fields=['id','age','score_ids', 'tournament_ids', 'tournament_count','name']
        )
        return {
            'status': 200,
            'partners': partners
        }
    def get_partner_by_id(self,id=id):
        if id is None:
            return {
                'status': 404,
                'message': _('Not exist tournament by id')
            }
        partner = self.search_read(
                domain=[('id', '=', id)],
                fields=['id','age','score_ids', 'tournament_ids', 'tournament_count','name']
            )
        return{
            'status': 200,
            'partner': partner
        }

    def get_partner_by_ids(self,id=id):
        if id is None:
            return {
                'status': 404,
                'message': _('Not exist tournament by id')
            }
        partners = self.search_read(
                domain=[('id', 'in', id)],
                fields=['id','age','score_ids', 'tournament_ids', 'tournament_count','name']
            )
        return{
            'status': 200,
            'partners': partners
        }
