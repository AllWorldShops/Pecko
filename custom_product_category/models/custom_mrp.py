from odoo import models, fields, api, _
from docutils.nodes import line

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    segment_master_id = fields.Many2one('segment.master',string='Local/Overseas')
    location_wh_id = fields.Many2one('stock.location',string='Location')
    is_auto_assign = fields.Boolean("Auto Assign",compute="compute_is_auto_assign")
    picking_assign_id  = fields.Many2one('stock.picking',string='Picking',compute="compute_picking_assign_id")
    is_picking_auto_assign = fields.Boolean("Auto Assign Picking")
    
    def compute_is_auto_assign(self):
        if self.product_id.categ_id.auto_assign == True:
            self.is_auto_assign = True
            for line_ids in self.move_raw_ids:
                    line_ids.write({
                                'is_auto_assign': True,
                                  })
        else:
            self.is_auto_assign = False
            for line_ids in self.move_raw_ids:
                    line_ids.write({
                                'is_auto_assign': False,
                                  })
                    
    def compute_picking_assign_id(self):
        picking_stock_assign_id = self.env['stock.picking'].search([('origin','=',self.name)])
        if picking_stock_assign_id:
            self.picking_assign_id = picking_stock_assign_id.id
                   
    @api.onchange('location_wh_id')
    def onchange_location_wh_id(self):
        self.is_locked = False
        
        for line_ids in self.move_raw_ids:
            if self.location_wh_id:
                line_ids.available_location_wh_id = self.location_wh_id.id
                stock_quant_id = self.env['stock.quant'].search([('product_id','=',line_ids.product_id.id),('location_id','=',self.location_wh_id.id)])
                product_id_stock = ''
                quantity = 0
                if stock_quant_id:
                    for qty_hand in stock_quant_id:
                        product_id_stock = qty_hand.product_id.id
                        quantity += qty_hand.quantity
                    if line_ids.product_id.id == product_id_stock:
                        line_ids.available_qty_done = quantity 
                    quantity = 0  
                else:
                    line_ids.available_qty_done = 0 
                    
    def action_internal_move_picking(self): 
        for line_items in self.move_raw_ids:
            if line_items.available_location_wh_id:
                line_items.action_create_move()
                mrp_production_assign_id = self.env['mrp.production'].search([('name','=',line_items.origin)])
                if mrp_production_assign_id:
                    mrp_production_assign_id.is_picking_auto_assign = True
                    
    def action_is_locked_assign(self): 
        if self.is_locked == False:
            self.is_locked = True             
                    
class StockMove(models.Model):
    _inherit = "stock.move"
    
    available_location_wh_id = fields.Many2one('stock.location',string='Available WH/LOC')
    available_qty_done = fields.Integer("Available Qty")
    is_internal_move = fields.Boolean("Internal Move")
    is_auto_assign = fields.Boolean("Auto Assign")
    
    def action_create_move(self):  
        if self.origin:
            mrp_production_id = self.env['mrp.production'].search([('name','=',self.origin)])
            picking_stock_id = self.env['stock.picking'].search([('origin','=',self.origin)])
            current_company_id = self.env.user.company_id
            picking_location_id = self.env['stock.picking.type'].search([('warehouse_id.company_id','=',current_company_id.id),('code','=','internal')],limit=1)
            
            create_lines=[]
            if mrp_production_id:
                if not picking_stock_id:
                    if self.is_internal_move == False:
                        if self.available_qty_done >0:
                            create_lines.append({
                                        'product_id': self.product_id.id,
                                        'customer_part_no':self.customer_part_no,
                                        'name':self.name,
                                        'manufacturer_id': self.manufacturer_id.id or False,
                                        'product_uom_qty':self.available_qty_done,
#                                         'quantity_done': self.available_qty_done,
                                        'product_uom': self.product_uom.id or False,
                                        'location_id':mrp_production_id.location_wh_id.id or False,
                                        'location_dest_id': mrp_production_id.location_src_id.id or False,
                                        'picking_type_id': picking_location_id.id,
                                        'state':'draft',
                                        })
                            self.env['stock.picking'].create({
                                        'origin': self.origin,
                                        'location_dest_id': mrp_production_id.location_src_id.id or False,
                                        'picking_type_id': picking_location_id.id,
                                        'location_id':mrp_production_id.location_wh_id.id or False,
                                        'move_ids_without_package': [(0, 0, line) for line in create_lines],
                                        'state':'draft',
                                        })
                            self.is_internal_move =True
                        
                if picking_stock_id: 
                    if self.is_internal_move == False:
                        if self.available_qty_done >0:
                            self.env['stock.move'].create({
                                            'picking_id':picking_stock_id.id,
                                            'product_id': self.product_id.id,
                                            'customer_part_no':self.customer_part_no,
                                            'name':self.name,
                                            'manufacturer_id': self.manufacturer_id.id or False,
                                            'product_uom_qty':self.available_qty_done,
#                                             'quantity_done': self.available_qty_done,
                                            'product_uom': self.product_uom.id or False,
                                            'location_id':mrp_production_id.location_wh_id.id or False,
                                            'location_dest_id': mrp_production_id.location_src_id.id or False,
                                            'picking_type_id': picking_location_id.id,
                                            'state':'draft',
                                            }) 
                            self.is_internal_move =True
                    
                    
        
        
        
        
        
        
