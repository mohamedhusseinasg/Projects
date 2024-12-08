from odoo import models, fields, api


class GymCustomer(models.Model):
    _inherit = 'res.partner'

    number_id=fields.Integer(streing='ID Number')

    _sql_constraints = [
        ('unique_number', 'UNIQUE(number_id)', 'The number_id must be unique.'),
    ]

    _sql_constraints = [
        ('unique_phone', 'UNIQUE(phone)', 'The phone number must be unique.'),
    ]