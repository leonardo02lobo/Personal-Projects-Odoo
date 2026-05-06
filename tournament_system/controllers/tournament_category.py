from odoo import http
from odoo.http import request
from . import base_controller

class TournamentCategory(base_controller.APIController,http.Controller):
    _model='event.tournament.category'
    _url_base='/api/categories'

    @http.route(_url_base, methods=['GET'], auth='public', type='http')
    def get_categories(self, **kwargs):
        return request.make_json_response(self.get_all())

    @http.route(f'{_url_base}/<int:id>', methods=['GET'], auth='public', type='http')
    def get_categories_by_id(self, id, **kwargs):
        return request.make_json_response(self.get_data_by_id(id=id))

    @http.route(f'{_url_base}/participants/<int:category_id>', methods=['GET'], auth='public', type='http')
    def get_category_with_participants(self, category_id, **kwargs):
        category = self.get_data_by_id(id=category_id)
        for cat in category:
            participants = request.env['res.partner'].search_read(
                domain=[('id', 'in', cat['participant_ids'])],
                fields=['id','age','score_ids', 'tournament_ids', 'tournament_count','name']
            )
            cat['participants'] = participants

        return request.make_json_response(category)

    @http.route(f'{_url_base}/participants/score/<int:category_id>', methods=['GET'], auth='public', type='http')
    def get_category_with_score(self, category_id, **kwargs):
        category = self.get_data_by_id(id=category_id)
        for cat in category:
            participants = request.env['res.partner'].search_read(
                domain=[('id', 'in', cat['participant_ids'])],
                fields=['id','age','score_ids', 'tournament_ids', 'tournament_count','name']
            )
            cat['participants'] = participants
            for participant in participants:
                scores = request.env['event.tournament.score'].search_read([
                    ('id', 'in', participant['score_ids'])
                ])
                participant['scores'] = scores
        
        return request.make_json_response(category)
                
