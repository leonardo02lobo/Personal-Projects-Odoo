from odoo import fields, models, _
from odoo.exceptions import UserError
from markupsafe import Markup

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
        message_html = ""
        for category in self.category_ids:
            cat_name = category.name or ''
            message_html += Markup(_("<b>Category: %s</b><br/>") % (cat_name))
            scores = self.env['event.tournament.score'].search([
                ('tournament_category_id', '=', category.id)
            ], order='score desc')
            if not scores:
                message_html += Markup(_("&nbsp;&nbsp;- No scores available<br/>"))
                continue
            ind = 1
            for sc in scores:
                pname = Markup(sc.participant_id.name or '')
                pnotes = Markup(sc.notes or '')
                message_html += Markup(_("[%s]. Name: %s -- Points: %s -- Notes: %s<br/>") % (
                    ind, pname, sc.score, pnotes
                ))
                ind += 1
            message_html += Markup(_("<br/>"))
        if message_html:
            self.message_post(body=message_html)


    def write(self, vals):
        if 'state' not in vals:
            cancelled = self.filtered(lambda t: t.state == 'cancel')
            if cancelled:
                raise UserError(_("You cannot edit a cancelled tournament."))
        return super().write(vals)

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
        
        self.write({'state': 'done'})
        self.message_post(body=_("The tournament finish"))
        self._calculate_podium()

    def action_open_cancel_wizard(self):
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("You cannot cancel a tournament that is already done."))
        if self.state == 'cancel':
            raise UserError(_("This tournament is already cancelled."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Tournament'),
            'res_model': 'tournament.canceld.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tournament_id': self.id,
            },
        }

    def action_cancel(self, reason=''):
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_("Tournament cancelled. Reason: %s") % (reason or _('No reason provided')))

    def action_report_pdf(self):
        self.ensure_one()

    def get_all_tournaments(self):
        tournaments = self.search_read([])
        return {
            'status': 200,
            'tournaments': tournaments
        }

    def get_tournament_by_id(self, id=None):
        if id is None:
            return {
                'status': 404,
                'message': _('Not exist tournament by id')
            }
        tournament = self.search_read([('id', '=', id)])
        return {
            'status': 200,
            'tournaments': tournament
        }

    def get_tournament_by_company(self, id=None):
        tournament = self.get_tournament_by_id(id=id)
        if not tournament:
            return {
                'status': 404,
                'message': _('Not exist tournament by id')
            }
        for tour in tournament['tournaments']:
            company = self.env['res.partner'].get_partner_by_id(tour['company_id'][0])
            tour['company'] = company['partner']
        return tournament
