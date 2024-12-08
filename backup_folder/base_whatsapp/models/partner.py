# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'base.whatsapp.mixin']

    def _count_whatsapp(self):
        for rec in self:
            rec.whatsapp_count = len(rec.whatsapp_ids.ids)

    whatsapp_ids = fields.One2many(
        'base.whatsapp.message', 'partner_id', string='whatsapp')
    whatsapp_count = fields.Integer(
        compute="_count_whatsapp", string="#whatsapp Count")
    wa_subscription_reg_message = fields.Text("Subscription ID Message", readonly=True,
                                         default="""'Dear ' + res.name + ', Your Subscription No. is: *' , res.id , 'رقم الأشتراك'""")

    def send_id_message(self):
        message_env = self.env['base.whatsapp.message']
        for res in self:
            messaghe_dx = res.wa_subscription_reg_message
            send = eval(messaghe_dx)
            message_id =  self.env['base.whatsapp.message'].create(
                {
                    'partner_id': res.id,
                    'message_type': 'message',
                    'message': send,
                    "mobile": res.mobile.replace("+", "").replace(" ", ""),
                }
            )
            message_id.send_whatsapp_message()

