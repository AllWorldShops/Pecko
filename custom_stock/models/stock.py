# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    mrp_do_no = fields.Char(string='DO No')
    carrier = fields.Char(string='Carrier')
    
    @api.model
    def create(self, vals):
        if vals.get('backorder_id'):
            vals['mrp_do_no'] = ''
        return super(StockPicking, self).create(vals)
        
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    additional_notes = fields.Char(string='Additional Notes')
    mrp_order_no = fields.Char(string='Manufacturing Order Number')
    mrp_do_no = fields.Char(related='picking_id.mrp_do_no', string='DO No', store=True)
    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer')
    
    @api.onchange('product_id')
    def onchange_product_id_stock_name(self):
        self.name = self.product_id.product_tmpl_id.x_studio_field_mHzKJ
        
    @api.model
    def create(self, vals):
        if vals.get('product_id'):
            product_id = self.env['product.product'].search([('id','=',vals.get('product_id'))])
            vals['manufacturer_id'] = product_id.product_tmpl_id.manufacturer_id.id
        if vals.get('sale_line_id'):
            sale_line_id = self.env['sale.order.line'].search([('id','=',vals.get('sale_line_id'))])
            vals['name'] = sale_line_id.name
        if vals.get('purchase_line_id'):
            purchase_line_id = self.env['purchase.order.line'].search([('id','=',vals.get('purchase_line_id'))])
            vals['name'] = purchase_line_id.name
        return super(StockMove, self).create(vals)
    
    @api.multi
    def action_additional_notes(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        context.update({'act_id':self.id})
        return {
            'name': _('Additional Notes'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move.notes',
            'context': context,
            'target': 'new'
        }
        
    def _get_partner_id_for_valuation_lines(self):
        if self.picking_id:
            return (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
        if self.sale_line_id:
            return self.sale_line_id.order_partner_id or False
    
    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        self.ensure_one()
        AccountMove = self.env['account.move']
        quantity = self.env.context.get('forced_quantity', self.product_qty)
        quantity = quantity if self._is_in() else -1 * quantity

        # Make an informative `ref` on the created account move to differentiate between classic
        # movements, vacuum and edition of past moves.
        if self.picking_id:
            ref = self.picking_id.name
        else:
            ref = self.origin
        if self.env.context.get('force_valuation_amount'):
            if self.env.context.get('forced_quantity') == 0:
                ref = 'Revaluation of %s (negative inventory)' % ref
            elif self.env.context.get('forced_quantity') is not None:
                ref = 'Correction of %s (modification of past move)' % ref

        move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value), credit_account_id, debit_account_id)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': ref,
                'stock_move_id': self.id,
            })
            new_account_move.post()