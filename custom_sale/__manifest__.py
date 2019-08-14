# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Sale',
    'version': '12.0',
    'category': 'Sale',
    'description': """
    Enhancement in Sale module
    """,
    'website': 'https://www.pptssolutions.com',
    'depends': ['sale','custom_product'],
    'data': [
        'views/sale_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
