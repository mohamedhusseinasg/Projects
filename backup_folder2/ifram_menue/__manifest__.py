# -*- coding: utf-8 -*-
{
    'name': "ifram_menue",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "ASG Team",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        # 'views/res_user.xml',

    ],

    'assets': {
        'web.assets_backend': [
            'ifram_menue/static/src/js/iframe_content_template.js',
        ],
    },
    
    
}
