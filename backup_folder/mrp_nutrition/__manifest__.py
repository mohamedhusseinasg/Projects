# -*- coding: utf-8 -*-
{
    'name': 'Manufacturing Nutrition Facts',
    'summary': "Nutrition Facts via BoM",
    'category': 'Manufacturing',
    "version": "17.0",
    "sequence": 10,
    "author": "Remon Salem",
    "website": "https://github.com/remonSalem",
    "license": 'AGPL-3',
    'depends': ['mrp', 'product_nutrition'],
    'data': [
        'data/ir_actions_server.xml',
        'views/product.xml',
    ],
    'installable': True,
    'auto_install': False,
}
