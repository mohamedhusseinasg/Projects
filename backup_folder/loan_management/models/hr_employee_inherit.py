from odoo import models, fields, api, _


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    join_date = fields.Date(string='Join Date ')
    loan_request_ids = fields.One2many('loan.request', 'employee_id', string='Loan Requests')
    hr_id = fields.Many2one('hr.employee' ,string='HR')
    financial_manager_id = fields.Many2one('hr.employee' ,string='Financial Manager')


    def action_view_loan_requests(self):

        return {
            'name': _('Loan Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'loan.request',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.loan_request_ids.ids)],
        }


