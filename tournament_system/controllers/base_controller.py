from odoo.http import request


class APIController:
    _model = None
    _base_url = None

    def get_all(self):
        return request.env[self._model].search_read([])

    def get_data_by_id(self, id):
        return request.env[self._model].search_read([('id', '=', id)])

