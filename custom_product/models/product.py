# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name')
    storage_location_id = fields.Many2one('stock.location',string='Storage Location')
    
# class ProductProduct(models.Model):
#     _inherit = 'product.product'
# 
#     manufacturer_id = fields.Many2one('product.manufacturer',string='Manufacturer/Customer Name',related='product_tmpl_id.manufacturer_id',store=True)
#     
#     @api.multi
#     def write(self, vals):
#         rec = super(ProductProduct, self).write(vals)
#         if vals.get('manufacturer_id'):
#             product_id = self.env['product.product'].search([('id','=',self.id)])
#             product_id.product_tmpl_id.manufacturer_id = vals.get('manufacturer_id')
#         return rec

# class UomCategory(models.Model):
#     _inherit = 'uom.category'

#     ref_id = fields.Integer(string='Ref ID')

# class UomUom(models.Model):
#     _inherit = 'uom.uom'

#     ref_id = fields.Integer(string='Ref ID')

# class ProductCategory(models.Model):
#     _inherit = 'product.category'

#     ref_id = fields.Integer(string='Ref ID')
#     ref_id_2 = fields.Integer(string='Ref ID 2')
#     parent_left = fields.Integer(string='Ref ID 2')
#     parent_right = fields.Integer(string='Ref ID 2')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_studio_field_CCkqP = fields.Char(string='Ref ID')
    x_studio_field_fr3x5 = fields.Boolean(string='Ref ID1')
    x_studio_field_015p9 = fields.Char(string='Ref ID2')
    x_studio_field_Komya = fields.Boolean(string='Ref ID3')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    mps_active = fields.Boolean(string='MPS Active')
    mps_forecasted = fields.Float(string='MPS Forecasted')
    mps_min_supply = fields.Float(string='MPS Min Supply')
    mps_max_supply = fields.Float(string='MPS Max Supply')
    mps_apply = fields.Datetime(string='MPS Date')
    apply_active = fields.Boolean(string='Apply Active')
    x_studio_field_E1WLc = fields.Boolean(string='E Active')

class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    x_studio_field_fbauF = fields.Float(string='Test')
    
    


