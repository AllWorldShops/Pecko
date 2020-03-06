from odoo import models, fields, api,_
from odoo.http import request


class AccountAgedReport(models.TransientModel):
    _name = "account.aged.report"
 
    report_account_id = fields.Many2one('account.account',string='Account',domain=[('user_type_id', '=', 2)])
 
    @api.multi
    def report_aged_payable(self):
        request.session['payable_account'] = self.report_account_id.id
        request.session['receivable_account'] = ''
        print (request.session['payable_account'])
        context = {
            'model': 'account.aged.payable',
            'payable_account': self.report_account_id.id,
            'context': {'payable_account': self.report_account_id.id,}
            }
        return {
            'type': 'ir.actions.client',
            'name': 'Aged Payable',
            'tag': 'account_report',
            'context': context
            }



