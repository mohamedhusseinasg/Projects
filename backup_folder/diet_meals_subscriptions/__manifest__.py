# -*- coding: utf-8 -*-
{
    'name': "diet meals subscriptions",
    'author': 'KSC kuwait System Company',
    'category': 'subscriptions',
    'summary': """diet meals subscriptions""",
    'license': 'OPL-1',
    'website': 'http://github.com/omerahmed1994',
    'description': """diet meals subscriptions""",
    'version': '17.0',
    'depends': ['base_whatsapp', 'account', 'sale', 'sale_management', 'stock'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/days.xml',

        'views/views.xml',
        'views/category.xml',
        'views/product.xml',
        'views/partner.xml',
        'views/company.xml',
        'views/packages.xml',
        'views/menu_schedual.xml',
        'views/kitchen_view.xml',
        # 'views/assets.xml',
        'wizard/freeze_wizard.xml',

        'views/menuitem.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'diet_meals_subscriptions/static/src/js/datepicker.js',
    #     ],
    # },
    'installable': True,
    'application': True,
    'auto_install': False,
}
