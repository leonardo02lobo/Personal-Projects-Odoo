from odoo import http
from odoo.http import request


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

