from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from datetime import timedelta

class LoanRequest(models.Model):
    _name = 'loan.request'
    _description = 'Loan Request'



    name = fields.Char(string='Loan Reference',readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', domain=[('join_date', '<=', fields.Date.today() - timedelta(days=90))])
    department_name = fields.Many2one(related='employee_id.department_id')
    job_name = fields.Many2one(related='employee_id.job_id')
    manager_name = fields.Many2one(related='employee_id.parent_id')
    phone = fields.Char(related='employee_id.work_phone', readonly=True)
    age = fields.Integer( compute='_compute_employee_age',store=True)
    birth_date = fields.Date(related='employee_id.birthday', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, readonly = True)
    amount = fields.Monetary(string='Loan Amount', required=True)
    state = fields.Selection([
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('hr', 'HR'),
        ('financial manager', 'Financial Manager'),
        ('approved', ' Financial Manager approved'),
        ('cancelled', ' cancel')
    ], string='Status', default='employee')
    start_deduction_date = fields.Date(string='Start Deduction Date')
    number_of_months = fields.Integer(string='Number of month', required=True)
    installment_ids = fields.One2many('loan.installment', 'loan_id', string='Installments')
    is_loan_done = fields.Boolean(string='the loan Fully Done',computed="_computed_amount_loan",store=True,default=False)
    # fully_done = fields.Char(string='Fully Done',readonly=True)
    next_payment_date = fields.Date(string="Next Payment Date", compute="_compute_next_payment_date")
    next_payment_amount = fields.Float(string="Next Payment amount", compute="_compute_next_payment_amount")
    salary = fields.Float(string='The Salary Of Employee')
    salary_deduction = fields.Float (string='The salary after deduction',compute='_compute_salary')


    # compute salary after deduction
    @api.depends('salary', 'number_of_months','amount')
    def _compute_salary(self):
        for rec in self:
            net_salary = rec.amount /rec.number_of_months
            rec.salary_deduction = rec.salary - net_salary

    # to git next payment date
    @api.depends('installment_ids', 'installment_ids.paid')
    def _compute_next_payment_date(self):
        for rec in self:
            unpaid_installment = rec.installment_ids.filtered(lambda l: not l.paid)
            next_payment = unpaid_installment.sorted('date', reverse=False)
            rec.next_payment_date = next_payment[0].date if next_payment else None

    # to git next payment amount
    @api.depends('installment_ids', 'installment_ids.paid')
    def _compute_next_payment_amount(self):
        for rec in self:
            unpaid_installments = rec.installment_ids.filtered(lambda l: not l.paid)
            next_payment = unpaid_installments.sorted('date', reverse=False)
            rec.next_payment_amount = next_payment[0].amount if next_payment else 0.0

    @api.model
    def create(self, values):
        values['name'] = self.env["ir.sequence"].next_by_code("loan_request_code")
        return super(LoanRequest, self).create(values)

    # calculate age based on birth_date
    @api.depends('birth_date')
    def _compute_employee_age(self):
        for record in self:
            if record.birth_date:
                dob = fields.Date.from_string(record.birth_date)
                today = fields.Date.today()
                age = relativedelta(today, dob).years
                record.age = age
            else:
                record.age = 0


    def actions_approve_manager(self):
        self.write({'state': 'hr'})

    def actions_approve_hr(self):
        self.write({'state': 'financial manager'})

    def actions_approve_financial_manager(self):
        self.write({'state': 'approved'})

    def actions_cancel(self):
        self.write({'state': 'cancelled'})


    @api.onchange('installment_ids')
    def _computed_amount_loan(self):
        for rec in self:
            total = sum(rec.installment_ids.mapped('amount'))
            all_paid = all(installment.paid for installment in rec.installment_ids)
            rec.is_loan_done = total == rec.amount and all_paid

