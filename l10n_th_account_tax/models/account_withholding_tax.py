# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .withholding_tax_cert import INCOME_TAX_FORM, WHT_CERT_INCOME_TYPE


class AccountWithholdingTax(models.Model):
    _name = "account.withholding.tax"
    _description = "Account Withholding Tax"
    _check_company_auto = True

    name = fields.Char(required=True)
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Withholding Tax Account",
        domain="[('wht_account', '=', True), ('company_id', '=', company_id)]",
        required=True,
        ondelete="restrict",
    )
    amount = fields.Float(
        string="Percent",
    )
    is_pit = fields.Boolean(
        string="Personal Income Tax",
        help="As PIT, the calculation of withholding amount is based on pit.rate",
    )
    pit_id = fields.Many2one(
        comodel_name="personal.income.tax",
        string="PIT Rate",
        compute="_compute_pit_id",
        help="Latest PIT Rates used to calcuate withholiding amount",
    )
    income_tax_form = fields.Selection(
        selection=INCOME_TAX_FORM,
        string="Default Income Tax Form",
    )
    wht_cert_income_type = fields.Selection(
        selection=WHT_CERT_INCOME_TYPE,
        string="Default Type of Income",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ("name_unique", "UNIQUE(name,company_id)", "Name must be unique!"),
    ]

    @api.constrains("is_pit")
    def _check_is_pit(self):
        pits = self.search_count([("is_pit", "=", True)])
        if pits > 1:
            raise ValidationError(_("Only 1 personal income tax allowed!"))

    @api.constrains("account_id")
    def _check_account_id(self):
        for rec in self:
            if rec.account_id and not rec.account_id.wht_account:
                raise ValidationError(_("Selected account is not for withholding tax"))

    @api.depends("is_pit")
    def _compute_pit_id(self):
        pit_date = self.env.context.get("pit_date") or fields.Date.context_today(self)
        pit = self.env["personal.income.tax"].search(
            [("effective_date", "<=", pit_date)], order="effective_date desc", limit=1
        )
        self.update({"pit_id": pit.id})
