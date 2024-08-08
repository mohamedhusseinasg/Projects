import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderInhert(models.Model):

    _inherit = 'sale.order'


    total_discounts = fields.Monetary(string='Total Discount Company')
    final_total = fields.Monetary(string='Final Total')
    oppertunity_count = fields.Integer(compute="compute_count_cost_sheet")
    flag = fields.Boolean()
    from_cost_sheet = fields.Boolean(  string='From Cost Sheet', default=False, help='this field used to controll appearing of column for quantity')
    total_prises = fields.Monetary(string='Price',compute='_compute_total_prises')

    @api.depends('order_line.price_subtotal')
    def _compute_total_prises(self):
        for rec in self:
            rec.total_prises = sum(rec.order_line.mapped('price_subtotal'))

    # # @api.onchange('final_total')
    # def _compute_amount(self):
    #       for rec in self:
    #         rec.amount_total = rec.final_total

    # def _compute_amounts(self):
    #     super(SaleOrderInhert, self)._compute_amounts()
    #     for order in self:
    #         order.amount_total = order.final_total


    def _compute_amounts(self):
        res = super(SaleOrderInhert, self)._compute_amounts()
        for order in self:
            order.amount_total =22
        return res



    def compute_count_cost_sheet(self):
        for record in self:
            record.oppertunity_count = self.env['cost.sheet'].search_count(
                [('sequence', '=', self.origin)])
            # print(record.oppertunity_count)

    def get_cost_sheets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Qutations',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'cost.sheet',
            'domain': [('sequence', '=', self.origin)],
        }

