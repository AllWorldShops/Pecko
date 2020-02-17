from odoo import api, fields, models, _
from setuptools.dist import sequence
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.constrains('segment_master_id')
    def _segment_master(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.segment_master_id:
                if rec.partner_id.segment_master_id.id != rec.segment_master_id.id:
                    raise ValidationError(_('The Segment is different for this partner'))
    
    segment_master_id = fields.Many2one('segment.master',string='Local/Overseas',readonly=False)
    
    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
                'segment_master_id':False
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'user_id': self.partner_id.user_id.id or self.env.uid,
            'segment_master_id':self.partner_id.segment_master_id
        }
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)
        
    @api.model
    def create(self,vals):
        res = super(SaleOrder,self).create(vals)
        if res.segment_master_id and res.segment_master_id.so_sequence_id:
            sequence = self.env['ir.sequence'].search([('id','=',res.segment_master_id.so_sequence_id.id),('company_id','=',self.env.user.company_id.id)])
            if sequence:
                res.name = sequence._next()
            else:
                res.name = self.env['ir.sequence'].next_by_code('sale.order')
        return res