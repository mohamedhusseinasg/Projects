# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class cost_sheet(models.Model):
    _name = 'cost.sheet'
    _description = 'cost.sheet'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'

    STATUS_SELECTION = [
        ('draft', 'Draft'),
        ('qutation', 'Qutation Created'),
    ]
    status = fields.Selection(
        STATUS_SELECTION, string='Status', default='draft')
    sequence = fields.Char(string='Reference', required=True,
                           readonly=True, index=True, copy=False, default='New')
    date = fields.Date(string="Date")
    partner_id = fields.Many2one('res.partner', string="Customer")
    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    cost_sheet_line_ids = fields.One2many(
        'cost.sheet.line', 'cost_sheet_id', string="Cost Sheet Line")
    # cost_currency = fields.Many2one('res.currency', string ="Cost Currency",required=True, default=lambda self: self.env['res.currency'].search([('name', '=', 'USD')]))
    # price_currency = fields.Many2one('res.currency', string ="Price Currency",required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    # initial_cost_currency = fields.Many2one('res.currency', string ="Initial Cost Currency",required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    # shipping_cost_currency = fields.Many2one('res.currency', string ="Shipping Cost Currency",required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    quotation_currency = fields.Many2one('res.currency', string="Quotation Currency",
                                         required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    quotation_count = fields.Integer(compute="compute_count_qutation")
    final_total = fields.Float(string='Final Total', compute='_compute_final_total')
    total_discount = fields.Float(string='Total Discount', compute='_compute_final_discount')
    margin_total = fields.Float(string='Margin Total',compute='_compute_margin_total')
    price_currency = fields.Many2one(
        'res.currency',
        string="Price Currency",
        compute='_onchange_set_price_currency'
    )

    # cost_price_oh = fields.Float(string="Cost Price Overhead", compute='_compute_cost_price_oh')
    # parent_product = fields.Many2one(
    #     'product.product', string="Parent Product")
    #
    # @api.depends('parent_product.standard_price')
    # def _compute_cost_price_oh(self):
    #     for rec in self:
    #         if rec.parent_product.standard_price:
    #             rec.cost_price_oh = rec.parent_product.standard_price + rec.parent_product.standard_price * 0.10
    #         else:
    #             rec.cost_price_oh = 0.0

    @api.depends('cost_sheet_line_ids')
    def _onchange_set_price_currency(self):
        for rec in self:
            rec.price_currency = rec.cost_sheet_line_ids.price_currency


    @api.depends('cost_sheet_line_ids.margin_unit')
    def _compute_margin_total(self):
        for rec in self:
            rec.margin_total = sum(rec.cost_sheet_line_ids.mapped('margin_unit'))

    @api.depends('cost_sheet_line_ids.total_price')
    def _compute_final_total(self):
        for req in self:
            req.final_total = sum(req.cost_sheet_line_ids.mapped('total_price'))

    @api.depends('cost_sheet_line_ids.absolute_discount')
    def _compute_final_discount(self):
        for req in self:
            total_discounts = sum(req.cost_sheet_line_ids.mapped('absolute_discount'))
            req.total_discount = total_discounts
    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'cost.sheet') or 'New'
            result = super(cost_sheet, self).create(vals)
        return result

    def action_open_quotation(self):
        order_lines = []
        parents = []
        total = []
        for rec in self.cost_sheet_line_ids:
            if rec.product_id.parent_product.id:
                if rec.product_id.parent_product.id not in parents:
                    for record in self.cost_sheet_line_ids:
                        if rec.product_id.parent_product.id == record.product_id.parent_product.id:
                            parents.append(rec.product_id.parent_product.id)
                            total.append(rec.total_price)
                            # totale.append(rec.unit_price)
                            total_price = sum(total)
                            print(total, total_price, "total_price",
                                  rec.product_id.name)

                    if rec.price_currency.id != self.env.user.company_id.currency_id.id and self.quotation_currency.id != self.env.user.company_id.currency_id.id:
                        if rec.price_currency.id != self.quotation_currency.id:
                            initial_ex = unit_price * rec.price_currency.rate
                            exchange = initial_ex * self.quotation_currency.inverse_rate
                            order_line = (0, 0, {
                                'product_id': rec.product_id.parent_product.id,
                                'product_uom_qty': rec.qty,
                                'price_unit': exchange,
                                'real_qty': rec.qty,
                                'price_subtotal': exchange * rec.qty
                            })
                            order_lines.append(order_line)
                            total = []

                        else:
                            order_line = (0, 0, {
                                'product_id': rec.product_id.parent_product.id,
                                'product_uom_qty': rec.qty,
                                'price_unit': unit_price,
                                'real_qty': rec.qty,
                                'price_subtotal': unit_price * rec.qty

                            })
                            order_lines.append(order_line)
                            total = []
                    elif rec.price_currency.id == self.env.user.company_id.currency_id.id and self.quotation_currency.id != self.env.user.company_id.currency_id.id:
                        exchange = unit_price * rec.cost_currency.inverse_rate
                        order_line = (0, 0, {
                            'product_id': rec.product_id.parent_product.id,
                            'product_uom_qty': rec.qty,
                            'price_unit': exchange,
                            'real_qty': rec.qty,
                            'price_subtotal': exchange * rec.qty

                        })
                        order_lines.append(order_line)
                        total = []
                    elif self.quotation_currency.id == self.env.user.company_id.currency_id.id and rec.price_currency.id != self.env.user.company_id.currency_id.id:
                        exchange = unit_price * rec.price_currency.rate
                        order_line = (0, 0, {
                            'product_id': rec.product_id.parent_product.id,
                            'product_uom_qty': rec.qty,
                            'price_unit': exchange,
                            'real_qty': rec.qty,
                            'price_subtotal': exchange * rec.qty

                        })
                        order_lines.append(order_line)
                        total = []
                    elif rec.price_currency.id == self.env.user.company_id.currency_id.id and self.quotation_currency.id == self.env.user.company_id.currency_id.id:
                        fainal_total = unit_price
                        order_line = (0, 0, {
                            'product_id': rec.product_id.parent_product.id,
                            'product_uom_qty': rec.qty,
                            'price_unit': fainal_total,
                            'real_qty': rec.qty,
                            'price_subtotal': fainal_total * rec.qty

                        })
                        order_lines.append(order_line)
                        total = []

            else:
                if rec.price_currency.id != self.env.user.company_id.currency_id.id and self.quotation_currency.id != self.env.user.company_id.currency_id.id:
                    if rec.price_currency.id != self.quotation_currency.id:
                        initial_ex = rec.unit_price * rec.price_currency.rate
                        exchange = initial_ex * self.quotation_currency.inverse_rate
                        order_line = (0, 0, {
                            'product_id': rec.product_id.id,
                            'product_uom_qty': rec.qty,
                            'price_unit': exchange,
                            'real_qty': rec.qty,

                        })
                        order_lines.append(order_line)

                    else:
                        order_line = (0, 0, {
                            'product_id': rec.product_id.id,
                            'product_uom_qty': rec.qty,
                            'price_unit': rec.unit_price,
                            'real_qty': rec.qty,

                        })
                        order_lines.append(order_line)
                elif rec.price_currency.id == self.env.user.company_id.currency_id.id and self.quotation_currency.id != self.env.user.company_id.currency_id.id:
                    exchange = rec.unit_price * rec.cost_currency.inverse_rate
                    order_line = (0, 0, {
                        'product_id': rec.product_id.id,
                        'product_uom_qty': rec.qty,
                        'price_unit': exchange,
                        'real_qty': rec.qty,

                        # 'name':rec.product_id.name

                    })
                    order_lines.append(order_line)
                elif self.quotation_currency.id == self.env.user.company_id.currency_id.id and rec.price_currency.id != self.env.user.company_id.currency_id.id:
                    exchange = rec.unit_price * rec.price_currency.rate
                    order_line = (0, 0, {
                        'product_id': rec.product_id.id,
                        'product_uom_qty': rec.qty,
                        'price_unit': exchange,
                        'real_qty': rec.qty
                    })
                    order_lines.append(order_line)
                elif rec.price_currency.id == self.env.user.company_id.currency_id.id and self.quotation_currency.id == self.env.user.company_id.currency_id.id:
                    order_line = (0, 0, {
                        'product_id': rec.product_id.id,
                        'product_uom_qty': rec.qty,
                        'price_unit': rec.unit_price,
                        'real_qty': rec.qty
                    })
                    order_lines.append(order_line)
                # raise UserError(_("There's no Parent Product For %s please add one") %[(rec.product_id.name)])
        pricelist = self.env['product.pricelist'].search(
            [('currency_id', '=', self.quotation_currency.id)])
        if pricelist:
            print("pricelist", pricelist)
            order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'origin': self.sequence,
                'order_line': order_lines,
                'flag': True,
                'final_total': self.final_total,
                'total_discounts' : self.total_discount,
                'from_cost_sheet': True,
                'opportunity_id': self.opportunity_id.id,
                'pricelist_id': self.env['product.pricelist'].search([('currency_id', '=', self.quotation_currency.id)], limit=1).id, })
            context = {
                'default_partner_id': self.partner_id.id,
                'default_date_order': self.date,
            }
            self.status = 'qutation'
            return {
                'name': 'Quotation',
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'view_id': self.env.ref('sale.view_order_form').id,
                'target': 'new',
                'res_id': order.id,
                'context': context,
            }
        else:
            raise UserError(_("There's no pricelist with currency %s to create a qutation please add one") % [
                            (self.quotation_currency.name)])

    def compute_count_qutation(self):
        for record in self:
            record.quotation_count = self.env['sale.order'].search_count(
                [('opportunity_id', '=', self.opportunity_id.id)])

    def get_qutation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Qutations',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'sale.order',
            'domain': [('opportunity_id', '=', self.opportunity_id.id)],
            # 'context': "{'create': True}"
        }

    def action_confirm(self):
        self.status = 'confirmed'

    def action_cancle(self):
        self.status = 'cancle'


