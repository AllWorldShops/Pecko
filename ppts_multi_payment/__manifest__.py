{
    'name': 'Account Multi Payments',
    'version': '11.0',
    'description': 'Bulk payments for invoice',
    'category': 'Account Invoice',
    'author': 'PPTS [India] Pvt.Ltd.',
    'website': "http://www.pptssolutions.com",
    'sequence': 10,
    'depends': ['base','account','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_payment_view.xml',
        'views/vendor_payment_view.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
