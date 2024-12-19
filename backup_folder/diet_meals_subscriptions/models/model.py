from odoo import _, api, fields, models
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import functools
from random import randrange
from odoo.osv.expression import get_unaccent_wrapper
import re
from odoo.tools import format_datetime


class CustomWeekdays(models.Model):
    _name = "custom.weekdays"

    def name_get(self):
        result = []
        for rec in self:
            name = dict(self._fields["day"].selection).get(rec.day)
            result.append((rec.id, name))
        return result

    day = fields.Selection(
        [
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        required=True,
    )


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Res Partner"

    def get_number(self, number):
        if number.startswith("00965"):
            return number[5:]
        if number.startswith("+965"):
            return number[4:]
        return number

    @api.model
    def create(self, values):
        if values.get("phone"):
            values["phone"] = self.get_number(values.get("phone"))
        if values.get("mobile"):
            values["mobile"] = self.get_number(values.get("mobile"))
        if values.get("phone") and not values.get("phone").startswith(
            ("00965", "+965")
        ):
            values["phone"] = "00965" + values.get("phone")
        if values.get("mobile") and not values.get("mobile").startswith(
            ("00965", "+965")
        ):
            values["mobile"] = "00965" + values.get("mobile")
        if values.get("phone") and not values.get("mobile"):
            values["mobile"] = values.get("phone")
        return super(ResPartner, self).create(values)

    def write(self, values):
        for p in self:
            if values.get("phone"):
                values["phone"] = self.get_number(values.get("phone"))
            if values.get("mobile"):
                values["mobile"] = self.get_number(values.get("mobile"))
            if values.get("phone") and not values.get("phone").startswith(
                ("00965", "+965")
            ):
                values["phone"] = "00965" + values.get("phone")
            if values.get("mobile") and not values.get("mobile").startswith(
                ("00965", "+965")
            ):
                values["mobile"] = "00965" + values.get("mobile")
            if values.get("phone") and not values.get("mobile"):
                values["mobile"] = values.get("phone")
        return super(ResPartner, self).write(values)

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, order=None):
        if args is None:
            args = []
        order_by_rank = self.env.context.get("res_partner_search_mode")
        if (name or order_by_rank) and operator in (
            "=",
            "ilike",
            "=ilike",
            "like",
            "=like",
        ):
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, "read")
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            from_str = from_clause if from_clause else "res_partner"
            where_str = where_clause and (" WHERE %s AND " % where_clause) or " WHERE "

            search_name = name
            if operator in ("ilike", "like"):
                search_name = "%%%s%%" % name
            if operator in ("=ilike", "=like"):
                operator = operator[1:]

            unaccent = self.env.cr.unaccent

            fields = self._get_name_search_order_by_fields()

            query = f"""SELECT res_partner.id
                         FROM {from_str}
                      {where_str} ({unaccent('res_partner.email')} {operator} %s
                           OR {unaccent('res_partner.phone')} {operator} %s
                           OR {unaccent('res_partner.mobile')} {operator} %s
                           OR {unaccent('res_partner.display_name')} {operator} %s
                           OR {unaccent('res_partner.ref')} {operator} %s
                           OR {unaccent('res_partner.vat')} {operator} %s)
                     ORDER BY {fields} {unaccent('res_partner.display_name')} {operator} %s DESC,
                              {unaccent('res_partner.display_name')}
                    """

            where_clause_params += [
                search_name
            ] * 5  # for email, display_name, reference, phone, mobile
            where_clause_params += [
                re.sub("[^a-zA-Z0-9\-\.]+", "", search_name) or None
            ]  # for vat
            where_clause_params += [search_name]  # for order by
            if limit:
                query += " limit %s"
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            return [row[0] for row in self.env.cr.fetchall()]

        return super(ResPartner, self)._name_search(
            name, args, operator=operator, limit=limit, order=order
        )


class DietPackagesLine(models.Model):
    _name = "diet.packages.line"
    _description = "Diet Packages Line"

    package_id = fields.Many2one("diet.packages")
    categ_ids = fields.Many2many("diet.category", required=True)
    quantity = fields.Integer(default=1)
    use_in_diet_meal = fields.Boolean(
        string="Use in diet meal", related="package_id.product_id.diet_meal_ok"
    )


class SubscriptionTemplate(models.Model):
    _name = "subscription.template"
    _description = "Subscription Template"

    name = fields.Char(required=True, translate=True)
    number_of_days = fields.Integer(required=True)


