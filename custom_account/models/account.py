# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _

class Company(models.Model):
    _inherit = "res.company"
    
    fax = fields.Char('Fax')
    street1 = fields.Char('Street 1')
    
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.multi
    def _get_do(self):
#         sale_id = self.env['sale.order'].search([('name','=',self.origin)],limit=1)
#         do_name = ''
#         if sale_id:
#             do_id = self.env['stock.picking'].search([('sale_id','=',sale_id.id)])
#             for rec in do_id:
#                 if not do_name:
#                     do_name =  rec.name
#                 else:
#                     do_name += ','+ rec.name
#         self.do_name = do_name
#         for line in self.invoice_line_ids:  
        sale_order_line_id = self.env['sale.order.line'].search([('invoice_lines','in',self.invoice_line_ids.ids)])
        do_name = ''
        if sale_order_line_id:
            move_id = self.env['stock.move'].search([('sale_line_id','=',sale_order_line_id.ids),('state','=','done')])
            print()
            if move_id:
                do_id = {}
                for rec in move_id:
                    do_id.setdefault(rec.picking_id,[]).append(rec)
                for key,val in do_id.items():
                    if not do_name:
                        do_name =  key.name
                    else:
                        do_name += ','+ key.name
                self.do_name = do_name 
        print(do_name,'rraaraaa')  
#         print (sale_line_id,'tttttttttttttttttttt')
    currency_conv_rate = fields.Float('Currency Conversation Rate', copy=False, readonly=True, help='It will show the currency conversation value against the invoice currency id.')
    company_currency_id = fields.Many2one('res.currency', 'Invoice Rate Currency', copy=False, related='company_id.currency_id', readonly=True)
    exchange_rate = fields.Float('Exchange Rate', digits=(12,6), copy=False, readonly=True, help='The specific rate that will be used, in this invoice, between the selected currency (in \'Invoice Rate Currency\' field)  and the Invoice currency.')
    currency_help_label = fields.Text(string="Helping Sentence", copy=False, readonly=True, help="This sentence helps you to know how to specify the invoice rate by giving you the direct effect it has")
    do_name = fields.Char(string="DO No.",compute='_get_do',readonly=True)
     
    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if res.company_id.currency_id != res.currency_id:
            if res.date_invoice:
                rate_id = self.env['res.currency.rate'].search([('name','=',res.date_invoice),('currency_id','=',res.currency_id.id)])
                if rate_id:
                    res.exchange_rate = rate_id.rate
                    res.currency_conv_rate = (1/rate_id.rate)
                    val = round(res.currency_conv_rate,2)
                    res.currency_help_label = 'At the operation date, the exchange rate was \n'+res.currency_id.symbol+'1.00 = '+res.company_id.currency_id.symbol+' '+str(val)+'\n'+res.company_currency_id.symbol+'1.00 = '+res.currency_id.symbol+' '+str(res.exchange_rate)   
                else:
                    rate_id = self.env['res.currency'].search([('id','=',res.currency_id.id)])
                    res.exchange_rate = rate_id.rate
                    res.currency_conv_rate = (1/rate_id.rate)
                    val = round(res.currency_conv_rate,2)
                    res.currency_help_label = 'At the operation date, the exchange rate was \n'+res.currency_id.symbol+'1.00 = '+res.company_id.currency_id.symbol+' '+str(val)+'\n'+res.company_currency_id.symbol+'1.00 = '+res.currency_id.symbol+' '+str(res.exchange_rate)
            else:
                rate_id = self.env['res.currency'].search([('id','=',res.currency_id.id)])
                res.exchange_rate = rate_id.rate
                res.currency_conv_rate = (1/rate_id.rate)
                val = round(res.currency_conv_rate,2)
                res.currency_help_label = 'At the operation date, the exchange rate was \n'+res.currency_id.symbol+'1.00 = '+res.company_id.currency_id.symbol+' '+str(val)+'\n'+res.company_currency_id.symbol+'1.00 = '+res.currency_id.symbol+' '+str(res.exchange_rate)
        else:
            res.exchange_rate = 0.00
            res.currency_conv_rate = 0.00
            res.currency_help_label = ''
        return res
    
    @api.multi
    def currency_values(self):
        if self.company_id.currency_id != self.currency_id:
            if self.date_invoice:
                rate_id = self.env['res.currency.rate'].search([('name','=',self.date_invoice),('currency_id','=',self.currency_id.id)])
                if rate_id:
                    self.exchange_rate = rate_id.rate
                    self.currency_conv_rate = (1/rate_id.rate)
                    val = round(self.currency_conv_rate,2)
                    self.currency_help_label = 'At the operation date, the exchange rate was \n'+self.currency_id.symbol+'1.00 = '+self.company_id.currency_id.symbol+' '+str(val)+'\n'+self.company_currency_id.symbol+'1.00 = '+self.currency_id.symbol+' '+str(self.exchange_rate)
                else:
                    rate_id = self.env['res.currency'].search([('id','=',self.currency_id.id)])
                    self.exchange_rate = rate_id.rate
                    self.currency_conv_rate = (1/rate_id.rate)
                    val = round(self.currency_conv_rate,2)
                    self.currency_help_label = 'At the operation date, the exchange rate was \n'+self.currency_id.symbol+'1.00 = '+self.company_id.currency_id.symbol+' '+str(val)+'\n'+self.company_currency_id.symbol+'1.00 = '+self.currency_id.symbol+' '+str(self.exchange_rate)
            else:
                rate_id = self.env['res.currency'].search([('id','=',self.currency_id.id)])
                self.exchange_rate = rate_id.rate
                self.currency_conv_rate = (1/rate_id.rate)
                val = round(self.currency_conv_rate,2)
                self.currency_help_label = 'At the operation date, the exchange rate was \n'+self.currency_id.symbol+'1.00 = '+self.company_id.currency_id.symbol+' '+str(val)+'\n'+self.company_currency_id.symbol+'1.00 = '+self.currency_id.symbol+' '+str(self.exchange_rate)
        else:
            self.exchange_rate = 0.00
            self.currency_conv_rate = 0.00
            self.currency_help_label = ''
    
    def get_currency_conv_rate(self,):
        conv_rate = 0.00
        for record in self:
            if record.currency_conv_rate:
                conv_rate = round(record.currency_conv_rate,4)
        return conv_rate
            
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name')
    
    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product_id = self.env['product.product'].search([('id','=',vals.get('product_id'))])
            vals['manufacturer_id'] = product_id.manufacturer_id.id
        return super(AccountInvoiceLine, self).create(vals)
        
    @api.onchange('product_id')
    def onchange_invoice_line_product(self):
        if self.product_id:
            self.manufacturer_id = self.product_id.manufacturer_id
