from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EventTournamentScore(models.Model):
    _name='event.tournament.score'
    _description='This model is for the points of the user registrate by tournament'

    participant_id = fields.Many2one('res.partner', string='Participant', required=True, domain="[('tournament_category_id', '!=', False)]")
    judge_id = fields.Many2one('res.users', string="judge", default=lambda self: self.env.user, readonly=True)

    tournament_category_id = fields.Many2one(
        "event.tournament.category",
        related="participant_id.tournament_category_id",
        string="Category",
        store=True,
        index=True,
        readonly=True,
    )

    tournament_id = fields.Many2one(
        "event.tournament",
        related="participant_id.tournament_category_id.tournament_id",
        string="Tournament",
        store=True,
        index=True,
        readonly=True,
    )

    score = fields.Integer(string='Points', required=True)
    notes = fields.Char(string='Description')

    @api.constrains('score')
    def _check_score(self):
        for record in self:
            if record.score < 0:
                raise ValidationError(_("The point has that be more a zero"))
            if record.score > 100:  
                raise ValidationError(_("The point has that be less than 100"))

    def get_all_scores(self):
        scores = self.search_read([])
        return {
            'status': 200,
            'scores': scores
        }

    def get_score_by_id(self, id=None):
        if id is None:
            return {
                'status': 404,
                'message': _('Not exist tournament by id')
            }
        score = self.search_read([('id', '=', id)])
        return {
            'status': 200,
            'score': score
        }

    def get_score_by_ids(self, ids=None):
        if ids is None:
            return {
                'status': 404,
                'message': _('Not exist tournament by id')
            }
        scores = self.search_read([('id', 'in', ids)])
        return {
            'status': 200,
            'scores': scores
        }
