# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Treesa Maria(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo.exceptions import UserError
from odoo import fields, models, api, _
from odoo.tools import float_is_zero
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_compare


class CustomerInvoice(models.Model):
    _inherit = 'res.partner'

    invoice_option = fields.Selection([('on_delivery', 'Delivered quantities'),
                                       ('before_delivery', 'Ordered quantities'), ],
                                      "Invoicing Policy")


class DeliveryInvoice(models.Model):

    _inherit = 'sale.order'

    invoice_option = fields.Selection([('on_delivery', 'Delivered quantities'),
                                       ('before_delivery', 'Ordered quantities'), ],
                                      string="Invoicing Policy", required=True, default='on_delivery')
    
    @api.onchange('partner_id')
    def onchange_customer(self):
        if self.partner_id:
            if self.partner_id.invoice_option:
                self.invoice_option = self.partner_id.invoice_option
            else:
                self.invoice_option = 'on_delivery'
    
#     @api.multi
#     def _prepare_invoice(self):
#         invoice_vals = super(SaleOrder, self)._prepare_invoice()
# #         invoice_vals['']
    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if self.invoice_option == 'before_delivery':
            inv_obj = self.env['account.invoice']
            for order in self:
                inv_data = order._prepare_invoice()
                invoice = inv_obj.create(inv_data)
                for inv_line in order.order_line:

                    inv_line.invoice_line_create(invoice.id, inv_line.product_uom_qty)

        else:
            inv_obj = self.env['account.invoice']
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            invoices = {}
            references = {}
            context = dict(self.env.context or {})
            for order in self:
                group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
                for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                    if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue
                    if group_key not in invoices:
                        inv_data = order._prepare_invoice()
                        if context.get('picking_id'):
                            pick_id = self.env['stock.picking'].browse(context.get('picking_id'))
                            inv_data['do_name'] = pick_id.name
                        if order.company_id.scheduled_date_invoice == 'scheduled_date':
                            inv_data['date_invoice'] = pick_id.scheduled_date.strftime('%Y-%m-%d')
                        if order.company_id.scheduled_date_invoice == 'current_date':
                            inv_data['date_invoice'] = datetime.now().strftime('%Y-%m-%d')
                        invoice = inv_obj.create(inv_data)
                        if invoice:
                            pick_id.invoice_created = True
                        
                        references[invoice] = order
                        invoices[group_key] = invoice
                    elif group_key in invoices:
                        vals = {}
                        if order.name not in invoices[group_key].origin.split(', '):

                            vals['origin'] = invoices[group_key].origin + ', ' + order.name
                        if order.client_order_ref and order.client_order_ref \
                                not in invoices[group_key].name.split(', '):

                            vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                        invoices[group_key].write(vals)
                    if line.qty_to_invoice > 0:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                    elif line.qty_to_invoice < 0 and final:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

                if references.get(invoices.get(group_key)):

                    if order not in references[invoices[group_key]]:

                        references[invoice] = references[invoice] | order
            if not invoices:

                raise UserError(_('There is no invoicable line.'))

            for invoice in invoices.values():

                if not invoice.invoice_line_ids:

                    raise UserError(_('There is no invoicable line.'))
                # If invoice is negative, do a refund invoice instead
                if invoice.amount_untaxed < 0:

                    invoice.type = 'out_refund'
                    for line in invoice.invoice_line_ids:

                        line.quantity = -line.quantity
                for line in invoice.invoice_line_ids:

                    line._set_additional_fields(invoice)
                invoice.compute_taxes()
                invoice.message_post_with_view('mail.message_origin_link',
                                               values={'self': invoice, 'origin': references[invoice]},
                                               subtype_id=self.env.ref('mail.mt_note').id)
            return [inv.id for inv in invoices.values()]


