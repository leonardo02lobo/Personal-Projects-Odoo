from odoo import http
from odoo.http import request
from . import base_controller


class TournamentController(base_controller.APIController,http.Controller):
    _model='event.tournament'
    _base_url='/api/tournaments'

    @http.route(_base_url, methods=['GET'], auth='public', type='http')
    def get_tournaments(self, **kwargs):
        return request.make_json_response(self.get_all())

    @http.route(f'{_base_url}/<int:id>', methods=['GET'], auth='public', type='http')
    def get_tournament_by_id(self, id, **kwargs):
        tournament = request.env[self._model].search_read([('id', '=', id)])
        return request.make_json_response(tournament)

    @http.route(f'{_base_url}/company/<int:company_id>', methods=['GET'], auth='public', type='http')
    def get_tournament_by_company(self, company_id, **kwargs):
        tournament = request.env[self._model].search_read([('company_id', '=', company_id)])
        return request.make_json_response(tournament)
    
    @http.route(f'{_base_url}/category', methods=['GET'], auth='public', type='http')
    def get_tournament_with_category(self, **kwargs):
        tournaments = self.get_all()
        for tournament in tournaments:
            categories = request.env['event.tournament.category'].search_read([
                ('id', 'in', tournament['category_ids'])
            ])
            tournament['categories'] = categories
        return request.make_json_response(tournaments)