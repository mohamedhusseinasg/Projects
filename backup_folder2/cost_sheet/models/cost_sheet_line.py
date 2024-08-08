
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class cost_sheet_line(models.Model):
    _name = 'cost.sheet.line'
    _description = 'cost sheet'

    cost_sheet_id = fields.Many2one('cost.sheet')
    product_id = fields.Many2one(
        'product.product', string="Prod.", placeholder="Enter Product Description")
    # Brand  = fields.Char('Brand')
    # description = fields.Char(string='Product Description',related='Product_id.name')
    product_quantity = fields.Float(
        string='Qty.Hand', related='product_id.virtual_available')
    qty = fields.Float(string='Qty')
    # cost_currency = fields.Many2one(related='cost_sheet_id.cost_currency', string ="Cost Currency")
    initial_cost = fields.Float(string='Init.Cost', required=True)
    discount = fields.Float(string='Disc.', digits=(10, 2))
    company_discount = fields.Float(string='Comp.Disc', digits=(10, 2))
    shipping_cost = fields.Float(
        string='Ship.Cost', required=True, digits=(10, 2))
    landed_cost = fields.Float(
        string='Land.Cost', related='product_id.cost_price_oh',   readonly=False)
    unit_cost = fields.Float(
        string='Unit.Cost', compute='_compute_unit_total_cost')
    total_cost = fields.Float(string='Tot.Cost')
    margin = fields.Float(string='Margin',  default=0.0, digits=(
        10, 2), compute='_compute_margin', store=True, readonly=False)
    # price_currency = fields.Many2one(related='cost_sheet_id.price_currency', string ="Price Currency")
    unit_price = fields.Float(
        string='Unit.Price', compute='_compute_unit_total_prise', readonly=False)
    total_price = fields.Float(string='Tot.Price')
    cost_currency = fields.Many2one('res.currency', string="Cost.Curr", required=True,
                                    default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]))
    price_currency = fields.Many2one('res.currency', string="Price.Curr",
                                     required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    initial_cost_currency = fields.Many2one('res.currency', string="Init.CostCurr",
                                            required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    rounding = fields.Boolean(string='Rnd')
    absolute_discount = fields.Float(
        string='Discount', compute='_compute_absolute_discount',default=0.0)
    margin_unit = fields.Float(
        string='margin', compute='_compute_margin_unit',default=0.0)


    @api.depends('total_price', 'unit_cost','qty','margin')
    def _compute_margin_unit(self):
        for record in self:
            record.margin_unit = 0.0
            if record.margin:
                if record.initial_cost_currency and record.cost_currency != record.price_currency:
                   record.margin_unit = record.total_price - (record.total_cost * record.cost_currency.rate)
                else:
                    record.margin_unit = record.total_price - record.total_cost

    @api.depends('total_price', 'unit_price')  # Define dependencies
    # @api.onchange('total_price', 'unit_price')  # Define dependencies
    def _compute_absolute_discount(self):
        for record in self:
            record.absolute_discount = 0.0
            if record.total_price and record.unit_price:
                record.absolute_discount =  (record.unit_price * record.qty) - record.total_price



    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and self.product_quantity == 0:
            self.landed_cost = 0

    @api.depends('initial_cost', 'discount', 'company_discount', 'shipping_cost', 'qty')
    def _compute_unit_total_cost(self):
        #### total Unit cost =initial cost(1-discount/100t)+initial cost(1+shipping and custom/100)###
        for record in self:
            if record.product_id and record.initial_cost:
                shipping = record.shipping_cost
                discount = record.discount
                company_discount = record.company_discount
                if record.initial_cost_currency.id != self.env.user.company_id.currency_id.id and record.cost_currency.id != self.env.user.company_id.currency_id.id:
                    if record.initial_cost_currency.id != record.cost_currency.id:
                        initial_ex = record.initial_cost * record.initial_cost_currency.rate
                        exchange = initial_ex * record.cost_currency.inverse_rate
                        unit_cost = exchange * (1-discount)* (1+record.shipping_cost)
                        # unit_cost *= (1-company_discount)
                        fainal_total = unit_cost
                        record.unit_cost = fainal_total
                        record.total_cost = record.unit_cost * record.qty
                    else:
                        unit_cost = record.initial_cost * (1-discount)* (1+record.shipping_cost)
                        # unit_cost *= (1-company_discount)
                        fainal_total = unit_cost
                        record.unit_cost = fainal_total
                        record.total_cost = record.unit_cost * record.qty
                elif record.initial_cost_currency.id == self.env.user.company_id.currency_id.id and record.cost_currency.id == self.env.user.company_id.currency_id.id:
                    fainal_total = record.initial_cost * (1-discount)* (1+record.shipping_cost)
                    # fainal_total *= (1-company_discount)
                    record.unit_cost = fainal_total
                    record.total_cost = record.unit_cost * record.qty

                elif record.initial_cost_currency.id == self.env.user.company_id.currency_id.id and record.cost_currency.id != self.env.user.company_id.currency_id.id:
                    exchange = record.initial_cost * record.cost_currency.inverse_rate
                    unit_cost = exchange * (1-discount)* (1+record.shipping_cost)
                    # unit_cost *= (1-company_discount)
                    fainal_total = unit_cost
                    record.unit_cost = fainal_total
                    record.total_cost = record.unit_cost * record.qty

                elif record.cost_currency.id == self.env.user.company_id.currency_id.id and record.initial_cost_currency.id != self.env.user.company_id.currency_id.id:
                    exchange = record.initial_cost * record.initial_cost_currency.rate
                    unit_cost = exchange * (1-discount)* (1+record.shipping_cost)
                    # unit_cost *= (1-company_discount)
                    fainal_total = unit_cost
                    record.unit_cost = fainal_total
                    record.total_cost = record.unit_cost * record.qty
                elif record.initial_cost_currency.id == self.env.user.company_id.currency_id.id and record.cost_currency.id == self.env.user.company_id.currency_id.id and record.price_currency.id == self.env.user.company_id.currency_id.id:
                    fainal_total = record.initial_cost * (1-discount)* (1+record.shipping_cost)
                    # fainal_total *= (1-company_discount)
                    record.unit_cost = fainal_total
                    record.total_cost = record.unit_cost * record.qty
            elif record.product_id and record.initial_cost == 0.0 and record.landed_cost:
                discount = record.discount
                company_discount = record.company_discount
                fainal_total = record.landed_cost * (1-discount)* (1+record.shipping_cost)
                # fainal_total *= (1-company_discount)
                record.unit_cost = fainal_total
                record.total_cost = record.unit_cost * record.qty
            else:
                record.unit_cost = 0.0

    @api.onchange('landed_cost')
    def _onchange_landed_cost(self):
        currency_id = self.env['res.currency'].search([('name', '=', 'USD')])
        if self.landed_cost:
            self.cost_currency = self.env.user.company_id.currency_id.id
            self.price_currency = self.env.user.company_id.currency_id.id
        else:
            self.cost_currency = currency_id.id
            self.price_currency = currency_id.id

    @api.depends('unit_price')
    def _compute_margin(self):
        for record in self:
            if record.unit_price and record.unit_cost and record.price_currency.id == self.env.user.company_id.currency_id.id:
                record.margin = (
                    (record.unit_price - record.unit_cost * record.cost_currency.rate) / record.unit_price)
                record.total_price = record.unit_price * record.qty
            elif record.unit_price and record.unit_cost and record.price_currency.id != self.env.user.company_id.currency_id.id:
                 record.margin = (
                    (record.unit_price - record.unit_cost) / record.unit_price)
                 record.total_price = record.unit_price * record.qty
            else:
                 record.margin = 0.0




    @api.depends('margin', 'unit_cost', 'cost_currency', 'price_currency', 'company_discount', 'rounding')
    def _compute_unit_total_prise(self):
        for record in self:
            company_discount = record.company_discount
            ###### unit price= total cost*(1+margin/100)##########
            if record.product_id and record.unit_cost:
                if record.cost_currency.id != self.env.user.company_id.currency_id.id and record.price_currency.id != self.env.user.company_id.currency_id.id:
                    if record.cost_currency.id != record.price_currency.id:
                        initial_ex = record.unit_cost * record.cost_currency.rate
                        exchange = initial_ex * record.price_currency.inverse_rate
                        # prise_total = record.unit_cost  * exchange
                        if record.rounding == True:
                            record.unit_price = round(
                                exchange / (1-record.margin))
                            record.total_price = record.unit_price * record.qty
                            record.total_price -= (record.total_price *
                                                   company_discount)

                        else:
                            record.unit_price = exchange / (1-record.margin)
                            record.total_price = record.unit_price * record.qty
                            record.total_price -= (record.total_price *
                                                   company_discount)
                    else:
                        record.unit_price = record.unit_cost * \
                            (1+record.margin)

                        record.total_price = record.unit_price * record.qty
                        record.total_price -= round(record.total_price *
                                                    company_discount)
                elif record.cost_currency.id == self.env.user.company_id.currency_id.id and record.price_currency.id != self.env.user.company_id.currency_id.id:
                    exchange = record.unit_cost * record.price_currency.inverse_rate
                    prise_total = exchange
                    if record.rounding == True:
                        record.unit_price = round(
                            prise_total / (1-record.margin))
                        record.total_price = record.unit_price * record.qty
                        record.total_price -= round(record.total_price *
                                                    company_discount)
                    else:
                        record.unit_price = prise_total / (1-record.margin)
                        record.total_price = record.unit_price * record.qty
                        record.total_price -= round(record.total_price *
                                                    company_discount)
                        # record.margin = 10
                elif record.price_currency.id == self.env.user.company_id.currency_id.id and record.cost_currency.id != self.env.user.company_id.currency_id.id:
                    exchange = record.unit_cost * record.cost_currency.rate
                    prise_total = exchange
                    if record.rounding == True:
                        record.unit_price = round(
                            prise_total / (1-record.margin))
                        record.total_price = record.unit_price * record.qty
                        record.total_price -= round(record.total_price *
                                                    company_discount)

                    else:
                        record.unit_price = prise_total / (1-record.margin)
                        record.total_price = record.unit_price * record.qty
                        record.total_price -= round(record.total_price *
                                                    company_discount)

                        # record.margin = 20

                elif record.price_currency.id == self.env.user.company_id.currency_id.id and record.cost_currency.id == self.env.user.company_id.currency_id.id:
                    exchange = record.unit_cost * record.cost_currency.rate
                    prise_total = exchange
                    if record.rounding == True:
                        record.unit_price = round(
                            prise_total / (1-record.margin), 0) if record.margin < 1 else round(
                            prise_total / (record.margin), 0)
                        record.total_price = record.unit_price * record.qty
                        record.total_price -= round(record.total_price *
                                                    company_discount)

                    else:

                        record.unit_price = prise_total / \
                            (1-record.margin)
                        record.total_price = record.unit_price * record.qty
                        record.total_price -= round(record.total_price *
                                                    company_discount)

                    # if record.rounding == True:
                    #     record.unit_price = round(record.unit_cost * (1+record.margin))
                    #     print(record.unit_price,"#$#$")
                    #     record.total_price = record.unit_price * record.qty

                    # else:
                    #     record.unit_price = record.unit_cost * (1+record.margin)
                    #     record.total_price = record.unit_price * record.qty

            else:
                record.unit_price = 0.0

