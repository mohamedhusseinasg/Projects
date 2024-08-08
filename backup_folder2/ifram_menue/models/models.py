import logging
from odoo import models, fields, api
from xml.sax.saxutils import escape

_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError

class IframeContent(models.Model):
    _name = 'iframe.iframe'
    _description = 'Iframe Content'

    name = fields.Char(string='Iframe Name', required=True, store=True)
    allowed_user = fields.Many2many('res.users', string='Allowed Users', required=True)
    iframe_url = fields.Char(string='Iframe URL', store=True)
    web_icon_image = fields.Binary(string='Web Icon Image', store=True)
    menu_id = fields.Many2one('ir.ui.menu', string='Menu Item', ondelete='set null')
    group_id = fields.Many2one('res.groups', string='User Group', ondelete='cascade')
    parent_menu_id = fields.Many2one('ir.ui.menu', string='Parent Menu', ondelete='set null')


    # override the create method to create menu item and user group automatically with users in allowed_user
    @api.model
    def create(self, vals):
        if 'name' not in vals or not vals.get('name'):
            raise ValidationError("The 'name' field is required.")
        record = super(IframeContent, self).create(vals)
        group = self.create_user_group(record)
        form_view = self.create_form_view(record)
        self.create_menu_item(record, group, form_view)
        return record

    # override the write method to update menu item and user group
    def write(self, vals):
        res = super(IframeContent, self).write(vals)
        for record in self:
            if 'name' in vals or 'web_icon_image' in vals or 'allowed_user' in vals or 'parent_menu_id' in vals:
                self.update_user_group(record)
                self.update_menu_item(record, vals)
            if 'iframe_url' in vals:
                self.update_form_view(record, vals['iframe_url'])
        return res

    # override the unlink method to delete menu item if i delete the iframe record
    def unlink(self):
        for record in self:
            self.delete_menu_item(record)
            if record.group_id:
                record.group_id.unlink()
            self.delete_form_view(record)
        return super(IframeContent, self).unlink()

  # create user group with users in allowed_user and assign it to menu item
    def create_user_group(self, record):
        group_vals = {
            'name': 'Group for {}'.format(record.name),
            'users': [(6, 0, record.allowed_user.ids)],
            'is_iframe_group': True,
        }
        group = self.env['res.groups'].create(group_vals)
        record.group_id = group.id
        return group

    # update user group with users if users in allowed_user changed
    def update_user_group(self, record):
        if record.group_id:
            record.group_id.write({'users': [(6, 0, record.allowed_user.ids)]})
        else:
            self.create_user_group(record)

    # create form view with url in field iframe_url
    def create_form_view(self, record):
        arch_base = """
               <form string="Embedded Webpage" edit="false" create="false">
                   <div style="position:absolute; left:0; top:0; width:100%; height:100%;">
                       <iframe src="{url}"
                               width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" scrolling="yes"
                               style="border-width:0px;">
                       </iframe>
                   </div>
               </form>
           """.format(url=record.iframe_url)
        view_vals = {
            'name': 'form.iframe.{}'.format(record.id),
            'type': 'form',
            'priority': 20,
            'model': 'iframe.iframe',
            'arch_base': arch_base,
        }
        form_view = self.env['ir.ui.view'].create(view_vals)
        return form_view

    # update form view with new url
    def update_form_view(self, record, url):
        if record.menu_id:
            form_view = self.env['ir.ui.view'].search([('name', '=', 'form.iframe.{}'.format(record.id))])
            if form_view:
                arch_base = """
                       <form string="Embedded Webpage" edit="false" create="false">
                           <div style="position:absolute; left:0; top:0; width:100%; height:100%;">
                               <iframe src="{url}"
                                       width="100%" height="100%" marginwidth="0" marginheight="0" frameborder="no" scrolling="yes"
                                       style="border-width:0px;">
                               </iframe>
                           </div>
                       </form>
                   """.format(url=record.iframe_url)
                form_view.write({'arch_base': arch_base})

    # create menu item with user group and url action and group to menuitem
    def create_menu_item(self, record, group, form_view):
        if not record.allowed_user:
            return  # Skip creating menu item if no allowed users are specified

        # Create window action
        window_action_vals = {
            'name': record.name,
            'res_model': 'iframe.iframe',
            'view_mode': 'form',
            'view_id': form_view.id,
            'target': 'current',
            'context': {'default_iframe_url': record.iframe_url},
        }
        window_action = self.env['ir.actions.act_window'].create(window_action_vals)

        # Create menu item
        menu_vals = {
            'name': record.name,
            'parent_id': record.parent_menu_id.id if record.parent_menu_id else None,  # Conditionally set parent_menu_id
            'action': 'ir.actions.act_window,{}'.format(window_action.id),
            'sequence': record.id,
            'web_icon_data': record.web_icon_image,
            'groups_id': [(6, 0, [group.id])],
        }

        menu = self.env['ir.ui.menu'].sudo().create(menu_vals)
        record.menu_id = menu.id

    # update menu item if name or iframe_url changed or image changed or parent menu changed
    def update_menu_item(self, record, vals):
        menu_item = record.menu_id
        if menu_item:
            action = menu_item.action
            if action:
                action_vals = {
                    'name': vals.get('name', record.name),
                    'context': {'default_iframe_url': vals.get('iframe_url', record.iframe_url)},
                }
                action.write(action_vals)

            menu_vals = {
                'name': vals.get('name', record.name),
                'web_icon_data': vals.get('web_icon_image', record.web_icon_image),
            }
            if 'parent_menu_id' in vals:
                menu_vals['parent_id'] = vals['parent_menu_id']

            menu_item.write(menu_vals)

    # delete menu item if name of iframe record deleted
    def delete_menu_item(self, record):
        menu_items = self.env['ir.ui.menu'].search([
            ('name', '=', record.name),
        ])
        if menu_items:
            menu_items.unlink()

    # delete form view if name of iframe record deleted
    def delete_form_view(self, record):
        form_view = self.env['ir.ui.view'].search([('name', '=', 'form.iframe.{}'.format(record.id))])
        if form_view:
            form_view.unlink()

