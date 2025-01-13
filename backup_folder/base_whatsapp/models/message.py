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

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import format_datetime

class BaseWhatsAppMessage(models.Model):
    _name = 'base.whatsapp.message'
    _description = 'whatsapp'
    _order = 'id desc'

    READONLY_STATES = {'sent': [('readonly', True)], 'error': [('readonly', True)]}

    @api.depends('file_name','message','message_type')
    def _get_name(self):
        for rec in self:
            if rec.message and rec.message_type=='message':
                if len(rec.message)>100:
                    rec.name = rec.message[:100]
                else:
                    rec.name = rec.message or 'Message'
            elif rec.message_type in ['file','file_url']:
                name = "File"
            elif rec.message_type=='link':
                name = "Link"
            else:
                name = rec.file_name or 'Message'

    name = fields.Char(string="Name", compute="_get_name", store=True)
    partner_id = fields.Many2one('res.partner', 'Contact', states=READONLY_STATES)
    file =  fields.Binary(string='File', states=READONLY_STATES)
    file_name =  fields.Char(string='File Name')
    file_url =  fields.Char(string='File URL')
    message =  fields.Text(string='WhatsApp Text', states=READONLY_STATES)
    mobile =  fields.Char(string='Destination Number', required=True, states=READONLY_STATES)
    state =  fields.Selection([
        ('draft', 'Queued'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ], string='Message Status', index=True, default='draft', states=READONLY_STATES)
    message_type =  fields.Selection([
        ('message', 'Message'),
        ('file', 'File'),
        ('link', 'Link'),
    ], string='Message Type', default='message', states=READONLY_STATES)
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id.id, states=READONLY_STATES)
    error_message = fields.Char("Error Message", states=READONLY_STATES)
    template_id = fields.Many2one("base.whatsapp.template", string="Template", states=READONLY_STATES)
    whatsapp_announcement_id = fields.Many2one("base.whatsapp.announcement", string="Announcement", states=READONLY_STATES)
    reply_data = fields.Text(copy=False, states=READONLY_STATES)
    mimetype = fields.Char('Mime Type', readonly=True, states=READONLY_STATES)
    link = fields.Char('Link', states=READONLY_STATES)
    caption = fields.Text('Caption Text', states=READONLY_STATES)
    daily_message = fields.Integer(related='company_id.daily_message_number')
 
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
        return super(BaseWhatsAppMessage, self).create(values)

    def write(self, vals):
        if 'mimetype' in vals or 'file' in vals:
            vals = self._check_contents(vals)
        return super(BaseWhatsAppMessage, self).write(vals)

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

    def action_draft(self):
        self.state = 'draft'

    @api.model
    def complete_queue(self):
        records = self.search([('state', '=', 'draft')], limit=100)
        records.send_whatsapp_message()

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id and self.partner_id.mobile:
            self.mobile = self.partner_id.mobile.replace("+", "").replace(" ", "")
    
    def check_connection(self):
        URL = "%s/%s/check-connection-session" % (self.company_id.whatsapp_api_url, self.company_id.whatsapp_api_instance)
        headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer %s" % (self.company_id.whatsapp_api_token)
                }
        try:
            reply = requests.get(URL, headers=headers, stream=True, timeout=3)
            reply_data = reply.json()
            if reply_data['message'] == 'Connected':
                return True
            elif reply_data['message'] == 'Disconnected':
                return False
        except Exception as e:
            pass
    
    def resend_message(self):
        mobile = "+" + self.mobile
        self.mobile = mobile
        self.reply_data = ''
        self.send_whatsapp_message()

    def send_whatsapp_message(self):
        count = self.search_count([('create_date', '>=', datetime.now().strftime(
            '%Y-%m-%d 00:00:00')), ('create_date', '<=', datetime.now().strftime('%Y-%m-%d 23:23:59')), ('state', '=', 'sent')])
        for rec in self:
            if rec.check_connection():
                if count < rec.daily_message:
                    try:
                        if rec.message_type == 'message':
                            URL = "%s/%s/send-message" % (
                                rec.company_id.whatsapp_api_url, rec.company_id.whatsapp_api_instance)
                            message = {
                                "phone": rec.mobile,
                                "message": rec.message,
                            }
                        elif rec.message_type in ['file', 'file_url']:
                            URL = "%s/%s/send-file-base64" % (
                                rec.company_id.whatsapp_api_url, rec.company_id.whatsapp_api_instance)
                            if rec.message_type == 'file_url':
                                file_body = rec.file_url

                                filename = rec.file_url.split('/')[-1].split('.')[0]
                                file_ext = '.' + rec.file_url.split('.')[-1]
                                file_name = filename + file_ext
                            else:
                                file_body = "data:" + rec.mimetype + \
                                    ";base64," + (rec.file).decode('utf-8')
                                file_name = rec.file_name
                            message = {
                                "phone": rec.mobile,
                                "base64": file_body,
                            }

                        else:
                            URL = "%s/%s/send-link-preview" % (
                                rec.company_id.whatsapp_api_url, rec.company_id.whatsapp_api_instance)
                            message = {
                                "caption": rec.caption,
                                "phone": rec.mobile,
                                "url": rec.link,
                            }

                        headers = {
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "Authorization": "Bearer %s" % (rec.company_id.whatsapp_api_token)
                        }
                        reply = requests.post(URL, data=json.dumps(message), headers=headers)
                        if rec.message_type == 'message':
                            reply_data = reply.json()
                            if reply_data.get('error'):
                                rec.state = 'error'
                            # elif reply_data['status'] == 'Disconnected':
                            #     rec.resend_message()
                            else:
                                rec.state = 'sent'
                            rec.reply_data = reply_data
                        else:
                            rec.reply_data = reply
                            if reply.status_code == 200:
                                rec.state = 'sent'
                            elif reply.status_code == 201:
                                rec.state = 'sent'
                            else:
                                rec.state = 'error'
                        rec.env.user.notify_success(_('Your Messages Sent'))
                    except Exception as e:
                        rec.state = 'error'
                        rec.error_message = e
                else:
                    rec.env.user.notify_warning(_('Your Sent Messages Exceed Today Limit'))
            else:
                rec.env.user.notify_danger(_("Message Not Send Due To Your Phone Connection"))

