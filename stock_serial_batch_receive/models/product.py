from odoo import api, fields, models, tools, _

class ProductCategory(models.Model):
    _inherit = "product.category"
    
    company_id = fields.Many2one('res.company',string='Company', required=True, default=lambda self:self.env.user.company_id)
    product_sequence_id = fields.Many2one('ir.sequence',string='Product Sequence Local',company_dependent=True)
    product_sequence_overseas_id = fields.Many2one('ir.sequence',string='Product Sequence Overseas',company_dependent=True)
