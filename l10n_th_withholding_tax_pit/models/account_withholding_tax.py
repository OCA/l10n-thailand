# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountWithholdingTax(models.Model):
    _inherit = "account.withholding.tax"

    account_pit = fields.Boolean(
        string="Personal Income Tax",
        help="As PIT, the calculation of withholding amount is based on pit.rate",
    )
    pit_id = fields.Many2one(
        comodel_name="personal.income.tax",
        string="PIT Rate",
        compute="_compute_pit_id",
        help="Latest PIT Rates used to calcuate withholiding amount",
    )
    _sql_constraints = [
        ("account_pit_unique", "UNIQUE(account_pit)", "Only one PIT is allowed!"),
    ]

    @api.depends("account_pit")
    def _compute_pit_id(self):
        pit_date = self.env.context.get("pit_date") or fields.Date.context_today(self)
        pit = self.env["personal.income.tax"].search(
            [("effective_date", "<=", pit_date)], order="effective_date desc", limit=1
        )
        self.update({"pit_id": pit.id})
