from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    @api.constrains('segment_master_id')
    def _segment_master(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.segment_master_id:
                if rec.partner_id.segment_master_id.id != rec.segment_master_id.id:
                    raise ValidationError(_('The Segment is different for this partner'))
    
    segment_master_id = fields.Many2one('segment.master',string='Local/Overseas',readonly=False)
    
    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.fiscal_position_id = False
            self.payment_term_id = False
            self.currency_id = False
            self.segment_master_id = False
        else:
            self.fiscal_position_id = self.env['account.fiscal.position'].with_context(company_id=self.company_id.id).get_fiscal_position(self.partner_id.id)
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
            self.currency_id = self.partner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id
            self.segment_master_id = self.partner_id.segment_master_id.id
        return {}
    
    @api.model
    def create(self,vals):  
        res = super(PurchaseOrder, self).create(vals)
        if res.segment_master_id and res.segment_master_id.po_sequence_id:
            sequence = self.env['ir.sequence'].search([('id','=',res.segment_master_id.po_sequence_id.id),('company_id','=',self.env.user.company_id.id)])
            if sequence:
                res.name = sequence._next()
            else:
                res.name = self.env['ir.sequence'].next_by_code('purchase.order')
        return res