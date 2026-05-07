from odoo import http
from odoo.http import request


class TournamentController(http.Controller):
    _model='event.tournament'
    _base_url='/api/tournaments'

    @http.route(_base_url, methods=['GET'], auth='public', type='http')
    def get_tournaments(self, **kwargs):
        data = request.env[self._model].sudo().get_all_tournaments()
        return request.make_json_response(data)

    @http.route(f'{_base_url}/<int:id>', methods=['GET'], auth='public', type='http')
    def get_tournament_by_id(self, id, **kwargs):
        tournament = request.env[self._model].sudo().get_tournament_by_id(id)
        return request.make_json_response(tournament)

    @http.route(f'{_base_url}/company/<int:id>', methods=['GET'], auth='public', type='http')
    def get_tournament_by_company(self, id, **kwargs):
        data = request.env['event.tournament'].sudo().get_tournament_by_company(id)
        return request.make_json_response(data)
    
    @http.route(f'{_base_url}/category', methods=['GET'], auth='public', type='http')
    def get_tournament_with_category(self, **kwargs):
        tournaments = self.get_all()
        return request.make_json_response(tournaments)