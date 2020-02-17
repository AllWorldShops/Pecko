# -*- coding: utf-8 -*-

{
    'name' : 'Segment Master',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Sale',
    'description': """""",
    'depends' : ['base','sale','purchase',],
    'data': [
        'data/segment_default.xml',
        'security/ir.model.access.csv',
        'views/segment_master_views.xml',
        'views/res_partner_views.xml',
        'views/sale_views.xml',
        'views/purchase_order_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application':True
}