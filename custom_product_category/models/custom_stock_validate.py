# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
import datetime
from odoo.exceptions import AccessError, UserError
from dateutil.relativedelta import relativedelta


class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    is_landing_cost = fields.Boolean('Landing Cost')


class Picking(models.Model):
    _inherit = "stock.picking"
    
    landed_cost_id = fields.Many2one('stock.landed.cost','Landing Cost',compute='_compute_landed_cost')
    journal_entry_id = fields.Many2one('account.move','Journal Entry',compute='_compute_journal_entry')
    
    @api.one
    def _compute_journal_entry(self):
        journal_id = self.env['stock.landed.cost'].search([('picking_ids','in',self.id)])
        if journal_id:
            self.journal_entry_id = journal_id.account_move_id.id
    
    @api.one
    def _compute_landed_cost(self):
        pick_id = self.env['stock.landed.cost'].search([('picking_ids','in',self.id)])
        if pick_id:
            self.landed_cost_id = pick_id
    
    @api.multi
    def button_validate(self):
        result = super(Picking, self).button_validate()
        current_date = datetime.date.today()
        current_company = self.env.user.company_id
        if not self.company_id.landing_cost_id:
            raise UserError(_('Please Configure The Journals In Account Settings.'))
        
        if self.partner_id.segment_master_id.code == 'local':
            count=0
            for list in self.move_ids_without_package:
                if list.product_id.categ_id.duty_local == True:
                    count +=1
            if count > 0:
                createoff_lines=[]
                journal_landing_id = self.company_id.landing_cost_id
                product_landing_id = self.env['product.product'].search([('default_code','=','001')])
                pick_id = self.env['stock.landed.cost'].search([('picking_ids','in',self.id)])
                
                if not pick_id:
                    if journal_landing_id and product_landing_id:
                        createoff_lines.append({
                            
                                'product_id': product_landing_id.id,
                                'name':product_landing_id.name,
                                'account_id':product_landing_id.property_account_expense_id.id or False,
                                'price_unit': 0.0,
                                'split_method':'equal',
                                })
                        landed_cost_id = self.env['stock.landed.cost'].create({
                                    'date': current_date,
                                    'account_journal_id': journal_landing_id.id,
                                    'picking_ids': [(4, self.id)],
                                    'cost_lines': [(0, 0, line) for line in createoff_lines],
                                    })
                    
        if self.partner_id.segment_master_id.code == 'overseas':
            count=0
            for list in self.move_ids_without_package:
                if list.product_id.categ_id.duty_overseas == True:
                    count +=1
            if count > 0:
                createoff_lines=[]
                journal_landing_id = self.company_id.landing_cost_id
                product_landing_id = self.env['product.product'].search([('default_code','=','001')])
                pick_id = self.env['stock.landed.cost'].search([('picking_ids','in',self.id)])
                if not pick_id:
                    if journal_landing_id and product_landing_id:
                        createoff_lines.append({
                            
                                'product_id': product_landing_id.id,
                                'name':product_landing_id.name,
                                'account_id':product_landing_id.property_account_expense_id.id or False,
                                'price_unit': 0.0,
                                'split_method':'equal',
                                })
                        landed_cost_id = self.env['stock.landed.cost'].create({
                                    'date': current_date,
                                    'account_journal_id': journal_landing_id.id,
                                    'picking_ids': [(4, self.id)],
                                    'cost_lines': [(0, 0, line) for line in createoff_lines],
                                    })            
                
        return result
    
class StockRule(models.Model):
    _inherit = 'stock.rule'    
    
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'pull' or 'pull_push') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        source_location_order_id = self.env['sale.order'].search([('name','=',origin)])
        product_location_id = self.env['product.product'].search([('id','=',product_id.id)])
        
        location_bonded_id = ''
        if source_location_order_id.segment_master_id.code == 'local':
            if product_location_id.categ_id.wh_loaction_local_id:
                location_bonded_id = product_location_id.categ_id.wh_loaction_local_id
                 
        if source_location_order_id.segment_master_id.code == 'overseas':
            if product_location_id.categ_id.wh_loaction_overseas_id:
                location_bonded_id = product_location_id.categ_id.wh_loaction_overseas_id
                     
        if not location_bonded_id:
            location_bonded_id = self.location_src_id
   
        date_expected = fields.Datetime.to_string(
            fields.Datetime.from_string(values['date_planned']) - relativedelta(days=self.delay or 0)
        )
        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        qty_left = product_qty
        move_values = {
            'name': name[:2000],
            'company_id': self.company_id.id or self.location_src_id.company_id.id or self.location_id.company_id.id or values['company_id'].id,
            'product_id': product_id.id,
            'product_uom': product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': self.partner_address_id.id or (values.get('group_id', False) and values['group_id'].partner_id.id) or False,
            'location_id': location_bonded_id.id,
            'location_dest_id': location_id.id,
            'move_dest_ids': values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or [],
            'rule_id': self.id,
            'procure_method': self.procure_method,
            'origin': origin,
            'picking_type_id': self.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
            'warehouse_id': self.propagate_warehouse_id.id or self.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate': self.propagate,
            'priority': values.get('priority', "1"),
        }
        for field in self._get_custom_move_fields():
            if field in values:
                move_values[field] = values.get(field)
        return move_values
    
    
    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, values, bom):
        
        sale_order_id = self.env['sale.order'].search([('name','=',origin)])
        
        location_src_dest_id = ''
        if sale_order_id.segment_master_id.code == 'overseas':
            if product_id.categ_id.wh_loaction_overseas_id:
                location_src_dest_id = product_id.categ_id.wh_loaction_overseas_id.id
                
        if sale_order_id.segment_master_id.code == 'local':
            if product_id.categ_id.wh_loaction_local_id:
                location_src_dest_id  = product_id.categ_id.wh_loaction_local_id.id
        
        if not location_src_dest_id:
            location_src_dest_id = self.location_src_id.id or self.picking_type_id.default_location_src_id.id or location_id.id     
        
        return {
            'origin': origin,
            'product_id': product_id.id,
            'product_qty': product_qty,
            'product_uom_id': product_uom.id,
            'location_src_id': location_src_dest_id,
            'location_dest_id': location_src_dest_id,
            'customer_po_no': sale_order_id.customer_po_no or False,
            'bom_id': bom.id,
            'date_planned_start': fields.Datetime.to_string(self._get_date_planned(product_id, values)),
            'date_planned_finished': values['date_planned'],
            'procurement_group_id': False,
            'propagate': self.propagate,
            'picking_type_id': self.picking_type_id.id or values['warehouse_id'].manu_type_id.id,
            'company_id': values['company_id'].id,
            'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
            'segment_master_id': sale_order_id.segment_master_id.id or False,       
        }
    
class StockMove(models.Model):
    _inherit = "stock.move" 
    
    is_landing = fields.Boolean('LC')
 

