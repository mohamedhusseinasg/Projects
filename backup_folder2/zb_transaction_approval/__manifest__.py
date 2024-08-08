{
    'name': 'Transaction Approval',
    'version': '17.0.0.1',
    'category': 'All',
    'summary': """Approval functionality in Sales Order, Purchase Order, Accounting Entries, Payments.""",
    'description': """
        Approval functionality in
        - Sales Order
        - Purchase Order
        - Accounting Entries
        - Payments.
    """,
    'author': 'ZestyBeanz Technologies',
    'maintainer': 'ZestyBeanz Technologies',
    'support': 'support@zbeanztech.com',
    'website': 'http://www.zbeanztech.com/',
    'license': 'LGPL-3',
    'icon': "/zb_transaction_aproval/static/description/icon.png",
    'images': ['static/description/banners/banner.png',],
    'currency': 'USD',
    'price': 0.0,
    'depends': [
        'purchase', 'sale_management'
    ],
    'data': [
      'security/security.xml',
      'data/mail_template_approval.xml',
      'data/mail_template_purchase_approval.xml',
      'data/mail_template_invoice_approval.xml',
      'data/mail_template_payment_approval.xml',
      'views/sale_order_view.xml',
      'views/purchase_order_view.xml',
      'views/account_move_view.xml',
      'views/account_payment_view.xml',
      'views/res_config_settings_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
