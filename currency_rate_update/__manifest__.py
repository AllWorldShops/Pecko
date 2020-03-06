# -*- encoding: utf-8 -*-
{
    'name': 'Currency Rate Update',
    "website": "http://www.pptssolutions.com",
    'version': '11.0.0',

    'category': 'Accounting',
    'sequence': 65,
    'summary': 'Currency Rate Update',
    'description': "Currency Rate Update",
    
    'depends': ['base','account'],
    'data': [
            'wizard/currency_rate_update_wizard.xml',
            'views/account_invoice_view.xml',
            ],
    'license': 'LGPL-3',
    
    'installable': True,
    'auto_install': False,
    'application': True,

}
