# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class Users(models.Model):
    _inherit = "res.users"

    @api.onchange("title", "firstname", "lastname")
    def _compute_name(self):
        return super()._compute_name()
