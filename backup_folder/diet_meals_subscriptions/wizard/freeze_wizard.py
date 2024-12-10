from odoo import _, api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import datetime

class FreezeWizard(models.TransientModel):
    _name = 'freeze.wizard'
    _description = 'Freeze Wizard'
    
    def _get_minDate(self):
        date = fields.Date.context_today(self)
        start_date = fields.Date.context_today(self)
        if self._context.get('start_date',False):
            start_date = datetime.strptime(self._context.get('start_date'), '%Y-%m-%d').date()
        if start_date > date:
            date = start_date
        date += relativedelta(days=2)
        return date.strftime('%Y-%m-%d')

    minDate = fields.Char(default=_get_minDate)
    subscriptions_id = fields.Many2one('diet.meals.subscriptions')
    start_date = fields.Date(readonly=False, tracking=True)
    freeze = fields.Integer()

    def confirm(self):
        if self.subscriptions_id:
            self.env['diet.subscriptions.freeze'].create({
                'subscriptions_id': self.subscriptions_id.id,
                'start_date': self.start_date,
                'freeze': self.freeze,
                'state': 'draft',
            })