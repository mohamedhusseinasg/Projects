# -*- coding: utf-8 -*-
from modulefinder import Module
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import json
import requests
import base64
import re

class QrCode(models.Model):
    _name = "qr.code.generate"

    state = fields.Char()
    qr_code = fields.Binary()
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id.id)

    def generate_qr_code(self):
        url = '%s/%s/start-session' % (self.company_id.whatsapp_api_url, self.company_id.whatsapp_api_instance)
        payload = {}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % (self.company_id.whatsapp_api_token)
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if data['status']:
            self.state = data['status']
        if 	data['status']=='QRCODE':
            if data['qrcode']:
                qrcode = data["qrcode"]
                qrcode = (qrcode.split(",",1)[1])
                qrcode = bytes(qrcode, encoding='utf-8')
                self.qr_code =(qrcode)
        else: 
            pass