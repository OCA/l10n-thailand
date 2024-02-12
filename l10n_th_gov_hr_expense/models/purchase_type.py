# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class PurchaseType(models.Model):
    _inherit = "purchase.type"

    visible_on_expense = fields.Boolean(string="Expense")