class DietPackages(models.Model):
    _name = "diet.packages"
    _inherit = [
        "portal.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "ksc.mixin",
        "base.whatsapp.mixin",
    ]
    _description = "Diet Packages"

    name = fields.Char(required=True, translate=True)
    image = fields.Binary()
    description = fields.Text(translate=True)
    template_id = fields.Many2one("subscription.template", required=True)
    number_of_days = fields.Integer(related="template_id.number_of_days")
    product_id = fields.Many2one(
        "product.product", domain="[('package_ok', '=', True)]", required=True
    )
    price = fields.Float(related="product_id.lst_price")
    allowed_freeze = fields.Boolean()
    freeze = fields.Integer("Freeze")
    categ_ids = fields.Many2many("diet.category", string="Category ids")
    number_off_days = fields.Selection(
        [
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
        ],
        default="2",
        required=True,
    )

    package_line_ids = fields.One2many("diet.packages.line", "package_id")


class ProductCategory(models.Model):
    _inherit = "product.category"
    _description = "Product Category"

    diet_ok = fields.Boolean("Use in Dite")
    name = fields.Char(translate=True)


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Product Template"

    package_ok = fields.Boolean("Use in Package")
    diet_meal_ok = fields.Boolean(
        "Use in Dite Meal",
    )
    # category_ids = fields.Many2one('diet.category', string="Category")
    category_ids = fields.Many2one("diet.category", string="Category")
    color = fields.Integer(related="category_ids.color", string="Color")

    total_calories = fields.Integer()


class DietSubscriptionsFreeze(models.Model):
    _name = "diet.subscriptions.freeze"
    _description = "Diet Subscriptions Freeze"

    subscriptions_id = fields.Many2one("diet.meals.subscriptions")
    start_date = fields.Date(readonly=False, tracking=True)
    freeze = fields.Integer()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
    )

    def auto_action_freeze_subscriptions(self):
        today = fields.Date.context_today(self)
        diet_subscriptions_freeze_ids = self.search(
            [("state", "=", "draft"), ("start_date", "=", "today")]
        )
        for rec in diet_subscriptions_freeze_ids:
            rec.state = "done"


