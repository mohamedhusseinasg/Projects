# -*- encoding: utf-8 -*-
from odoo import models, fields, api,_
from datetime import date, datetime, timedelta as td
from odoo.exceptions import UserError

class BaseWhatsappHistory(models.TransientModel):
    _name = "base.whatsapp.history"
    _description = "WhatsApp Chat History"

    data =  fields.Html(string='WhatsApp Chat')