# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Aged Filter Report',
    'category': 'Accounting',
    'sequence': 144,
    'website': "http://www.pptssolutions.com",
    'author': "PPTS India Pvt Ltd",
    'summary': 'Aged Filter Report',
    'version': '1.0',
    'description': """
Aged Filter Report
        """,
    'depends': ['base','account','account_reports'],
    'data': [
        'wizard/account_aged_payable_view.xml',
        'wizard/account_aged_receivable_view.xml',
        ],
    'installable': True,
    'application': True,
}