class BasewhatsappMixin(models.AbstractModel):
    _name = "base.whatsapp.mixin"
    _description = "WhatsApp Mixin"

    @api.model
    def send_whatsapp(self, message, mobile, partner=False):
        company_id = self._context.get('force_company')
        if not company_id:
            company_id = self.env.user.sudo().company_id.id
        record = self.env['base.whatsapp.message'].create({
            'message': message,
            'partner_id': partner and partner.id or False,
            'mobile': mobile,
            'message_type': 'message',
            'company_id': company_id,
        })
        if self.env.context.get('force_send'):
            record.send_whatsapp_message()
        return record

    @api.model
    def send_whatsapp_file_url(self, file_url, mobile, partner=False):
        company_id = self._context.get('force_company')
        if not company_id:
            company_id = self.env.user.sudo().company_id.id
        record = self.env['base.whatsapp.message'].create({
            'file_url': file_url,
            'partner_id': partner and partner.id or False,
            'mobile': mobile,
            'message_type': 'file_url',
            'company_id': company_id,
        })
        if self.env.context.get('force_send'):
            record.send_whatsapp_message()
        return record

    @api.model
    def send_whatsapp_file(self, filedata, file_name, mobile, partner=False):
        company_id = self._context.get('force_company')
        if not company_id:
            company_id = self.env.user.sudo().company_id.id
        record = self.env['base.whatsapp.message'].create({
            'file': filedata,
            'file_name': file_name,
            'message_type': 'file',
            'partner_id': partner and partner.id or False,
            'mobile': mobile,
            'company_id': company_id,
        })
        if self.env.context.get('force_send'):
            record.send_whatsapp_message()
        return record

    def base_whatsapp_chat_history(self, partner, mobile):
        mobile = mobile.replace(' ', '')
        mobile = mobile.replace('+', '')
        URL = "%s/instance%s/messages?token=%s" % (self.env.user.company_id.whatsapp_api_url, self.env.user.company_id.whatsapp_api_instance,self.env.user.company_id.whatsapp_api_token) 
        message_data = {
            "chatId": mobile + '@c.us',
            "last": 100,
            "limit": 100,
        }
        try:
            reply = urlopen(URL+'&'+urllib.parse.urlencode(message_data))
            reply_data = json.loads(reply.read().decode('utf-8'))
        except Exception as e:
            raise UserError(_("Something went wrong with configuration, please contact your administrator."))

        data = ""
        for msg in reply_data.get('messages'):
            date_time = time.strftime(DTF, time.localtime(msg['time']))
            date_time = datetime.strptime(date_time, DTF)
            date_time = format_datetime(self.env, date_time, dt_format='medium')

            message = msg['body']
            if msg['type']=='location':
                lat_long = msg['body'].split(';')
                message = "https://maps.google.com/?q=%s,%s" % (lat_long[0], lat_long[1])
            
            if msg['fromMe']:
                data += _("<div class='base-right-chat'> <span>%s</span>") %(message)
                data += _("<br/><span class='pull-right base-chat-name'> %s - (%s) <span></div>")%(self.env.user.company_id.name,date_time)
            else:
                data += _("<div class='base-left-chat'> <span>%s</span>") %(message)
                data += _("<br/><span class='pull-right base-chat-name'> %s - (%s) <span></div>")%(partner.name,date_time)

            data += _("<br/>")

        wiz = self.env['base.whatsapp.history'].create({
            'data': data
        })
        action = self.env["ir.actions.actions"]._for_xml_id("base_whatsapp.action_base_whatsapp_history")
        action['res_id'] = wiz.id
        return  action


class whatsappTemplate(models.Model):
    _name = 'base.whatsapp.template'
    _description = 'whatsapp Template'

    name = fields.Text(string='Name', required=True)
    partner_ids = fields.Many2many("res.partner", "partner_whatsapp_template_rel", "partner_id", "whatsapp_template_id", "Partners")

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
    mimetype = fields.Char('Mime Type', readonly=True)
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
        return super(whatsappTemplate, self).create(values)

    def write(self, vals):
        if 'mimetype' in vals or 'file' in vals:
            vals = self._check_contents(vals)
        return super(whatsappTemplate, self).write(vals)