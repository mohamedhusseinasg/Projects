

from odoo import models,fields,api,_
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # add 2 fields to get the same values in the setting :
    po_product_approvals = fields.Boolean(
        string="Product Order Approval",
        store=True)

    product_double_validation_amount = fields.Integer(
        string="Double Validation Amount",
        store=True)
    is_true =fields.Boolean('Is True',compute="_compute_is_true")

    is_approved = fields.Boolean(string="Approved",default=False)
    approved_by = fields.Char(string="Approved by")
    approval_send = fields.Boolean(string="Approval Requested",default=False)
    approve_on = fields.Datetime(string="Approved on")


    @api.depends('product_double_validation_amount', 'amount_total')
    def _compute_is_true(self):
        groups = 'zb_transaction_approval.group_purchase_orders_approver'
        group = self.env.ref(groups)
        for record in self:
            if self.env.user not in group.users:
                if record.amount_total > record.product_double_validation_amount and record.po_product_approvals:
                    record.is_true = True
                else:
                    record.is_true = False
            else:
                record.is_true = False

    def action_approval(self):
        """
        This method sends an approval email for the current purchase order to all users in the 'group_purchase_orders_approver' group. 
        sets the 'approval_send' field of the purchase order to True.
        """
        template = self.env.ref('zb_transaction_approval.mail_template_purchase_approval')
        for order in self:
            if order.approval_send == True:
                raise ValidationError(_("Document is already send for approval.Please refresh the page."))
            else:
                if template:
                    approver_group = self.env.ref('zb_transaction_approval.group_purchase_orders_approver') 
                    if approver_group:
                        email_to = ','.join(user.email for user in approver_group.users)
                        template.write({'email_to': email_to})
                        template.with_context(purchase_order=order).send_mail(order.id, force_send=True) 
                        order.approval_send = True
                        order.message_post(body="Approval email sent for this purchase order.")
                        
    def action_approve(self):
        """
        Method gets called upon approval. It approves the current record and sets the fields with corresponding data.
        """
        for rec in self:
            if rec.is_approved == True:
                 raise ValidationError(_("Document is already approved by %s. Please refresh the page.",rec.approved_by,))
            else:
                rec.is_approved = True
                rec.state = 'purchase'
                rec.approved_by = self.env.user.name  
                rec.approve_on = fields.Datetime.now() 
                msg = f"Approved \n"
                rec.message_post(body=msg)
     
    def button_draft(self):
        """
        Resetting approval values on moving record to draft
        """ 
        for rec in self:
            rec.write({'approval_send':False,'is_approved':False,'approve_on':False, 'approved_by':False})
        return super(PurchaseOrder,self).button_draft()

    # ////////////////////
    @api.model
    def _compute_po_product_approvals(self):
        param_value = self.env['ir.config_parameter'].sudo().get_param('zb_transaction_approval.po_product_approval')
        self.po_product_approvals = param_value == 'True'  # Convert the string to a boolean

    @api.onchange('po_product_approvals')
    def _onchange_po_product_approvals(self):
        param_value = self.env['ir.config_parameter'].sudo().get_param('zb_transaction_approval.po_product_approval')
        self.po_product_approvals = param_value == 'True'  # Convert the string to a boolean

    @api.onchange('product_double_validation_amount')
    def _onchange_product_double_validation_amount(self):
        param_value = self.env['ir.config_parameter'].sudo().get_param(
            'zb_transaction_approval.product_double_validation_amount')
        self.product_double_validation_amount = int(
            param_value) if param_value else 0  # Convert to int and handle possible None

    @api.model
    def create(self, vals):
        self._set_config_values(vals)
        return super(PurchaseOrder, self).create(vals)

    def write(self, vals):
        self._set_config_values(vals)
        return super(PurchaseOrder, self).write(vals)

    def _set_config_values(self, vals):
        if 'po_product_approvals' not in vals:
            param_value = self.env['ir.config_parameter'].sudo().get_param('zb_transaction_approval.po_product_approval')
            vals['po_product_approvals'] = param_value == 'True'

        if 'product_double_validation_amount' not in vals:
            param_value = self.env['ir.config_parameter'].sudo().get_param(
                'zb_transaction_approval.product_double_validation_amount')
            vals['product_double_validation_amount'] = int(param_value) if param_value else 0


