from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TournamentCanceldWizard(models.TransientModel):
    _name = 'tournament.canceld.wizard'
    _description = 'This wizard be use for question if you want canceld'

    tournament_id = fields.Many2one('event.tournament', string="Tournament", readonly=True)
    reason = fields.Char(string="Notes", required=True)

    def action_confirm_cancel(self):
        self.ensure_one()
        if not self.tournament_id:
            raise UserError(_("No tournament linked to this wizard."))
        self.tournament_id.action_cancel(reason=self.reason)
        return {'type': 'ir.actions.act_window_close'}