class Bundle(models.Model):

    _inherit = 'product.template'

    parent_product = fields.Many2one(
        'product.product', string="Parent Product")
    cost_price_oh = fields.Float(string="Cost Price Overhead", compute='_compute_cost_price_oh')

    @api.depends('standard_price')
    def _compute_cost_price_oh(self):
        for rec in self:
            if rec.standard_price:
                rec.cost_price_oh = rec.standard_price + rec.standard_price * 0.10
            else:
                rec.cost_price_oh = 0.0


class CRM(models.Model):

    _inherit = 'crm.lead'

    current_date = fields.Date.today()
    oppertunity_count = fields.Integer(compute="compute_count_cost_sheet")

    def create_cost_sheet(self):
        self.ensure_one()
        return {
            'name': _('Create Cost Sheet'),
            'type': 'ir.actions.act_window',
            'res_model': 'cost.sheet',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_date': self.current_date,
                'default_partner_id': self.partner_id.id,
                'default_opportunity_id': self.id,
            }
        }

    def compute_count_cost_sheet(self):
        for record in self:
            record.oppertunity_count = self.env['cost.sheet'].search_count(
                [('opportunity_id', '=', self.id)])

    def get_cost_sheets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cost Shee',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'cost.sheet',
            'domain': [('opportunity_id', '=', self.id)],
        }




class cost(models.Model):

    _inherit = 'cost.sheet'


# ==============
class saleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    real_qty = fields.Float(string='Costsheet Quantity')
