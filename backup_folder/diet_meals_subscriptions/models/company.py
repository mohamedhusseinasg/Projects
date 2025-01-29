# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    wa_diet_meals_subscriptions_start_message = fields.Text(default="""'Dear ' + object.partner_id.name + ', Your Subscriptions No. is: ' + object.name + ' in Diet Meals.'""")
    wa_diet_meals_subscriptions_end_message = fields.Text(default="""'Dear ' + object.partner_id.name + ', Your Subscriptions end in ' + object.end_date + ' .'""")
