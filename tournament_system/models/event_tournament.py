from audioop import reverse
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
        scores_3_top = self.category_ids.participant_ids.score_ids.sorted('score', reverse=True)[:3]
        # scores = self.category_ids.participant_ids.score_ids
        # _logger.info(f"Top 3: {scores}")

        # scores_3_top = scores.search([
        #     ('tournament_id', 'in', )
        # ])
        message = ""
        ind = 1
        for score in scores_3_top:
            message += _("[%s]. %s - Points: %s -- Notes: %s\n") % (
                ind,score.participant_id.name, score.score,score.notes or ""
            )
            ind+=1
        self.message_post(body=message)


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

        self.write({'state': 'in_progress'})
        self.message_post(body=_("The tournament finish, Scoring..."))

    def action_done(self):
        self.ensure_one()
        participants = self.category_ids.mapped('participant_ids')
        
        participants_exist = self.env['event.tournament.score'].search([
            ('participant_id', 'in', participants.ids)
        ])

        for participant in participants_exist:
            if not (participant.score > 0 and participant.notes != ''):
                raise UserError(_("You cannot finisih a tournament. missing data..."))
        
        #self.write({'state': 'done'})
        self.message_post(body=_("The tournament finish"))
        self._calculate_podium()
