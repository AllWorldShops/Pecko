# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = "res.company"
    
    duty_local = fields.Boolean(string='Duty Applicable')
    invat_local = fields.Boolean(string='IN VAT Applicable')
    outvat_local = fields.Boolean(string='Out VAT Applicable')
    invat_claim_local = fields.Boolean(string='IN VAT Claimable')
    outvat_claim_local = fields.Boolean(string='Out VAT Claimable')
    duty_overseas = fields.Boolean(string='Duty Applicable')
    invat_overseas = fields.Boolean(string='IN VAT Applicable')
    outvat_overseas = fields.Boolean(string='Out VAT Applicable')
    invat_claim_overseas = fields.Boolean(string='IN VAT Claimable')
    outvat_claim_overseas = fields.Boolean(string='Out VAT Claimable')
    wh_loaction_local_id = fields.Many2one('stock.location',"WH/Location")
    wh_loaction_overseas_id = fields.Many2one('stock.location',"WH/Location")
    auto_assign = fields.Boolean(string='Auto Assign')


class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    wh_loaction_local_id = fields.Many2one('stock.location',"WH/Location", company_dependent=True)
    wh_loaction_overseas_id = fields.Many2one('stock.location',"Overseas WH/Location", company_dependent=True)
    duty_overseas = fields.Boolean(string='Overseas Duty Applicable', company_dependent=True)
    invat_overseas = fields.Boolean(string='Overseas IN VAT Applicable', company_dependent=True)
    outvat_overseas = fields.Boolean(string='Overseas Out VAT Applicable', company_dependent=True)
    invat_claim_overseas = fields.Boolean(string='Overseas IN VAT Claimable', company_dependent=True)
    outvat_claim_overseas = fields.Boolean(string='Overseas Out VAT Claimable', company_dependent=True)
    duty_local = fields.Boolean('Duty Applicable', company_dependent=True)
    invat_local = fields.Boolean(string='IN VAT Applicable', company_dependent=True)
    outvat_local = fields.Boolean(string='Out VAT Applicable', company_dependent=True)
    invat_claim_local = fields.Boolean(string='IN VAT Claimable', company_dependent=True)
    outvat_claim_local = fields.Boolean(string='Out VAT Claimable', company_dependent=True)
    auto_assign = fields.Boolean(string='Auto Assign', company_dependent=True)
    
    
    