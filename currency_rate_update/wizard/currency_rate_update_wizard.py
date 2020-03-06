# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import date
from datetime import datetime


#  Created Currency rate update
class CurrencyRateUpdate(models.TransientModel):
    _name = 'currency.rate.update'
    _description = 'Currency rate update'
    
    currency_rate = fields.Float(string="Currency Rate", copy=False,digits=(12,3))
    dup_inverse_val = fields.Float(string="Inverse Value", copy=False,digits=(12,10), readonly=True)
    inverse_val = fields.Float(string="Inverse Value", copy=False,digits=(12,10))
    dup_invoice_date = fields.Date('Invoice Date')
    invoice_date = fields.Date('Invoice Date')

    @api.model
    def default_get(self, fields):
        rec = super(CurrencyRateUpdate, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('act_id')
        invoice_obj = self.env['account.invoice']
        invoice_ids = invoice_obj.search([('id', '=' , active_ids)])
        if invoice_ids.date_invoice:
            invoice_date = invoice_ids.date_invoice
        else:
            invoice_date = datetime.now().strftime('%Y-%m-%d')
        rec.update({
            'invoice_date': invoice_date,
            'dup_invoice_date': invoice_date,
        })

        return rec

    @api.multi
    def Done(self):
        pick_list=[]
        context = dict(self.env.context or {})
        act_id = context.get('act_id', False)
        
        if act_id and self.currency_rate > 0.00:
            invoice_id = self.env['account.invoice'].search([('id', '=', act_id)])
            invoice_id.write({
            'currency_rate': self.currency_rate,
            })            
            if self.invoice_date:
                invoice_date = self.invoice_date
            else:
                invoice_date = datetime.now().strftime('%Y-%m-%d')
            currency_id = self.env['res.currency.rate'].create({
                'rate': self.inverse_val,
                'currency_id': invoice_id.currency_id.id,
                'name': invoice_date,
            })
            
        return {'type': 'ir.actions.act_window_close'}
    
    @api.onchange('currency_rate')
    def onchange_inverse_value(self):
        if self.currency_rate > 0.00:
            self.inverse_val = 1 / self.currency_rate
            self.dup_inverse_val = 1 / self.currency_rate
        else:
            self.inverse_val = 0
            self.dup_inverse_val = 0

class PaymentCurrencyRateUpdate(models.TransientModel):
    _name = 'payment.currency.rate.update'
    _description = 'Payment Currency rate update'
    
    currency_rate = fields.Float(string="Currency Rate", copy=False,digits=(12,3))
    dup_inverse_val = fields.Float(string="Inverse Value", copy=False,digits=(12,10), readonly=True)
    inverse_val = fields.Float(string="Inverse Value", copy=False,digits=(12,10))
    dup_payment_date = fields.Date('Payment Date')
    payment_date = fields.Date('Payment Date')

    @api.model
    def default_get(self, fields):
        rec = super(PaymentCurrencyRateUpdate, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('act_id')
        payment_obj = self.env['account.payment']
        payment_ids = payment_obj.search([('id', '=' , active_ids)])
        if payment_ids.payment_date:
            payment_date = payment_ids.payment_date
        else:
            payment_date = datetime.now().strftime('%Y-%m-%d')
        rec.update({
            'payment_date': payment_date,
            'dup_payment_date': payment_date,
        })

        return rec

    @api.multi
    def Done(self):
        pick_list=[]
        context = dict(self.env.context or {})
        act_id = context.get('act_id', False)
        
        if act_id and self.currency_rate > 0.00:
            payment_id = self.env['account.payment'].search([('id', '=', act_id)])
            payment_id.write({
            'currency_rate': self.currency_rate,
            })            
            if self.payment_date:
                payment_date = self.payment_date
            else:
                payment_date = datetime.now().strftime('%Y-%m-%d')
            currency_id = self.env['res.currency.rate'].create({
                'rate': self.inverse_val,
                'currency_id': payment_id.currency_id.id,
                'name': payment_date,
            })
            
        return {'type': 'ir.actions.act_window_close'}
    
    @api.onchange('currency_rate')
    def onchange_inverse_value(self):
        if self.currency_rate > 0.00:
            self.inverse_val = 1 / self.currency_rate
            self.dup_inverse_val = 1 / self.currency_rate
        else:
            self.inverse_val = 0
            self.dup_inverse_val = 0