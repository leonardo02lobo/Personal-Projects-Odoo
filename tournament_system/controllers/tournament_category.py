import json
from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)

class TournamentCategory(http.Controller):
    _model='event.tournament.category'
    _url_base='/api/categories'

    @http.route(_url_base, methods=['GET'], auth='public', type='http')
    def get_categories(self, **kwargs):
        data = request.env[self._model].get_all_category()
        return request.make_json_response(data)

    @http.route(f'{_url_base}/<int:id>', methods=['GET'], auth='public', type='http')
    def get_categories_by_id(self, id, **kwargs):
        data = request.env[self._model].get_category_by_id(id)
        return request.make_json_response(data)

    @http.route(f'{_url_base}/participants/<int:category_id>', methods=['GET'], auth='public', type='http')
    def get_category_with_participants(self, category_id, **kwargs):
        category = request.env[self._model].get_category_by_id(id=category_id)
        for cat in category['category']:
            participants = request.env['res.partner'].get_partner_by_ids(cat['participant_ids'])
            cat['participants'] = participants['partners']

        return request.make_json_response(category)

    @http.route(f'{_url_base}/participants/score/<int:category_id>', methods=['GET'], auth='public', type='http')
    def get_category_with_score(self, category_id, **kwargs):
        category = request.env[self._model].get_category_by_id(id=category_id)
        participants = self.get_category_with_participants(category_id=category_id)
        data = json.loads(participants.data)
        for category in data.get('category', []):
            for participant in category.get('participants', []):
                scores = request.env['event.tournament.score'].get_score_by_ids(participant.get('score_ids', []))
                participant['scores'] = scores['scores']
        return request.make_json_response(category)
                
