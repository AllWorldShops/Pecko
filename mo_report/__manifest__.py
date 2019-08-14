# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MO Report',
    'version': '12.0',
    'category': 'MRP',
    'description': """
    MO Report
    """,
    'website': 'https://www.pptssolutions.com',
    'depends': ['stock','account_tax_code','custom_mrp'],
    'data': [
        'report/mo_report.xml',
        'report/mo_report_templates.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
