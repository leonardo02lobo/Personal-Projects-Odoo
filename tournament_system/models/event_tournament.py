from odoo import fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class EventTournament(models.Model):
    _name='event.tournament'
    _inherit=['mail.thread', 'mail.activity.mixin']
    _description='This model is for manager the tournament of event'
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', readonly=True, tracking=True)

    name = fields.Char(string="Name Tournament")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    category_ids = fields.One2many('event.tournament.category','tournament_id', string='Category')
    company_id = fields.Many2one(
        'res.company', 
        string="Company", 
        required=True, 
        default= lambda self: self.env.company
    )

    def _calculate_podium(self):
        scores = self.category_ids.participant_ids.score_ids
        _logger.info(f"Total Scores: {scores}")
        for score in scores:
            _logger.info(f"Score: {score}")

    def action_confirm(self):
        self.ensure_one()
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only tournaments in Draft can be confirmed.'))

            if not record.category_ids:
                raise UserError(_('You cannot confirm a tournament without at least one category.'))

            for categories in record.category_ids:
                if not categories.participant_ids:
                    raise UserError(_("Not cannot confirm the tournament that not has participants"))

            record.write({'state': 'confirm'})

    def action_in_progress(self):
        self.ensure_one()
        vals_list = []

        for record in self:
            if record.state != 'confirm':
                raise UserError(_("You can only finish tournaments that are In Progress."))

            for category in record.category_ids:
                if not category.participant_ids:
                    raise UserError(_("The category %s has no participants.") % category.display_name)
            
        for participant in self.category_ids.participant_ids:
            vals_list.append({
                'participant_id': participant.id,
                'score': 0.0,
                'judge_id': self.env.user.id,
                'notes': ''
            })
        
        self.env['event.tournament.score'].create(vals_list)

        record.write({'state': 'in_progress'})
        record.message_post(body=_("The tournament finish, Scoring..."))

    def action_done(self):
        self.ensure_one()
        participants = self.category_ids.mapped('participant_ids')
        
        participants_exist = self.env['event.tournament.score'].search([
            ('participant_id', 'in', participants.ids)
        ]).mapped('participant_id')

        for participant in participants_exist:
            _logger.info(f"Participant: {participant}")
