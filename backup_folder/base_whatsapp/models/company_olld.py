# -*- encoding: utf-8 -*-
from email import message
from odoo import api, fields, models, _
from datetime import datetime


class ResCompany(models.Model):
    _inherit = 'res.company'

    whatsapp_api_url = fields.Char(string='WhatsApp API URL')
    whatsapp_api_instance = fields.Char(string='Session')
    whatsapp_api_token = fields.Char(string='Token')
    whatsapp_api_authentication = fields.Boolean("Authentication")
    daily_message_number = fields.Integer("Daily Message Number")
    message_counter = fields.Integer(
        "Message Sent", compute="_counter_of_message")
    wa_run_sub_message = fields.Text("Run Subscription Message",
        default="""'Dear ' + self.partner_id.name + 'your subscription run and' + ', Your Registration No. is: ' + self.partner_id.id""")
    

    def _counter_of_message(self):
        count_message = self.env['base.whatsapp.message'].search_count([('create_date', '>=', datetime.now().strftime(
            '%Y-%m-%d 00:00:00')), ('create_date', '<=', datetime.now().strftime('%Y-%m-%d 23:23:59')), ('state', '=', 'sent')])
        for rec in self:
            rec.message_counter = count_message
