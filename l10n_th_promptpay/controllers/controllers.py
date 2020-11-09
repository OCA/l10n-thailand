# -*- coding: utf-8 -*-
# from odoo import http


# class L10nThPromptpay(http.Controller):
#     @http.route('/l10n_th_promptpay/l10n_th_promptpay/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_th_promptpay/l10n_th_promptpay/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_th_promptpay.listing', {
#             'root': '/l10n_th_promptpay/l10n_th_promptpay',
#             'objects': http.request.env['l10n_th_promptpay.l10n_th_promptpay'].search([]),
#         })

#     @http.route('/l10n_th_promptpay/l10n_th_promptpay/objects/<model("l10n_th_promptpay.l10n_th_promptpay"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_th_promptpay.object', {
#             'object': obj
#         })
