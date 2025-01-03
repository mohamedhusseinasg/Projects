# -*- coding: utf-8 -*-
{
    'name': "Github Cloner",

    'summary': """
        Github integration to clone repository from github with ease
        Just push your code and let this module handle the rest
        Cloning your code changes and restart odoo service for you
        """,

    'description': """
        With this module you can add your repositories to odoo to clone its content with every push 
        and copy it to your addons directory then restart your odoo service
    """,

    'author': "DXEG.NET",
    'website': "https://dxeg.net",

    'category': 'Technical',
    'version': '17.231109',

    # any module necessary for this one to work correctly
    'depends': ['mail'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/github_view.xml',
        'views/res_config_views.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/images/banner.gif'],
    'price': 70.00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://youtu.be/rNHAcYzhcrA',
    'license': 'OPL-1',
    'application': True,
}
