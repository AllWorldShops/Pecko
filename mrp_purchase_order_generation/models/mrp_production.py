from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    purchase_order_id = fields.Many2many('purchase.order','mrp_order',string="Pruchase Order")
#     manufacture_order_id = fields.Many2many('mrp.production',string="Manufacture Order")
    mo_name = fields.Char('MO Name')
    @api.multi
    def action_purchase_order(self):
        buy = {}
        manufacture = []
        if not self.purchase_order_id:
            for lines in self.move_raw_ids:
                if lines.product_uom_qty > lines.reserved_availability:
#                     print (lines.product_id.route_ids.name)
                    for route in lines.product_id.route_ids:
                        if route.name == 'Buy':
                            buy.setdefault(lines.product_id.seller_ids[0].name, []).append({'partner_id':lines.product_id.seller_ids[0],
                                         'product_id':lines.product_id,
                                         'qty':lines.product_uom_qty - lines.reserved_availability,
                                         'route_name': [route.name for route in lines.product_id.route_ids if route.name in ['Buy','Manufacture']]
                                         })
                        elif route.name == 'Manufacture':
                            manufacture.append({
                                         'product_id':lines.product_id,
                                         'qty':lines.product_uom_qty - lines.reserved_availability,
                                         'route_name': [route.name for route in lines.product_id.route_ids if route.name in ['Buy','Manufacture']]
                                         })
            print(manufacture,'lllllllllllll')
            #purchase order creation
            for key,val in buy.items():
                record_id = []
                order_id = self.env['purchase.order'].create({
                        'partner_id': key.id,
                        'company_id': self.company_id.id,
                        'currency_id': key.with_context(force_company=self.company_id.id).property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
                        'origin': self.name,
                        'date_order': datetime.today(),
                        })
                for line in val:
                    line_id = self.env['purchase.order.line'].create({
                                                'name': line['product_id'].name,
                                                'product_qty': line['qty'],
                                                'product_id': line['product_id'].id,
                                                'product_uom': line['product_id'].uom_po_id.id,
                                                'price_unit': line['product_id'].lst_price,
                                                'date_planned': datetime.today(),
    #                                             'taxes_id': [(6, 0, taxes_id.ids)],
                                                'order_id': order_id.id,
                                            })
                record_id.append(order_id.id)
                print(record_id)
                self.write({'purchase_order_id' : [(6,0,record_id)]})
            
#             for val in manufacture:
            rec_id = []
            for line in manufacture:
                print (line)
                product_tmpl = self.env['product.product'].search([('id','=',line['product_id'].id)])
                mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id','=',product_tmpl.product_tmpl_id.id)])
                if mrp_bom:
                    print(line['product_id'].name,line['product_id'].uom_id.id)
                    manufacture_id = self.env['mrp.production'].create({
                            'product_id': line['product_id'].id,
                            'product_qty': line['qty'],
                            'product_uom_id':line['product_id'].product_tmpl_id.uom_id.id,
                            'bom_id': mrp_bom[0].id,
                            'customer_part_no': line['product_id'].name,
                            'origin':self.name,
                             'company_id': self.company_id.id,
                             'mo_name':self.name
                            })
                    if manufacture_id:
                        manufacture_id.location_src_id = manufacture_id.picking_type_id.default_location_src_id.id
                        manufacture_id.location_dest_id = manufacture_id.picking_type_id.default_location_dest_id.id
                    rec_id.append(manufacture_id.id)
            print(rec_id)
#                 self.write({'manufacture_order_id':[(6,0,rec_id)]})
#                     if mrp_borm:
#                         line_id = self.env['stock.move'].create({
#                                                     'name': line['product_id'].name,
#                                                     'product_uom_qty': line['qty'],
#                                                     'product_id': line['product_id'].id,
#                                                     'customer_part_no':line['product_id'].name or '',
#                                                     'product_uom': line['product_id'].uom_po_id.id,
#                                                     'price_unit': line['product_id'].lst_price,
#                                                     '': order_id.id,
#                                                 })
#                         lines_id.append(line_id)
#                 for record in lines_id:
#                     manufacture_id = self.env['mrp.production'].create({
#                             'product_id': key.id,
#                             'company_id': self.company_id.id,
#                             'currency_id': key.with_context(force_company=self.company_id.id).property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
#                             'origin': self.name,
#                             'date_order': datetime.today(),
#                             })
                
#             self.purchase_order_id = order_id.id
#             view_id = self.env.ref('purchase.purchase_order_form').id
#             return {
#                 'name':'Purchase Order',
#                 'view_type':'form',
#                 'view_mode':'form',
#                 'views' : [(view_id,'form')],
#                 'res_model':'purchase.order',
#                 'view_id':view_id,
#                 'type':'ir.actions.act_window',
#                 'res_id':order_id.id,
#                 'target':'current',
#                 
#                 }
    
    @api.multi       
    def action_view_purchase_order_form(self):
        view_id = self.env.ref('purchase.purchase_order_tree').id
        form_id = self.env.ref('purchase.purchase_order_form').id
        print(view_id)
        return {
            'name':'Purchase Order',
            'view_type':'tree',
            'view_mode':'tree',
            'views' : [(view_id,'list'),(form_id,'form')],
            'res_model':'purchase.order',
            'view_id':view_id,
            'type':'ir.actions.act_window',
#             'res_id':self.purchase_order_id.ids,
            'target':'current',
            'domain': [('id', 'in', self.purchase_order_id.ids)],            
            }
    
    @api.multi       
    def action_view_mrp_order_form(self):
        view_id = self.env.ref('mrp.mrp_production_tree_view').id
        form_id = self.env.ref('mrp.mrp_production_form_view').id
        print(view_id)
        return {
            'name':'Manufacture Order',
            'view_type':'tree',
            'view_mode':'tree,form',
            'views' : [(view_id,'list'),(form_id,'form')],
            'res_model':'mrp.production',
            'view_id':view_id,
            'type':'ir.actions.act_window',
#             'res_id':self.purchase_order_id.ids,
            'target':'current',
            'domain': [('mo_name', '=', self.name)],            
            }