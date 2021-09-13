# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.l10n_th_withholding_tax_cert.models.withholding_tax_cert import (
    WHT_CERT_INCOME_TYPE,
)


class AccountMove(models.Model):
    _inherit = "account.move"

    account_pit = fields.Boolean(
        string="Account PIT",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )
    pit_wht_cert_income_type = fields.Selection(
        WHT_CERT_INCOME_TYPE,
        string="Type of Income",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )
