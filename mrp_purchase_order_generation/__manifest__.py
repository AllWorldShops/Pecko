# -*- coding: utf-8 -*-

{
    'name': 'MRP Purchase Order Generation',
    'version': '12.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': 'https://www.pptssolutions.com',
    'category': 'Manufacturing',
    'description': """Generate purchase Order from MRP""",
    'depends': ['mrp','purchase'],
    'data': [
        'views/mrp_production_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
