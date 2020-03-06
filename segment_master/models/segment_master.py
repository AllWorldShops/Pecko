from odoo import api, fields, models

class SegmentMaster(models.Model):   
    _name = "segment.master"
    
    name = fields.Char('Name')
    code = fields.Char('Code')
    so_sequence_id = fields.Many2one('ir.sequence',string='SO Sequence',company_dependent=True)
    po_sequence_id = fields.Many2one('ir.sequence',string='PO Sequence',company_dependent=True)
    
class ResCompany(models.Model):
    _inherit = "res.company"
    
    so_sequence_id = fields.Many2one('ir.sequence',string='SO Sequence')
    po_sequence_id = fields.Many2one('ir.sequence',string='PO Sequence')    
    