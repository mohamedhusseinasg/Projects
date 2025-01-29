from odoo import _, api, fields, models
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


# class KitchenMealDay(models.Model):
#     _name = 'kitchen.meal.day'
#     _description = 'Kitchen Meal Day'
#     _rec_name = 'date'

#     date = fields.Date(required=True)
#     kitchen_meal_ids = fields.Many2many('kitchen.meals')
    # dinner_meal_ids = fields.Many2many('kitchen.dinner.meal')
    # launch_meal_ids = fields.Many2many('kitchen.launch.meal')
    # snacks_meal_ids = fields.Many2many('kitchen.snacks.meal')


class KitchenMeals(models.Model):
    _name = 'kitchen.meals'
    _description = 'Kitchen Meals'

    name = fields.Char('Name', translate=True, required=True)
    color = fields.Integer(related='category_id.color')
    product_id = fields.Many2one('product.template', readonly=True)
    description = fields.Text(required=True, translate=True)
    image = fields.Image(required=True)
    sale_price = fields.Float(required=True)
    category_id=fields.Many2one('diet.category',string="Category")
   

    def create_product(self):
        product_id = self.env['product.template'].sudo().create({
            'name': self.name,
            'list_price': self.sale_price,
            'description_sale': self.description,
            'image_1920': self.image,
            'diet_meal_ok':True,
            'color':self.color,
            'category_ids':self.category_id.id
           
        })
        self.product_id = product_id.id

    @api.model
    def create(self, vals):
        res = super(KitchenMeals, self).create(vals)
        res.create_product()
        return res


# class KitchenDinnerMeal(models.Model):
#     _name = 'kitchen.dinner.meal'
#     _description = 'Kitchen Dinner Meal'

#     name = fields.Char('Name', translate=True, required=True)
#     color = fields.Integer()
#     product_id = fields.Many2one('product.template', readonly=True)
#     description = fields.Text(required=True, translate=True)
#     image = fields.Image(required=True)
#     sale_price = fields.Float(required=True)

#     def create_product(self):
#         product_id = self.env['product.template'].sudo().create({
#             'name': self.name,
#             'list_price': self.sale_price,
#             'description_sale': self.description,
#             'image_1920': self.image,
#         })
#         self.product_id = product_id.id

#     @api.model
#     def create(self, vals):
#         res = super(KitchenBreakfastMeal, self).create(vals)
#         res.create_product()
#         return res


# class KitchenLaunchMeal(models.Model):
#     _name = 'kitchen.launch.meal'
#     _description = 'Kitchen Launch Meal'

#     name = fields.Char('Name', translate=True, required=True)
#     color = fields.Integer()
#     product_id = fields.Many2one('product.template', readonly=True)
#     description = fields.Text(required=True, translate=True)
#     image = fields.Image(required=True)
#     sale_price = fields.Float(required=True)

#     def create_product(self):
#         product_id = self.env['product.template'].sudo().create({
#             'name': self.name,
#             'list_price': self.sale_price,
#             'description_sale': self.description,
#             'image_1920': self.image,
#         })
#         self.product_id = product_id.id

#     @api.model
#     def create(self, vals):
#         res = super(KitchenBreakfastMeal, self).create(vals)
#         res.create_product()
#         return res


# class KitchenSnacksMeal(models.Model):
#     _name = 'kitchen.snacks.meal'
#     _description = 'Kitchen Snacks Meal'

#     name = fields.Char('Name', translate=True, required=True)
#     color = fields.Integer()
#     product_id = fields.Many2one('product.template', readonly=True)
#     description = fields.Text(required=True, translate=True)
#     image = fields.Image(required=True)
#     sale_price = fields.Float(required=True)

#     def create_product(self):
#         product_id = self.env['product.template'].sudo().create({
#             'name': self.name,
#             'list_price': self.sale_price,
#             'description_sale': self.description,
#             'image_1920': self.image,
#         })
#         self.product_id = product_id.id

#     @api.model
#     def create(self, vals):
#         res = super(KitchenBreakfastMeal, self).create(vals)
#         res.create_product()
#         return res
