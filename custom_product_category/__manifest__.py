# -*- coding: utf-8 -*-

{
    'name': 'Custom Product Category',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Product',
    'description': """Enhancement in Product module""",
    'depends': ['product','base_setup','base','stock_landed_costs','purchase','account','purchase_stock','stock','sale','mrp','segment_master'],
    'data': [
        'views/product_category_view.xml',
        'views/custom_purchase_order.xml',
        'views/custom_journal.xml',
        'views/custom_stock_picking.xml',
        'views/custom_mrp_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
