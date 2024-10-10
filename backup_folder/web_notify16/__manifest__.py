
{
    "name": "Web Notify",
    "summary": """
        Send notification messages to user""",
    "version": "17.0.2.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV," "AdaptiveCity," "Odoo Community Association (OCA)",
    "development_status": "Production/Stable",
    "website": "https://github.com/OCA/web",
    "depends": ["web", "bus", "base", "mail"],
    "assets": {
        "web.assets_backend": [
            "web_notify16/static/src/js/services/notification.esm.js",
            "web_notify16/static/src/js/services/notification_services_esm.js",
        ]
    },
    "demo": ["views/res_users_demo.xml"],
    "installable": True,
}
