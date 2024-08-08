
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    po_product_approval = fields.Boolean("Product Order Approval",config_parameter="zb_transaction_approval.po_product_approval")

    product_double_validation_amount = fields.Integer(config_parameter="zb_transaction_approval.product_double_validation_amount", string="the Amount", currency_field='company_currency_id', readonly=False)

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     po_product_approval = self.env['ir.config_parameter'].sudo().get_param('zb_product_approve.po_product_approval')
    #     res.update(po_product_approval=po_product_approval)
    #     return res
    #
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     self.env['ir.config_parameter'].sudo().set_param('zb_product_approve.po_product_approval',
    #                                                      self.po_product_approval)
    #

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        po_product_approval = self.env['ir.config_parameter'].sudo().get_param('zb_transaction_approval.po_product_approval')
        product_double_validation_amount = self.env['ir.config_parameter'].sudo().get_param(
            'zb_transaction_approval.product_double_validation_amount')
        res.update(
            po_product_approval=po_product_approval,
            product_double_validation_amount=int(
                product_double_validation_amount) if po_product_approval == 'True' else 0
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('zb_transaction_approval.po_product_approval',
                                                         self.po_product_approval)

        if self.po_product_approval == False:
            self.env['ir.config_parameter'].sudo().set_param('zb_transaction_approval.product_double_validation_amount', 0)

