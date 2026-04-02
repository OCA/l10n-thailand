# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankTemplate(models.Model):
    _inherit = "bank.template"

    bank = fields.Selection(
        selection_add=[("KASITHBK", "KBank")],
        ondelete={"KASITHBK": "cascade"},
    )
    kbank_transfer_type = fields.Selection(
        selection=[
            ("same_bank", "Same Bank"),
            ("other_bank", "Other Bank"),
        ],
        string="Transfer Type",
    )
