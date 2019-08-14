# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'DO Report',
    'version': '12.0',
    'category': 'Inventory',
    'description': """
    DO Report
    """,
    'website': 'https://www.pptssolutions.com',
    'depends': ['stock','account_tax_code'],
    'data': [
        'report/do_report.xml',
        'report/do_report_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
