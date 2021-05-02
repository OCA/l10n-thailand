# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models


class Expense(models.Model):
    _name = "hr.expense"
    _inherit = ["hr.expense", "base.company.novat"]
    _tax_field_name = "tax_ids"
