# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Account',
    'version': '12.0',
    'category': 'Account',
    'description': """
    Enhancement in Account module
    """,
    'website': 'https://www.pptssolutions.com',
    'depends': ['account','custom_product'],
    'data': [
        'views/account_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
