from odoo import _, api, fields, models
from datetime import datetime , timedelta , date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class DietOrder(models.Model):
    _name = 'diet.order'
    _description = 'Diet Order'
    
    date = fields.Date(required=True)  
    subscriptions_id = fields.Many2one('diet.meals.subscriptions')
    partner_id = fields.Many2one('res.partner', related='subscriptions_id.partner_id')
    package_id = fields.Many2one('diet.packages', related='subscriptions_id.package_id')
    company_id = fields.Many2one('res.company', related='subscriptions_id.company_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], default='draft')

    line_ids = fields.One2many('diet.order.line', 'order_id', states={'draft': [('readonly', False)]}, copy=False, readonly=True)
    order_id = fields.Many2one('sale.order')

    def _prepare_order_vals(self):
        return {
            'date_order'            : fields.Datetime.now(),
            'partner_id'            : self.partner_id.id,
            'partner_invoice_id'    : self.partner_id.id,
            'partner_shipping_id'   : self.partner_id.id,
            'company_id'            : self.company_id.id,
        }

    def action_confirm(self):
        self.state = 'confirm'
        order = self.env['sale.order'].create(self._prepare_order_vals())
        self.order_id = order.id
        for line in self.line_ids:
            self.env['sale.order.line'].create(line._prepare_orderline_vals(order))

    def action_cancel(self):
        self.state = 'cancel'

    
    def auto_action_confirm_before_two_days(self):
        after_two_days = fields.Date.context_today(self) + timedelta(days=2)
        order_ids = self.search([('state','=','draft')])
        for rec in order_ids:
            if after_two_days >= rec.date:
                rec.action_confirm()


class DietOrderLine(models.Model):
    _name = 'diet.order.line'
    _description = 'Diet Order Line'
    
    order_id = fields.Many2one('diet.order')
    product_filter_ids = fields.Many2many('product.product', compute='_compute_product_filter_ids')
    categ_ids = fields.Many2many('diet.category', required=True)
    product_ids = fields.Many2many('product.product', domain="[('diet_meal_ok', '=', True),('category_ids','in',categ_ids),('id','in', product_filter_ids)]")
    quantity = fields.Integer('Allowed Quantity')

    def _prepare_orderline_vals(self, order):
        vals = []
        for product in self.product_ids:
            vals.append({
                'order_id'        : order.id,
                'product_id'      : product.id,
                'product_uom_qty' : 1,
                'product_uom'     : product.uom_id.id,
            })
        return vals

    def _compute_product_filter_ids(self):
        for rec in self:
            lines = self.env['menu.schedual.line'].search([('date', '=', rec.order_id.date)])
            rec.product_filter_ids = lines.mapped('product_ids')

    @api.constrains('product_ids', 'quantity')
    def _validate_allowed_quantity(self):
        for rec in self:
            if len(rec.product_ids) > rec.quantity:
                raise ValidationError(_("Products must be equal or less than allowed quantity"))