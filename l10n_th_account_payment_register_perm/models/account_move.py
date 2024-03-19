# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_register_payment(self):
        res = super().action_register_payment()
        res["name"] = _("Register Payment Form")
        res["res_model"] = "account.payment.register.perm"
        res["target"] = "current"
        return res
