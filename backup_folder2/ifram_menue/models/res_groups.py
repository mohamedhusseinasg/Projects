from odoo import models, fields, api

class ResGroups(models.Model):
    _inherit = 'res.groups'

    is_iframe_group = fields.Boolean(string="Is Iframe Group", default=False)

    def get_application_groups(self, domain):
        # Add condition to filter out iframe groups
        domain = domain + [('is_iframe_group', '=', False)]
        return super(ResGroups, self).get_application_groups(domain)
