from odoo import models, fields, api


class GymTrainer(models.Model):
    _inherit = 'res.partner'

    number_ids = fields.Integer(streing='ID Number')

