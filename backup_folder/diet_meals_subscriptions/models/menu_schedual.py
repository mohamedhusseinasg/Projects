from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime , timedelta , date
from dateutil.relativedelta import relativedelta


class MenuSchedual(models.Model):
    _name = 'menu.schedual'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'ksc.mixin','base.whatsapp.mixin']
    _description = 'Menu Schedual'
    
    name = fields.Char(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    categ_ids = fields.Many2many('diet.category', required=True)
    lines_count = fields.Integer(compute='_compute_lines_count')
    schedual_line_ids = fields.One2many('menu.schedual.line', 'menu_id', copy=False,)

    
    @api.depends('schedual_line_ids')
    def _compute_lines_count(self):
        for rec in self:
            rec.lines_count = len(rec.schedual_line_ids)

    def action_create_lines_by_date(self):
        if self.start_date and self.end_date and not self.schedual_line_ids:
            date = self.start_date
            lines = []
            while date <= self.end_date:
                lines.append({
                    'menu_id':self.id,
                    'date': date,
                })
                date += relativedelta(days=1)
            if lines:
                self.env['menu.schedual.line'].create(lines)


class MenuSchedualLine(models.Model):
    _name = 'menu.schedual.line'
    _description = 'Menu Schedual Line'
    
    date = fields.Date(required=True)
    product_ids = fields.Many2many('product.product', domain="[('diet_meal_ok', '=', True),('category_ids','in',parent.categ_ids)]", required=True)
    menu_id = fields.Many2one('menu.schedual')