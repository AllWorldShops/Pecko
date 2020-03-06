from odoo import api, fields, models, tools, _

class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    stock_decrease_account = fields.Many2one('account.account',string='Stock Decrease Account')
    stock_increase_account = fields.Many2one('account.account',string='Stock Increase Account')
    

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.multi
    def _get_product_accounts(self):
        accounts = super(ProductTemplate, self)._get_product_accounts()
        res = self._get_asset_accounts()
        accounts.update({
            'stock_input': self.categ_id.stock_increase_account or res['stock_input'] or self.property_stock_account_input or self.categ_id.property_stock_account_input_categ_id,
            'stock_output': self.categ_id.stock_decrease_account or res['stock_output'] or self.property_stock_account_output or self.categ_id.property_stock_account_output_categ_id,
            'stock_valuation': self.categ_id.property_stock_valuation_account_id or False,
        })
        return accounts