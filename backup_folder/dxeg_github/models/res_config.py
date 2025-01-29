# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    addons_dir = fields.Char(string="Addons Directory", config_parameter="dxeg_github.addons_dir", required=True)
    service_restart_cmd = fields.Char(string="Odoo Restart Command", config_parameter="dxeg_github.service_restart_cmd")
    sudo_password = fields.Char(string="Sudo Password", config_parameter="dxeg_github.sudo_password")
