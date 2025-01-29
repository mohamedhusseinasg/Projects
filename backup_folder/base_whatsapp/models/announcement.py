# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

from odoo.tools.mimetypes import guess_mimetype
import mimetypes

import time
import urllib
from urllib.request import Request, urlopen
import json
import requests
import base64
import codecs


from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import format_datetime


class WhatsappAnnouncement(models.Model):
    _name = 'base.whatsapp.announcement'
    _description = 'whatsapp Announcement'
    _rec_name = 'message'

    READONLY_STATES = {'sent': [('readonly', True)]}

    date = fields.Date(string='Date', states=READONLY_STATES)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'), 
    ], string='Status', copy=False, default='draft', states=READONLY_STATES)
    partner_ids = fields.Many2many("res.partner", "whatsapp_partner_announement_rel", "partner_id", "announcement_id", "Contacts", states=READONLY_STATES)
    template_id = fields.Many2one("base.whatsapp.template", "Template", states=READONLY_STATES)
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id.id, states=READONLY_STATES)

    message = fields.Text(string='Message')
    file = fields.Binary(string='File')
    file_name = fields.Char(string='File Name')
    file_url = fields.Char(string='File URL')
    message_type = fields.Selection([
        ('message', 'Message'),
        ('file', 'File'),
        ('file_url', 'File URL'),
        ('link', 'Link'),
    ], string='Message Type', default='message' , required=True)
    mimetype = fields.Char('Mime Type')
    link = fields.Char('Link')

    def _check_contents(self, values):
        mimetype = None
        if values.get('mimetype'):
            mimetype = values['mimetype']
        if not mimetype and values.get('file_name'):
            mimetype = mimetypes.guess_type(values['file_name'])[0]
        if values.get('file') and (not mimetype or mimetype == 'application/octet-stream'):
            mimetype = guess_mimetype(values['file'].decode('base64'))
        if not mimetype:
            mimetype = 'application/octet-stream'

        values['mimetype'] = mimetype
        xml_like = 'ht' in mimetype or 'xml' in mimetype # hta, html, xhtml, etc.
        force_text = (xml_like and (not self.env.user._is_admin() or
            self.env.context.get('attachments_mime_plainxml')))
        if force_text:
            values['mimetype'] = 'text/plain'
        return values

    @api.model
    def create(self, values):
        values = self._check_contents(values)
        return super(WhatsappAnnouncement, self).create(values)

    def write(self, vals):
        if 'mimetype' in vals or 'file' in vals:
            vals = self._check_contents(vals)
        return super(WhatsappAnnouncement, self).write(vals)

    @api.onchange('template_id')
    def onchange_template(self):
        if self.template_id:
            self.message_type = self.template_id.message_type
            self.message = self.template_id.message
            self.file = self.template_id.file
            self.file_name = self.template_id.file_name
            self.file_url = self.template_id.file_url
            self.link = self.template_id.link
            self.mimetype = self.template_id.mimetype
            self.partner_ids = [(6, 0, self.template_id.partner_ids.ids + self.partner_ids.ids)]

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft'):
                raise UserError(_('You cannot delete an record which is not draft.'))
        return super(Announcement, self).unlink()

    def send_message(self):
        for partner in self.partner_ids:
            if partner.mobile:
                if self.message_type == 'message':
                    partner.with_context(force_send=True).send_whatsapp(self.message, partner.mobile.replace("+", "").replace(" ", ""), partner)
                elif self.message_type == 'file':
                    partner.with_context(force_send=True).send_whatsapp_file(self.file, self.file_name, partner.mobile.replace("+", "").replace(" ", ""), partner)
                elif self.message_type == 'file_url':
                    partner.with_context(force_send=True).send_whatsapp_file_url(self.file_url, partner.mobile.replace("+", "").replace(" ", ""), partner)
                elif self.message_type == 'link':
                    partner.with_context(force_send=True).send_whatsapp(self.link, partner.mobile.replace("+", "").replace(" ", ""), partner)
            else:
                raise UserError(_("Please Check Mobile Field"))

        self.state = 'sent'
        self.date = fields.Datetime.now()