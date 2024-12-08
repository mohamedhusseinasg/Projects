# -*- encoding: utf-8 -*-
import json
import time
import uuid
from datetime import datetime

import requests
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import html_escape
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def get_whatsapp_webhook(self):
        return "%s/whatsapp/webhook" % (
            self.env["ir.config_parameter"].get_param("web.base.url")
        )

    whatsapp_api_url = fields.Char(
        string="WhatsApp URl with PORT", default="http://178.62.17.94:21465/api"
    )
    whatsapp_api_instance = fields.Char(string="Session")
    whatsapp_api_token = fields.Char(string="Token")
    whatsapp_api_authentication = fields.Boolean("Authentication")
    daily_message_number = fields.Integer("Daily Message Number")
    message_counter = fields.Integer("Message Sent", compute="_counter_of_message")
    whatsapp_secret_key = fields.Char()
    whatsapp_webhook = fields.Char(
        string="Webhook", default=lambda self: self.get_whatsapp_webhook()
    )
    whatsapp_partner_manager_id = fields.Many2one("res.partner")
    whatsapp_state = fields.Char(default="NOT CONNECT")
    wa_run_sub_message = fields.Text("Run Subscription Message",
        default="""'Dear ' + self.partner_id.name + 'your subscription run and' + ', Your Registration No. is: ' + self.partner_id.id""")
    

    def _counter_of_message(self):
        count_message = self.env['base.whatsapp.message'].search_count(
            [
                ("create_date", ">=", datetime.now().strftime("%Y-%m-%d 00:00:00")),
                ("create_date", "<=", datetime.now().strftime("%Y-%m-%d 23:23:59")),
                ("state", "=", "sent"),
            ]
        )
        for rec in self:
            rec.message_counter = count_message

    def get_session(self):
        if not self.whatsapp_api_instance:
            self.whatsapp_api_instance = uuid.uuid4()
        return self.whatsapp_api_instance

    def action_generate_token(self):
        session = self.get_session()
        URL = "{base_url}/{session}/{secret_key}/generate-token".format(
            base_url=self.whatsapp_api_url,
            session=session,
            secret_key=self.whatsapp_secret_key,
        )
        headers = {
            "Content-type": "application/json",
        }
        reply = requests.post(URL, headers=headers)
        result = reply.json() or {}
        print("\n \n result: ", result)
        if result.get("status", "error") == "success":
            self.whatsapp_api_token = result.get("token")
        elif (
            "response" in result and result["response"] == False and "message" in result
        ):
            raise UserError(_("whatsapp generate token fail! %s") % (result["message"]))
        else:
            raise UserError(_("whatsapp generate token fail!"))

    def update_whatsapp_state(self, result):
        state = "NOT CONNECT"
        if result == "CLOSED":
            state = "CLOSED"
        elif result.get("status") == "INITIALIZING" and result.get("urlcode"):
            state = "INITIALIZED"
        else:
            state = result.get("status") if result.get("status") else "ERROR"
        return state

    def action_whatsapp_get_qrcode(self):
        if not self.whatsapp_api_token:
            raise UserError(_("do generate token first!"))
        session = self.get_session()
        URL = "{base_url}/{session}/start-session".format(
            base_url=self.whatsapp_api_url, session=session
        )
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer %s" % self.whatsapp_api_token,
        }
        data = {
            "webhook": self.whatsapp_webhook,
            "waitQrCode": True,
        }
        reply = requests.post(URL, data=json.dumps(data), headers=headers)
        result = reply.json() or {}
        print("\n \n result: ", result)
        self.whatsapp_state = self.update_whatsapp_state(result)
        if result.get("status") == "QRCODE" and result.get("qrcode"):
            return {
                "name": _("Scan QRcode"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "qrcode.wizard",
                "context": {
                    "qrcode": result.get("qrcode").replace(
                        "data:image/png;base64,", ""
                    ),
                    "default_company_id": self.id,
                },
                "target": "new",
            }
        # raise UserError(_("whatsapp opene session fail!"))

    def action_whatsapp_close_session(self):
        if not self.whatsapp_api_token:
            raise UserError(_("do generate token first!"))
        session = self.get_session()
        URL = "{base_url}/{session}/close-session".format(
            base_url=self.whatsapp_api_url, session=session
        )
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer %s" % self.whatsapp_api_token,
        }
        reply = requests.post(URL, headers=headers)
        result = reply.json() or {}
        print("\n \n result: ", result)
        if result.get("status"):
            self.whatsapp_state = self.update_whatsapp_state("CLOSED")

    def action_whatsapp_get_session_info(self):
        if not self.whatsapp_api_token:
            raise UserError(_("do generate token first!"))
        session = self.get_session()
        URL = "{base_url}/{session}/status-session".format(
            base_url=self.whatsapp_api_url, session=session
        )
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer %s" % self.whatsapp_api_token,
        }
        reply = requests.get(URL, headers=headers)
        result = reply.json() or {}
        self.whatsapp_state = self.update_whatsapp_state(result)
        print("\n \n result: ", result)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
