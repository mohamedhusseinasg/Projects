# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import uuid
import string
import random
import subprocess
import logging
import os
import requests
from odoo.exceptions import ValidationError
from requests.structures import CaseInsensitiveDict
import time


_logger = logging.getLogger(__name__)


class DxGithub (models.Model):
    _name = "dxeg.github"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "DXEG Github"
    _rec_name = "name"

    name = fields.Char(string="Repository Name", required=True, tracking=True, copy=False)
    username = fields.Char(string="Github username", required=True, tracking=True)
    repo_url = fields.Char(string="Repository url", copy=False)
    branch = fields.Char(string="branch", required=True, tracking=True)
    github_access_token = fields.Char(string="Access Token", required=False)
    webhook_token = fields.Char(string="Webhook Token", copy=False)
    webhook_github_id = fields.Integer(string="Webhook Github ID", copy=False)
    last_commit_id = fields.Char(string="Last Commit ID", readonly=True, tracking=True)
    last_commit_message = fields.Char(string="Last Commit Message", readonly=True, tracking=True)
    notes = fields.Char(string="Notes", tracking=True)
    last_commit_content = fields.Char("Last commit directories", readonly=True)
    state = fields.Selection([
        ("not_linked", "Not linked"),
        ("linked", "Linked")], string="Status", index=True, required=True, default="not_linked",
        copy=False, tracking=True)

    _sql_constraints = [
        ('dxeg_github_name_unique', 'unique(name)', 'Repository name already exists!'),
    ]

    @api.model
    def create(self, values):
        destination_addons_dir = (
            self.env["ir.config_parameter"].sudo().get_param("dxeg_github.addons_dir", "False"))
        if not destination_addons_dir:
            raise UserError(_("Please define addons directory before adding new repo"))
        else:
            webhook_token = str(self.env.user.id) + "_" + uuid.uuid4().hex
            values["webhook_token"] = webhook_token
            res = super().create(values)
            return res

    @api.onchange("name", "username")
    def onchange_repo_name(self):
        repo = self.env["dxeg.github"].search([("id", "=", self._origin.id)])
        if self.name != repo.name or self.username != repo.username:
            if repo.state == "linked":
                repo.state = "not_linked"

    def get_last_commit_action(self):
        for git_repo in self:
            if not git_repo.name or not git_repo.branch or not git_repo.github_access_token:
                raise UserError(_("Missing required data"))
            else:
                tmp_dir_name = str(''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
                git_tmp_dir = os.path.join("/tmp/", tmp_dir_name)
                create_git_tmp_dir_cmd = "mkdir " + str(git_tmp_dir)
                try:
                    subprocess.run([create_git_tmp_dir_cmd], check=True, shell=True,
                                   stderr=subprocess.STDOUT)
                    try:
                        repo_url = "github.com/" + str(git_repo.username) + "/" + str(git_repo.name) + ".git"
                        git_line = "git clone -b %s https://%s@%s %s" % (git_repo.branch, git_repo.github_access_token,
                                                                         repo_url, git_tmp_dir)
                        subprocess.run([git_line], check=True, shell=True, capture_output=True)
                        last_commit_message = subprocess.run("git log -1 | grep commit", check=True,
                                                             shell=True, capture_output=True, cwd=git_tmp_dir)
                        try:
                            destination_addons_dir = self.env["ir.config_parameter"].sudo().get_param(
                                "dxeg_github.addons_dir", "False")
                            if destination_addons_dir:
                                last_commit_content = git_repo.last_commit_content
                                if last_commit_content:
                                    last_commit_content = eval(git_repo.last_commit_content)
                                    for content in last_commit_content:
                                        try:
                                            rm_old_dir_cmd = "rm -rf %s/%s" % (destination_addons_dir, content)
                                            subprocess.run([rm_old_dir_cmd], check=False, shell=True)
                                        except:
                                            pass
                                    _logger.info("Removed old commit directories successfully")
                                copy_repo_cmd = "cp -R %s/* %s" % (git_tmp_dir, destination_addons_dir)
                                subprocess.run([copy_repo_cmd], check=True, shell=True, capture_output=True)
                                git_repo.last_commit_content = os.listdir(git_tmp_dir)
                                git_repo.message_post(
                                    body=_('Fetched Commit "%s" Successfully' % last_commit_message.stdout))
                                time.sleep(3)
                                sudo_password = self.env["ir.config_parameter"].sudo().get_param(
                                    "dxeg_github.sudo_password",
                                    "False")
                                service_restart_cmd = self.env["ir.config_parameter"].sudo().get_param(
                                    "dxeg_github.service_restart_cmd", "systemctl restart odoo")
                                try:
                                    if service_restart_cmd.startswith("http"):
                                        requests.post(service_restart_cmd)
                                    else:
                                        if sudo_password:
                                            if sudo_password:
                                                subprocess.run('echo {} | sudo -S {}'.format(sudo_password,
                                                                                             service_restart_cmd),
                                                               shell=True)
                                            else:
                                                subprocess.run([service_restart_cmd], check=True, shell=True,
                                                               capture_output=True)
                                    _logger.info("Odoo restarted successfully")
                                except subprocess.CalledProcessError as e:
                                    _logger.exception(e.output)
                            else:
                                _logger.exception("Missing addons directory")
                        except subprocess.CalledProcessError as e:
                            _logger.exception(e.output)
                    except subprocess.CalledProcessError as e:
                        git_repo.message_post(body=_(e.stderr.decode("utf-8")))
                except subprocess.CalledProcessError as e:
                    _logger.exception(e.output)

    def backup_database_now(self):
        if self.id:
            for git_repo in self:
                git_repo.message_post(body=_('Backup Created Successfully by %s' % self.env.user.name))
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/github/database/backup_now',
                    'target': 'self',
                }

    def prepare_webhook_data(self, webhook_url):
        data = {
            'name': 'web',
            'events': ["push"],
            'config': {
                "content_type": "json",
                "insecure_ssl": "0",
                "url": webhook_url
            }
        }
        return data

    def link_webhook(self):
        try:
            for repo_data in self:
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                repo_url = str(base_url) + '/github/webhook/' + repo_data.webhook_token
                data = self.prepare_webhook_data(repo_url)
                if data:
                    oauth_token = repo_data.github_access_token
                    username = repo_data.username
                    url = "https://api.github.com/repos/%s/%s/hooks" % (repo_data.username, repo_data.name)
                    response = requests.post(url, json=data, auth=(username, oauth_token))
                    message = response.json()
                    if response.status_code in [200, 201]:
                        repo_data.state = "linked"
                        repo_data.webhook_github_id = message["id"]
                        repo_data.message_post(
                            body=_("Webhook linked successfully"))
                        _logger.info("Webhook linked successfully")
                    else:
                        if message["errors"][0]["message"]:
                            error_message = response.json()["errors"][0]["message"]
                            raise ValidationError(error_message)
                        else:
                            repo_data.message_post(
                                body=_(message))
                        _logger.error(message)
        except Exception as e:
            raise ValidationError(e)

    def unlink_webhook(self):
        try:
            for repo_data in self:
                url = "https://api.github.com/repos/%s/%s/hooks/%s" % (repo_data.username, repo_data.name,
                                                                       repo_data.webhook_github_id)
                oauth_token = repo_data.github_access_token
                headers = CaseInsensitiveDict()
                headers["Accept"] = "application/vnd.github.v3+json"
                headers["Authorization"] = "Bearer %s" % oauth_token
                response = requests.delete(url, headers=headers)
                if response.status_code == 204:
                    message = "Webhook unlinked successfully"
                else:
                    message = "Unknown error please delete it manually"
                repo_data.state = "not_linked"
                repo_data.webhook_github_id = None
                repo_data.message_post(
                    body=_(message))
        except Exception as e:
            raise ValidationError(e)
