from odoo import models, fields, api, _


class HrPayslipInherit(models.Model):
    _inherit = 'hr.payslip'

    amount_loan = fields.Float(string='Loan Payment amount')
    date_of_loan = fields.Date(string=' Loan Payment Date')



    @api.onchange('employee_id')
    def _onchange_date(self):
        for rec in self:
            if rec.employee_id:
                loan_request = self.env['loan.request'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', '=', 'approved')
                ], order='next_payment_date desc', limit=1)

                rec.date_of_loan = loan_request.next_payment_date if loan_request else None
            else:
                rec.date_of_loan = None


    @api.onchange('employee_id')
    def _onchange_amount(self):
        for rec in self:
            if rec.employee_id:
                loan_request = self.env['loan.request'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', '=', 'approved')
                ], order='next_payment_amount desc', limit=1)
                rec.amount_loan = loan_request.next_payment_amount if loan_request else None
            else:
                rec.amount_loan = None
















