from odoo import models, fields, api,_
from odoo.http import request


class AccountAgedReport(models.TransientModel):
    _name = "account.aged.receivable.report"
 
    report_receivable_account_id = fields.Many2one('account.account',string='Account',domain=[('user_type_id', '=', 1)])
 
    @api.multi
    def report_aged_receivable(self):
        request.session['receivable_account'] = self.report_receivable_account_id.id
        request.session['payable_account'] = ''
        print (request.session['receivable_account'])
        context = {
            'model': 'account.aged.receivable',
            'receivable_account': self.report_receivable_account_id.id,
            'context': {'receivable_account': self.report_receivable_account_id.id,}
            }
        return {
            'type': 'ir.actions.client',
            'name': 'Aged Receivable',
            'tag': 'account_report',
            'context': context
            }



