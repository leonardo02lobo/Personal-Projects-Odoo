import json
from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)

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
        data = request.env[self._model].sudo().get_tournament_by_company(id)
        return request.make_json_response(data)
    
    @http.route(f'{_base_url}/category', methods=['GET'], auth='public', type='http')
    def get_tournament_with_category(self, **kwargs):
        tournaments = request.env[self._model].sudo().get_all_tournaments()
        for tournament in tournaments['tournaments']:
            categories = request.env[f"{self._model}.category"].get_category_by_ids(tournament['category_ids'])
            tournaments['category'] = categories['category']
        return request.make_json_response(tournaments)

    @http.route(f'{_base_url}/category/<int:id>', methods=['GET'], auth='public', type='http')
    def get_tournament_by_category(self, id, **kwargs):
        tournaments = request.env[self._model].sudo().get_tournament_by_id(id)
        for tournament in tournaments['tournaments']:
            categories = request.env[f"{self._model}.category"].get_category_by_ids(tournament['category_ids'])
            tournaments['category'] = categories['category']
        return request.make_json_response(tournaments)

    @http.route(f'{_base_url}/category/participants', methods=['GET'], auth='public', type='http')
    def get_tournament_with_participants(self, **kwargs):
        tournaments = self.get_tournament_with_category()
        data = json.loads(tournaments.data)
        for participants in data['category']:
            participants_data = request.env['res.partner'].sudo().get_partner_by_ids(participants['participant_ids'])
            participants['participants'] = participants_data['partners']
        return request.make_json_response(data)