class InvoiceControl(models.Model):

    _inherit = 'stock.picking'

    invoice_control = fields.Selection([('to_invoice', 'To be Invoiced'),
                                        ('invoice_na', 'Not applicable'), ],
                                       string="Invoicing Policy", compute='get_invoice_control')
    invoice_created = fields.Boolean('Invoice Created', copy=False)
    journal_id = fields.Many2one('account.journal',string='Journal')
    billing_policy = fields.Selection([('to_be_billed', 'To be Billed'),
                                        ('no_bill', 'No Bill'), ],
                                       string="Billing Policy",default='no_bill',copy=False)
    
    @api.depends('group_id')
    def get_invoice_control(self):
        for group in self:
            obj = False
            if group.picking_type_code == 'outgoing':
                obj = self.env['sale.order'].search([('name', '=', group.group_id.name)])
            elif group.picking_type_code == 'incoming':
                obj = self.env['purchase.order'].search([('name', '=', group.group_id.name)])
            if obj:
                if obj.invoice_option == 'on_delivery':
                    group.invoice_control = 'to_invoice'
                elif obj.invoice_option == 'before_delivery':
                    group.invoice_control = 'invoice_na'
                else:
                    group.invoice_control = False

    @api.depends('group_id')
    def pick_create_invoices(self):
        for rec in self:
            if rec.picking_type_code == 'outgoing':
                sale_orders = self.env['sale.order'].search([('name', '=', rec.group_id.name)])
                sale_orders.with_context({'picking_id':rec.id}).action_invoice_create()
                return sale_orders.action_view_invoice()
            elif rec.picking_type_code == 'incoming':
                if rec.invoice_control:
                    purchase_orders = self.env['purchase.order'].search([('name', '=', rec.group_id.name)])
                    datas = {}
                    datas = {
                            'name':self.origin,
                            'partner_id':purchase_orders.partner_id.id,
                            'currency_id':purchase_orders.currency_id.id,
                            'payment_term_id':purchase_orders.payment_term_id.id,
                            'company_id':purchase_orders.company_id.id,
                            'purchase_id':purchase_orders.id,
                            'type': 'in_invoice',
                                   }
                    inv = self.env['account.invoice'].create(datas)
                    inv_line = []
                    for line in purchase_orders.order_line - inv.invoice_line_ids.mapped('purchase_line_id'):
                        data = inv._prepare_invoice_line_from_po_line(line)
                        inv_line.append((0,0,data))
                    inv.write({'invoice_line_ids':inv_line})
                    inv.write({'journal_id':self.journal_id.id})
                    rec.invoice_created = True
                    
                    action = self.env.ref('account.invoice_supplier_form').id
                    return {
                            'name': _('Invoices'),
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form,tree',
                            'res_model': 'account.invoice',
                            'views': [(action,'form')],
                            'view_id': action,
                            'res_id':inv.id,
                            'context': dict(inv.env.context, from_purchase_order_change=True,),
                        }
                else:
                    data = {}
                    datas = {'partner_id':self.partner_id.id,
                            'currency_id':self.company_id.currency_id.id,
                            'payment_term_id':self.partner_id.property_supplier_payment_term_id.id or False if self.partner_id else False,
                            'company_id':self.company_id.id,
                            'type': 'in_invoice',
                            'name':self.origin,
                                   }
                    inv = self.env['account.invoice'].create(datas)
                    inv_line = []
                    for move_lines in self.move_ids_without_package:
                        date = inv.date or inv.date_invoice
                        print(inv.name,move_lines.name,';;;;;;;;;;;;;;;;;;;;')
                        data = {
                            'name': move_lines.name,
                            'origin': self.origin,
                            'uom_id': move_lines.product_uom.id,
                            'product_id': move_lines.product_id.id,
                            'account_id': move_lines.product_id.property_account_expense_id.id or move_lines.product_id.categ_id.property_account_expense_categ_id.id,
                            'price_unit': inv.currency_id._convert(
                                move_lines.product_id.lst_price, self.company_id.currency_id, self.company_id, date or fields.Date.today(), round=False),
                            'quantity': move_lines.quantity_done,
                            'discount': 0.0,
#                             'journal_id':self.journal_id.id
#                             'account_analytic_id': line.account_analytic_id.id,
#                             'analytic_tag_ids': line.analytic_tag_ids.ids,
#                             'invoice_line_tax_ids': invoice_line_tax_ids.ids
                            }
                        inv_line.append((0,0,data))  
                    inv.write({'invoice_line_ids':inv_line})
                    action = self.env.ref('account.invoice_supplier_form').id
#                     journal_domain = [
#                     ('type', '=', 'purchase'),
#                     ('company_id', '=', self.company_id.id),
#                     ('currency_id', '=', self.partner_id.property_purchase_currency_id.id),
#                     ]
#                     default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
                    inv.write({'journal_id':self.journal_id.id})
                    rec.invoice_created = True
#                     print(default_journal_id,'ssasswefrwefre')
                    return {
                            'name': _('Invoices'),
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form,tree',
                            'res_model': 'account.invoice',
                            'views': [(action,'form')],
                            'view_id': action,
                            'res_id':inv.id,
                            'context':{'type':'in_invoice','journal_type': 'purchase'}
                        }
            
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    scheduled_date_invoice = fields.Selection([('current_date', 'Current Date'), ('scheduled_date', 'Scheduled Date'), ], default='current_date',
                                    readonly=False, related='company_id.scheduled_date_invoice', string='Based on Schedule Date')

 
class ResCompany(models.Model):
    _inherit = 'res.company'

    scheduled_date_invoice = fields.Selection([('current_date', 'Current Date'), ('scheduled_date', 'Scheduled Date')], string='Based on Schedule Date')

                                                             
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'  
    
    invoice_option = fields.Selection([('on_delivery', 'Delivered quantities'),
                                       ('before_delivery', 'Ordered quantities'), ],
                                      string="Invoicing Policy", required=True, default='on_delivery')
    
    @api.onchange('partner_id')
    def onchange_customer(self):
        if self.partner_id:
            if self.partner_id.invoice_option:
                self.invoice_option = self.partner_id.invoice_option
            else:
                self.invoice_option = 'on_delivery'

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    def _prepare_invoice_line_from_po_line(self, line):
        if line.product_id.purchase_method == 'purchase':
            qty = line.product_qty - line.qty_invoiced
        else:
            qty = line.qty_received - line.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0
        taxes = line.taxes_id
        invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes, line.product_id, line.order_id.partner_id)
        invoice_line = self.env['account.invoice.line']
        date = self.date or self.date_invoice
        data = {
            'purchase_line_id': line.id,
            'name': line.order_id.name + ': ' + line.name,
            'origin': line.order_id.origin,
            'uom_id': line.product_uom.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.order_id.currency_id._convert(
                line.price_unit, self.currency_id, line.company_id, date or fields.Date.today(), round=False),
            'quantity': qty,
            'discount': 0.0,
            'account_analytic_id': line.account_analytic_id.id,
            'analytic_tag_ids': line.analytic_tag_ids.ids,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids,
            'comapny_id':line.company_id.id,
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data