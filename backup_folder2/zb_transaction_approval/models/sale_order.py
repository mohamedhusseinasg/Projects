# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2024 ZestyBeanz Technologies.
#    (http://wwww.zbeanztech.com)
#    contact@zbeanztech.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models,fields,api,_
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    is_approved = fields.Boolean(string="Approved",default=False,readonly=True)
    approved_by = fields.Char(string="Approved by",readonly = True)
    approval_send = fields.Boolean(string="Approval Requested",default=False)
    approve_on = fields.Datetime(string="Approved On",readonly = True)

    def action_approval(self):
        """
        This method sends an approval email for the current sale order to all users in the 'group_sale_orders_approver' group. 
        sets the 'approval_send' field of the sale order to True.
        """ 
        template = self.env.ref('zb_transaction_approval.mail_template_approval')
        # sale_order = self.env['sale.order'].browse(self.id)
        for order in self:
            if order.approval_send == True:
                raise ValidationError(_("Document is already send for approval. Please refresh the page."))
            else:
                if template:
                    approver_group = self.env.ref('zb_transaction_approval.group_sale_order_approver') 
                    if approver_group:
                        email_to = ','.join(user.email for user in approver_group.users)
                        template.write({'email_to': email_to})
                        template.with_context(sale_order=order).send_mail(order.id, force_send=True) 
                        order.approval_send = True
                        order.message_post(body="Approval email sent for this sale order.")
                   
    def action_approve(self):
        """
        Method gets called upon approval. It approves the current record and sets the fields with corresponding data.
        """  
        for rec in self:
            if rec.is_approved == True:
                 raise ValidationError(_("Document is already approved by %s. Please refresh the page.",rec.approved_by,))
            else:
                rec.is_approved = True
                rec.approved_by = self.env.user.name  
                rec.approve_on = fields.Datetime.now()  
                msg = f"Approved \n"
                rec.message_post(body=msg)
                
    def action_draft(self):
        """
        Resetting approval values on moving record to draft
        """  
        for rec in self:
            rec.write({'approval_send':False,'is_approved':False,'approve_on':False, 'approved_by':False})
        return super(SaleOrder,self).action_draft()

            