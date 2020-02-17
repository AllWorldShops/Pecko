from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    segment_master_id = fields.Many2one('segment.master',string='Local/Overseas',required=True)
    
    