# -*- coding: utf-8 -*-

{
    'name' : 'for-ex gain | Loss',
    'version' : '1.0',
    'author' : 'PPTS [India] Pvt.Ltd.',
    'sequence': 112,
    'category': 'Account',
    'website' : 'http://www.pptssolutions.com',
    'license': 'LGPL-3',
    'support': 'business@pptservices.com',
    'description' : """ This module manage for-ex gain | Loss value in Invoice (Sales& Purchase). """,
    'depends' : ['account','account_accountant'],
    'data' : [
                'views/account_config_view.xml',
             ],  
    'installable' : True,
    'application' : True,
    'auto_install': False,
}
