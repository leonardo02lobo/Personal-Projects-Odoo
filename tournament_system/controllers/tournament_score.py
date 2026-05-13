from odoo import http
from odoo.http import request


class TournamentScore(http.Controller):
    _model = 'event.tournament.score'
    _base_url = '/api/score'

    @http.route(_base_url, methods=['GET'], auth='public', type='http')
    def get_scores(self, **kwargs):
        return request.make_json_response(self.get_all())