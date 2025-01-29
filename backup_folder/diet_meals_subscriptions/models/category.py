# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class DietCategory(models.Model):
    _name = 'diet.category'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'category for diet'

    name = fields.Char("Name", translate=True)
    description = fields.Text("Description", translate=True)
    parent = fields.Many2one('diet.category', string="Parent Category")
    color = fields.Integer()
    image = fields.Binary()
