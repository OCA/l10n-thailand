from odoo import fields, models


class AccountTaxFilingLine(models.Model):
    _name = "account.tax.filing.line"
    _description = "Account Tax Filing Line"

    name = fields.Char(
        string="Description",
        required=True,
        default="/",
    )
    filing_id = fields.Many2one(
        comodel_name="account.tax.filing",
        string="Tax Filing",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        readonly=True,
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        readonly=True,
    )
    debit = fields.Monetary(
        default=0.0,
        readonly=True,
        currency_field="currency_id",
    )
    credit = fields.Monetary(
        default=0.0,
        readonly=True,
        currency_field="currency_id",
    )
    date = fields.Date(
        readonly=True,
    )
    balance = fields.Monetary(
        default=0.0,
        currency_field="currency_id",
    )
    display_type = fields.Selection(
        selection=[("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
