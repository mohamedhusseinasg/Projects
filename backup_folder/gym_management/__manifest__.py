{

    'name': 'GYM Management',
    'version': '1.0.0',
    'author': 'mohamed',
    'sequence': -112,
    'website': 'www.proengmht.com',
    'category': 'gym',
    'summary': 'gym Management System',
    'description': """gym Management System """,
    'demo': [],
    'depends': ['base'],

    'data': ['security/ir.model.access.csv',
             'views/customer.xml',
             'views/customer_view.xml',
             'views/trainer_view.xml',

             ],

    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',

}
