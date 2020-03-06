# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare

from odoo.exceptions import UserError

from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    tax_mandatory = fields.Boolean(string='Mandatory')
    
    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        product_location_id = self.env['product.product'].search([('id','=',self.product_id.id)])
        
        landing_field = ''
        location_bonded_id = ''
        if self.order_id.segment_master_id.code == 'local':
            if product_location_id.categ_id.duty_local == True:
                landing_field = True
            
            if product_location_id.categ_id.wh_loaction_local_id:
                location_bonded_id = product_location_id.categ_id.wh_loaction_local_id
                     
        if self.order_id.segment_master_id.code == 'overseas':
            if product_location_id.categ_id.duty_overseas == True:
                landing_field = True
            
            if product_location_id.categ_id.wh_loaction_overseas_id:
                location_bonded_id = product_location_id.categ_id.wh_loaction_overseas_id
                     
        if not location_bonded_id:
            location_bonded_id = self.order_id.picking_type_id.default_location_dest_id
            
        if not landing_field:
            landing_field = False    
            
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': location_bonded_id.id,
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'is_landing': landing_field,
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if self.product_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = diff_quantity
            res.append(template)
        return res
    
    
    

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    landing_duty = fields.Boolean(string='Landing Duty(Applicable)',compute='_landing_duty')
    
    @api.one
    def _landing_duty(self):
        count = 0
        if self.segment_master_id.code == 'local':
            for list in self.order_line:
                if list.product_id.categ_id.duty_local == True:
                    count +=1
        if self.segment_master_id.code == 'overseas': 
            for list in self.order_line:
                if list.product_id.categ_id.duty_overseas == True:
                    count +=1          
        if count > 0:
            self.landing_duty = True
            
    @api.onchange('segment_master_id','order_line')
    def onchange_order_line(self): 
        if self.segment_master_id.code == 'local':
            for list in self.order_line:
                if list.product_id.categ_id.invat_local == True:
                    list.tax_mandatory = True
                else:
                    list.tax_mandatory = False   
        
        if self.segment_master_id.code == 'overseas':
            for list in self.order_line:
                if list.product_id.categ_id.invat_overseas == True:
                    list.tax_mandatory = True
                else:
                    list.tax_mandatory = False     
                    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'   
    
    tax_mandatory = fields.Boolean(string='Mandatory')         
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'           
    
    @api.onchange('segment_master_id','order_line')
    def onchange_order_line(self): 
        if self.segment_master_id.code == 'local':
            for list in self.order_line:
                if list.product_id.categ_id.outvat_local == True:
                    list.tax_mandatory = True
                else:
                    list.tax_mandatory = False   
        
        if self.segment_master_id.code == 'overseas':
            for list in self.order_line:
                if list.product_id.categ_id.outvat_overseas == True:
                    list.tax_mandatory = True
                else:
                    list.tax_mandatory = False   
                         
