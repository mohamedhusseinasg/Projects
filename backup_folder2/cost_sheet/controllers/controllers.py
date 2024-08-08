# -*- coding: utf-8 -*-
# from odoo import http


# class CostSheet(http.Controller):
#     @http.route('/cost_sheet/cost_sheet', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cost_sheet/cost_sheet/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cost_sheet.listing', {
#             'root': '/cost_sheet/cost_sheet',
#             'objects': http.request.env['cost_sheet.cost_sheet'].search([]),
#         })

#     @http.route('/cost_sheet/cost_sheet/objects/<model("cost_sheet.cost_sheet"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cost_sheet.object', {
#             'object': obj
#         })
