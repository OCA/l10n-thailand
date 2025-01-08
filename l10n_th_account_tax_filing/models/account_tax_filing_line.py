# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTaxFilingLine(models.Model):
    _name = "account.tax.filing.line"
    _description = "Account Tax Filing Line"
    _order = "sequence, account_id, date, balance"

    sequence = fields.Integer(
        default=10,
        help="Used to order tax filing lines",
    )
    name = fields.Char(string="Description")
    filing_id = fields.Many2one(
        comodel_name="account.tax.filing",
        string="Tax Filing",
        required=True,
        readonly=True,
        index=True,
        ondelete="restrict",
    )
    parent_state = fields.Selection(
        related="filing_id.state",
        readonly=True,
        store=True,
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
        index=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        readonly=True,
    )
    debit = fields.Monetary(
        default=0.0,
        readonly=True,
    )
    credit = fields.Monetary(
        default=0.0,
        readonly=True,
    )
    date = fields.Date(
        readonly=True,
    )
    balance = fields.Monetary(
        default=0.0,
        readonly=True,
    )
    display_type = fields.Selection(
        selection=[("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
