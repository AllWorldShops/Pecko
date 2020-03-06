from odoo import api, exceptions, fields, models, _
 
#    Inherited AccountInvoice
class AccountInvoice(models.Model):
    _inherit = "account.invoice"
 
    currency_rate = fields.Float(string="Exchange Rate", readonly=True, copy=False,digits=(12,3), track_visibility='always')
    currency_update_flag = fields.Boolean(string="Currency Update Flag", default=False)
    
    @api.multi
    def action_currency_rate_update(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({'act_id':self.id})
        return {
            'name': _('Currency Updater'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'currency.rate.update',
            'context': context,
            'target': 'new'
        }

    @api.onchange('currency_id')
    def onchange_currency_update_flag(self):
        if self.currency_id.currency_update_invoice == True:
            self.currency_update_flag = True
        else:
            self.currency_update_flag = False

class account_payment(models.Model):
    _inherit = "account.payment"
 
    currency_rate = fields.Float(string="Currency Rate", copy=False,digits=(12,3))
    currency_update_flag = fields.Boolean(string="Currency Update Flag",compute="compute_currency_update_flag", default=False)
    
    def compute_currency_update_flag(self):
        for order in self:
            if order.currency_id.currency_update_invoice == True:
                order.currency_update_flag = True
            else:
                order.currency_update_flag = False

    @api.multi
    def action_currency_rate_update(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({'act_id':self.id})
        return {
            'name': _('Currency Updater'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payment.currency.rate.update',
            'context': context,
            'target': 'new'
        }

    @api.onchange('currency_id')
    def onchange_currency_update_flag(self):
        if self.currency_id.currency_update_invoice == True:
            self.currency_update_flag = True
        else:
            self.currency_update_flag = False

    def action_validate_invoice_payment(self):
        """ Posts a payment used to pay an invoice. This function only posts the
        payment by default but can be overridden to apply specific post or pre-processing.
        It is called by the "validate" button of the popup window
        triggered on invoice form by the "Register Payment" button.
        """
        if any(len(record.invoice_ids) != 1 for record in self):
            # For multiple invoices, there is account.register.payments wizard
            raise UserError(_("This method should only be called to process a single invoice's payment."))
        if self.payment_date:
            payment_date = self.payment_date
        else:
            payment_date = datetime.now().strftime('%Y-%m-%d')
        if self.currency_rate > 0.00:
            inverse_val = 1 / self.currency_rate
            currency_id = self.env['res.currency.rate'].create({
                'rate': inverse_val,
                'currency_id': self.currency_id.id,
                'name': payment_date,
            })
            
        return self.post()

class Currency(models.Model):
    _inherit = "res.currency"
 
    currency_update_invoice = fields.Boolean(string="Currency Update In Invoice")
    rounding = fields.Float(string='Rounding Factor', digits=(12, 10), default=0.01)
    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(12, 10),
                        help='The rate of the currency to the currency of rate 1.')

    # def _get_rates(self, company, date):
    #     query = """SELECT c.id,
    #                       COALESCE((SELECT r.rate FROM res_currency_rate r
    #                               WHERE r.currency_id = c.id AND r.name <= %s
    #                                 AND (r.company_id IS NULL OR r.company_id = %s)
    #                            ORDER BY r.company_id, r.name, r.id DESC
    #                               LIMIT 1), 1.0) AS rate
    #                FROM res_currency c
    #                WHERE c.id IN %s"""
    #     self._cr.execute(query, (date, company.id, tuple(self.ids)))
    #     currency_rates = dict(self._cr.fetchall())
    #     return currency_rates

class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"
    _description = "Currency Rate"

    rate = fields.Float(digits=(12, 10), help='The rate of the currency to the currency of rate 1')