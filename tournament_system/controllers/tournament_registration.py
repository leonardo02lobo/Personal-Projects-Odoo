from odoo import http
from odoo.http import request
import logging 

_logger = logging.getLogger(__name__)


class TournamentRegistration(http.Controller):
    _model='res.partner'
    _base_url='/api/registration'

    @http.route(_base_url, methods=['GET'], auth='public', type='http')
    def get_res_partner(self, **kwargs):
        data = request.env[self._model].get_all_partner()
        return request.make_json_response(data)
    
    @http.route(f'{_base_url}/<int:id>', methods=['GET'], auth='public', type='http')
    def get_res_partner_by_id(self, id, **Kwargs):
        data = request.env[self._model].get_partner_by_id(id)
        return request.make_json_response(data)

    @http.route(f'{_base_url}/scores', methods=['GET'], auth='public', type='http')
    def get_partner_with_scores(self, **kwargs):
        partners = request.env[self._model].get_all_partner()
        for partner in partners.get('partners', []):
            _logger.info(f"Partner: {partner}")
            scores = request.env['event.tournament.score'].get_score_by_ids(partner['score_ids'])
            partner['scores'] = scores
        return request.make_json_response(partners)
