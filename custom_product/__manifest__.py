# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Product',
    'version': '12.0',
    'category': 'Product',
    'description': """
    Enhancement in Product module
    """,
    'website': 'https://www.pptssolutions.com',
    'depends': ['product','mrp','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_manufacturer_view.xml',
        'views/product_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
