from odoo import models, fields, api

class LoanInstallment(models.Model):
    _name = 'loan.installment'
    _description = 'Loan Installment'

    loan_id = fields.Many2one('loan.request', string='Loan Request')
    paid = fields.Boolean(string='Paid', default=False)
    amount = fields.Float(string='Amount',compute="_compute_installment_amount", store=True)
    date = fields.Date(string='Payment Date', required=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')


    @api.depends('loan_id.amount', 'loan_id.number_of_months')
    def _compute_installment_amount(self):
        for rec in self:
            if rec.loan_id.amount and rec.loan_id.number_of_months:
                rec.amount = rec.loan_id.amount / rec.loan_id.number_of_months
            else:
                rec.amount = 0.0