class DietMealsSubscriptions(models.Model):
    _name = "diet.meals.subscriptions"
    _description = "Diet Meals Subscriptions"
    _inherit = [
        "portal.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "ksc.mixin",
        "base.whatsapp.mixin",
    ]

    name = fields.Char(readonly=True, copy=False, tracking=True)
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    image_128 = fields.Binary(
        related="partner_id.image_128", string="Image", readonly=True
    )
    start_date = fields.Date(readonly=False, tracking=True)
    end_date = fields.Date(compute="_compute_end_date", tracking=True)
    package_id = fields.Many2one("diet.packages", required=True, tracking=True)
    number_of_days = fields.Integer(related="package_id.number_of_days")
    product_id = fields.Many2one("product.product", related="package_id.product_id")
    number_off_days = fields.Selection(
        related="package_id.number_off_days", readonly=True
    )

    invoice_id = fields.Many2one("account.move", tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("invoiced", "Invoiced"),
            ("in_progrees", "In Progrees"),
            ("freeze", "Freeze"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        group_expand="_expand_groups",
        string="State",
        default="draft",
        readonly=True,
        required=True,
        copy=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company.id
    )
    off_days_ids = fields.Many2many("custom.weekdays")

    freeze_ids = fields.One2many("diet.subscriptions.freeze", "subscriptions_id")
    freeze = fields.Integer(compute="_compute_freeze")
    allowed_freeze_days = fields.Integer(compute="_compute_allowed_freeze_days")
    allowed_freeze = fields.Boolean(related="package_id.allowed_freeze")
    minDate = fields.Char(compute="_get_minDate")
    order_ids = fields.One2many("diet.order", "subscriptions_id")

    @api.depends("end_date")
    def _get_minDate(self):
        for rec in self:
            today = fields.Date.context_today(self)
            today += relativedelta(days=2)
            rec.minDate = (rec.start_date or today).strftime("%Y-%m-%d")

    def action_create_orders(self):
        if self.start_date and self.end_date and self.package_id:
            days = self.off_days_ids.mapped("day")
            date = self.start_date
            orders = []
            while date <= self.end_date:
                order_id = self.env["sale.order"].create(
                    {
                        "partner_id": self.partner_id.id,
                        "package_id": self.package_id.id,
                        "date_order": date,
                    }
                )
                if str(date.weekday()) not in days:
                    orders.append(
                        {
                            "date": date,
                            "subscriptions_id": self.id,
                            "order_id": order_id.id,
                            "line_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "quantity": line.quantity,
                                        "categ_ids": [(6, 0, line.categ_ids.ids)],
                                    },
                                )
                                for line in self.package_id.package_line_ids
                            ],
                        }
                    )
                date += relativedelta(days=1)
            if orders:
                self.env["diet.order"].create(orders)

    def _compute_freeze(self):
        for rec in self:
            rec.freeze = sum(
                rec.freeze_ids.filtered(lambda line: line.state == "done").mapped(
                    "freeze"
                )
            )

    @api.depends("freeze", "package_id")
    def _compute_allowed_freeze_days(self):
        for rec in self:
            rec.allowed_freeze_days = rec.package_id.freeze - rec.freeze

    @api.depends(
        "start_date",
        "freeze",
        "package_id",
        "number_of_days",
        "off_days_ids",
        "number_off_days",
        "freeze_ids",
    )
    def _compute_end_date(self):
        for rec in self:
            rec.end_date = fields.Date.context_today(self)
            if rec.start_date and rec.package_id:
                days = rec.off_days_ids.mapped("day")
                start_date = rec.start_date
                number_of_days = rec.number_of_days
                end = number_of_days + rec.freeze - 1
                end_date = start_date + relativedelta(days=end)
                while start_date != end_date:
                    if str(start_date.weekday()) in days:
                        end += 1
                    start_date += relativedelta(days=1)
                end_date = rec.start_date + relativedelta(days=end)
                while str(end_date.weekday()) in days:
                    end_date += relativedelta(days=1)
                rec.end_date = end_date

    @api.constrains("freeze", "package_id", "package_id.freeze")
    def _validate_freeze(self):
        for rec in self:
            if rec.freeze > rec.package_id.freeze:
                raise ValidationError(
                    _("freeze must be equal or less than freeze in package")
                )

    @api.constrains("off_days_ids", "package_id", "package_id.number_off_days")
    def _validate_off_days_ids(self):
        for rec in self:
            if len(rec.off_days_ids) > int(rec.package_id.number_off_days):
                raise ValidationError(
                    _("off days must be equal or less than number off days in package")
                )

    @api.model
    def _expand_groups(self, states, domain, order):
        return ["draft", "invoiced", "in_progrees", "freeze", "done", "cancel"]

    def action_subscriptions_freeze(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Freeze"),
            "res_model": "freeze.wizard",
            "view_mode": "form",
            "context": {
                "default_subscriptions_id": self.id,
                "start_date": self.start_date,
            },
            "target": "new",
        }

    def action_subscriptions_unfreeze(self):
        self.state = "in_progrees"

    def auto_action_subscriptions_done(self):
        today = fields.Date.context_today(self)
        diet_meals_subscriptions_ids = self.search([("state", "=", "in_progrees")])
        for rec in diet_meals_subscriptions_ids:
            if today > rec.end_date:
                rec.action_subscriptions_done()

    def auto_action_subscriptions_msg_before_done(self):
        today = fields.Date.context_today(self)
        diet_meals_subscriptions_ids = self.search([("state", "=", "in_progrees")])
        for rec in diet_meals_subscriptions_ids:
            if today == rec.end_date - timedelta(days=1):
                rec.send_whatsapp_message(
                    rec.company_id.sudo().wa_diet_meals_subscriptions_end_message
                )

    def action_subscriptions_done(self):
        self.env.user.notify_danger(
            message="Message Not Send Due To Your Phone Connection",
            title="hello",
            sticky="goo",
        )
        self.state = "done"

    def action_subscriptions_cancel(self):
        self.state = "cancel"

    def send_whatsapp_message(self, msg_exp):
        if msg_exp and self.partner_id and self.partner_id.mobile:
            try:
                msg = eval(
                    msg_exp,
                    {
                        "object": self,
                        "format_datetime": lambda dt, tz=False, dt_format=False, lang_code=False: format_datetime(
                            self.env, dt, tz, dt_format, lang_code
                        ),
                    },
                )
            except:
                raise UserError(
                    _(
                        "Configured Message fromat is wrong please contact administrator correct it first."
                    )
                )
            self.with_context(force_send=True).send_whatsapp(
                msg, self.partner_id.mobile, self.partner_id
            )

    def action_subscriptions_run(self):
        if not self.start_date:
            self.start_date = fields.Date.context_today(self)
        self.state = "in_progrees"
        self.action_create_orders()
        self.send_whatsapp_message(
            self.company_id.sudo().wa_diet_meals_subscriptions_start_message
        )

    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code(
            "diet.meals.subscriptions"
        )
        return super(DietMealsSubscriptions, self).create(values)

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("You can not delete record not in draft state"))
        return super(DietMealsSubscriptions, self).unlink()

    def create_invoice(self):
        product_id = self.product_id
        if not product_id:
            raise UserError(_("Please Set Subscription Template first."))
        product_data = [{"product_id": product_id}]
        inv_data = {}
        invoice = self.ksc_create_invoice(
            partner=self.partner_id, product_data=product_data, inv_data=inv_data
        )
        self.invoice_id = invoice.id
        self.state = "invoiced"
        return self.view_invoice()

    def view_invoice(self):
        invoices = self.mapped("invoice_id")
        action = self.ksc_action_view_invoice(invoices)
        action["context"].update(
            {
                "default_partner_id": self.partner_id.id,
            }
        )
        return action


class SaleOrder(models.Model):
    _inherit = "sale.order"

    package_id = fields.Many2one("diet.packages")
