# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Stock',
    'version': '12.0',
    'category': 'Stock',
    'description': """
    Enhancement in inventory module
    """,
    'website': 'https://www.pptssolutions.com',
    'depends': ['stock','sale_stock'],
    'data': [
        'views/stock_view.xml',
        'wizard/stock_move_notes.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
