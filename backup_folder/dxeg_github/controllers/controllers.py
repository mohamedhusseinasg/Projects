# -*- coding: utf-8 -*-
import json
import logging
import subprocess
from odoo import _
from odoo.http import Controller, route
import string
import random
import datetime
import odoo
from odoo.http import content_disposition, request
import werkzeug
import os
import requests
import time

_logger = logging.getLogger(__name__)


class GithubWebhook(Controller):
    @route("/github/webhook/<token>", type="json", auth="public", methods=["POST"], csrf=False)
    def webhook(self, token, **post):
        repo_webhook_token = request.env["dxeg.github"].sudo().search(
            [("webhook_token", "=", token)])
        if repo_webhook_token:
            data = json.loads(request.httprequest.data)
            branch = data["ref"].replace("refs/heads/", "")
            if branch == repo_webhook_token.branch:
                for element in data["commits"]:
                    repo_webhook_token.last_commit_id = element["id"]
                    repo_webhook_token.last_commit_message = element["message"]
                    tmp_dir_name = str(''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
                    git_tmp_dir = os.path.join("/tmp/", tmp_dir_name)
                    create_git_tmp_dir_cmd = "mkdir " + str(git_tmp_dir)
                    if not repo_webhook_token.name or not repo_webhook_token.branch or not \
                            repo_webhook_token.github_access_token:
                        _logger.exception("Missing required data")
                    else:
                        try:
                            subprocess.run([create_git_tmp_dir_cmd], check=True, shell=True,
                                           stderr=subprocess.STDOUT)
                            try:
                                repo_url = "github.com/" + str(repo_webhook_token.username) + "/" + \
                                           str(repo_webhook_token.name) + ".git"
                                git_line = "git clone -b %s https://%s@%s %s" % (
                                   repo_webhook_token.branch, repo_webhook_token.github_access_token, repo_url, git_tmp_dir)
                                subprocess.run([git_line], check=True, shell=True, capture_output=True)
                                try:
                                    destination_addons_dir = request.env["ir.config_parameter"].sudo().get_param(
                                        "dxeg_github.addons_dir", "False")
                                    if destination_addons_dir:
                                        last_commit_content = repo_webhook_token.last_commit_content
                                        if last_commit_content:
                                            last_commit_content = eval(repo_webhook_token.last_commit_content)
                                            for content in last_commit_content:
                                                try:
                                                    rm_old_dir_cmd = "rm -rf %s/%s" % (destination_addons_dir, content)
                                                    subprocess.run([rm_old_dir_cmd], check=False, shell=True)
                                                except:
                                                    pass
                                            _logger.info("Removed old commit directories successfully")
                                        copy_repo_cmd = "cp -R %s/* %s" % (git_tmp_dir, destination_addons_dir)
                                        subprocess.run([copy_repo_cmd], check=True, shell=True, capture_output=True)
                                        repo_webhook_token.last_commit_content = os.listdir(git_tmp_dir)
                                        repo_webhook_token.message_post(
                                            body=_('Fetched Commit "%s" Successfully' % repo_webhook_token.last_commit_id))
                                        time.sleep(3)
                                        sudo_password = request.env["ir.config_parameter"].sudo().get_param(
                                            "dxeg_github.sudo_password",
                                            "False")
                                        service_restart_cmd = request.env["ir.config_parameter"].sudo().get_param(
                                            "dxeg_github.service_restart_cmd", "systemctl restart odoo")
                                        try:
                                            if service_restart_cmd.startswith("http"):
                                                requests.post(service_restart_cmd)
                                            else:
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
                                repo_webhook_token.message_post(body=_(e.stderr.decode("utf-8")))
                        except subprocess.CalledProcessError as e:
                            _logger.exception(e.output)
                return {"status": "success", "code": 200}
            else:
                return {"status": "Branch not registered", "code": 422}
        else:
            return {"status": "Forbidden", "code": 403}

    @route('/github/database/backup_now', type='http', auth="user", methods=['GET'], csrf=False)
    def backup_database_now(self):
        try:
            backup_format = "zip"
            dbname = request.env.cr.dbname
            ts = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            filename = "%s_%s.%s" % (dbname, ts, backup_format)
            headers = [
                ('Content-Type', 'application/octet-stream; charset=binary'),
                ('Content-Disposition', content_disposition(filename)),
            ]
            dump_stream = odoo.service.db.dump_db(dbname, None, backup_format)
            response = werkzeug.wrappers.Response(dump_stream, headers=headers, direct_passthrough=True)
            return response
        except Exception as e:
            _logger.exception('Database.backup %s' % e)
            return {"status": "Forbidden", "code": 403}
