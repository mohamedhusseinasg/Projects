# -*- coding: utf-8 -*-
#╔══════════════════════════════════════════════════════════════════════╗
#║                                                                      ║
#║                  ╔═══╦╗       ╔╗  ╔╗     ╔═══╦═══╗                   ║
#║                  ║╔═╗║║       ║║ ╔╝╚╗    ║╔═╗║╔═╗║                   ║
#║                  ║║ ║║║╔╗╔╦╦══╣╚═╬╗╔╬╗ ╔╗║║ ╚╣╚══╗                   ║
#║                  ║╚═╝║║║╚╝╠╣╔╗║╔╗║║║║║ ║║║║ ╔╬══╗║                   ║
#║                  ║╔═╗║╚╣║║║║╚╝║║║║║╚╣╚═╝║║╚═╝║╚═╝║                   ║
#║                  ╚╝ ╚╩═╩╩╩╩╩═╗╠╝╚╝╚═╩═╗╔╝╚═══╩═══╝                   ║
#║                            ╔═╝║     ╔═╝║                             ║
#║                            ╚══╝     ╚══╝                             ║
#║                  SOFTWARE DEVELOPED AND SUPPORTED BY                 ║
#║                ALMIGHTY CONSULTING SOLUTIONS PVT. LTD.               ║
#║                      COPYRIGHT (C) 2016 - TODAY                      ║
#║                      https://www.almightycs.com                      ║
#║                                                                      ║
#╚══════════════════════════════════════════════════════════════════════╝
{
    'name' : 'WhatsApp Integration gym',
    'summary': 'Odoo WhatsApp Integration to send Watsapp messages from Odoo.',
    'category' : 'Extra-Addons',
    'version': '1.0.3',
    'depends' : ['base_setup', 'mail', 'web'],
    'author': 'Almighty Consulting Solutions Pvt. Ltd.',
    'website': 'www.almightycs.com',
    'description': """
        Odoo WhatsApp Integration to send Watsapp messages from Odoo. Notification WhatsApp to customer or users, base hms
    """,
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "wizard/create_whatsapp_message_view.xml",
        "wizard/whatsapp_messages_view.xml",
        "views/data.xml",
        # "views/assets.xml",
        "views/message_view.xml",
        "views/partner_view.xml",
        "views/company_view.xml",
        "views/announcement_view.xml",
        "views/qr_code.xml",
        "views/menu_item.xml",
    ],
      'assets': {
    'web.assets_backend': [
        '/base_whatsapp/static/src/scss/custom_backend.scss',
    ],
},
    'installable': True,
    'application': False,
}