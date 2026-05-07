from odoo import http
from odoo.http import request


class TournamentRegistration(http.Controller):
    _model='res.partner'
    _base_url='/api/registration'

    @http.route(_base_url, methods=['GET'], auth='public', type='http')
    def get_res_partner(self, **kwargs):
        return request.make_json_response(self.get_all())
    
    @http.route(f'{_base_url}/<int:id>', methods=['GET'], auth='public', type='http')
    def get_res_partner_by_id(self, id, **Kwargs):
        return request.make_json_response(self.get_data_by_id(id=id))

