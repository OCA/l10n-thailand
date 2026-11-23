# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankPaymentProfile(models.Model):
    _inherit = "bank.payment.profile"

    bank = fields.Selection(
        selection_add=[("KASITHBK", "KBank")],
        ondelete={"KASITHBK": "cascade"},
    )
