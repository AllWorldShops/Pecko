# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import UserError

    
class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    
    @api.multi
    def button_validate(self):
        for line_items_ids in self.cost_lines:
            if line_items_ids.price_unit <= 0:
                raise UserError(_('Cost contains zero value .It cannot be validated')) 
        if any(cost.state != 'draft' for cost in self):
            raise UserError(_('Only draft landed costs can be validated'))
        if any(not cost.valuation_adjustment_lines for cost in self):
            raise UserError(_('No valuation adjustments lines. You should maybe recompute the landed costs.'))
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
            }
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                # Prorate the value at what's still in stock
                cost_to_add = (line.move_id.remaining_qty / line.move_id.product_qty) * line.additional_landed_cost

                new_landed_cost_value = line.move_id.landed_cost_value + line.additional_landed_cost
                line.move_id.write({
                    'landed_cost_value': new_landed_cost_value,
                    'value': line.move_id.value + line.additional_landed_cost,
                    'remaining_value': line.move_id.remaining_value + cost_to_add,
                    'price_unit': (line.move_id.value + line.additional_landed_cost) / line.move_id.product_qty,
                })
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = line.move_id.product_qty - line.move_id.remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

            move = move.create(move_vals)
            cost.write({'state': 'done', 'account_move_id': move.id})
            move.post()
        return True
    
    def get_valuation_lines(self):
            lines = []
            for move in self.mapped('picking_ids').mapped('move_lines'):
           
                # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
    #             if move.product_id.valuation != 'real_time' or move.product_id.cost_method != 'fifo':
                if move.product_id.cost_method == 'real_time':
                    continue
                if move.picking_id.partner_id.segment_master_id.code == 'local':
                    if move.product_id.categ_id.duty_local == True:
                        vals = {
                            'product_id': move.product_id.id,
                            'move_id': move.id,
                            'quantity': move.product_qty,
                            'former_cost': move.value,
                            'weight': move.product_id.weight * move.product_qty,
                            'volume': move.product_id.volume * move.product_qty
                        }
                        lines.append(vals)
                if move.picking_id.partner_id.segment_master_id.code == 'overseas':
                    if move.product_id.categ_id.duty_overseas == True:
                        vals = {
                            'product_id': move.product_id.id,
                            'move_id': move.id,
                            'quantity': move.product_qty,
                            'former_cost': move.value,
                            'weight': move.product_id.weight * move.product_qty,
                            'volume': move.product_id.volume * move.product_qty
                        }
                        lines.append(vals)
    #         if not lines and self.mapped('picking_ids'):
    #             raise UserError(_("You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO costing method."))
            return lines    
        
        
        
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    landing_cost_id = fields.Many2one('account.journal',"Landing Cost Journals",related='company_id.landing_cost_id',
        readonly=False, help="Enable Journals For Landed Cost",domain=[('is_landing_cost','=',True)])
    
    
class ResCompany(models.Model):
    _inherit = 'res.company'
    
    landing_cost_id = fields.Many2one('account.journal',"Landing Cost Journals")
    
    
class ProductProduct(models.Model):
    _inherit = 'product.product'
        
    debit_account_id = fields.Many2one('account.account',"Debit Account")
    
class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'
    
    def _create_accounting_entries(self, move, qty_out):
        # TDE CLEANME: product chosen for computation ?
        cost_product = self.cost_line_id.product_id
        if not cost_product:
            return False
        accounts = self.product_id.product_tmpl_id.get_product_accounts()
        debit_account_id = self.cost_line_id.product_id.debit_account_id.id or False
        already_out_account_id = accounts['stock_output'].id
        credit_account_id = self.cost_line_id.product_id.property_account_expense_id.id or False

        if not credit_account_id:
            raise UserError(_('Please configure Stock Expense Account for product: %s.') % (cost_product.name))
        
        if not debit_account_id:
            raise UserError(_('Please configure Debit Account for product: %s.') % (cost_product.name))
        
        return self._create_account_move_line(move, credit_account_id, debit_account_id, qty_out, already_out_account_id)

  
    
    
    