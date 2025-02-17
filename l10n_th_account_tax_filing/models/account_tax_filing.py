# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountTaxFiling(models.Model):
    _name = "account.tax.filing"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Account Transfer Tax Filing"
    _check_company_auto = True
    _order = "id desc"

    name = fields.Char(
        required=True,
        index=True,
        readonly=True,
        copy=False,
        default="Draft",
    )
    date_range_id = fields.Many2one(
        comodel_name="date.range",
        string="Date range",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_from = fields.Date(
        string="Start Date",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_to = fields.Date(
        string="End Date",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    account_from_id = fields.Many2one(
        comodel_name="account.account",
        required=True,
        check_company=True,
        copy=False,
        default=lambda self: self.env.company.account_from_id,
    )
    account_to_id = fields.Many2one(
        comodel_name="account.account",
        required=True,
        copy=False,
        check_company=True,
        default=lambda self: self.env.company.account_to_id,
    )
    account_adjust_id = fields.Many2one(
        comodel_name="account.account",
        check_company=True,
        default=lambda self: self.env.company.account_adjust_id,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entries",
        readonly=True,
        copy=False,
    )
    move_type = fields.Selection(
        related="move_id.move_type",
        readonly=True,
        store=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submit", "Submitted"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="draft",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self.env.company,
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency", related="company_id.currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        readonly=True,
        required=True,
        default=lambda self: self.env.company.tax_authority_id,
        states={"draft": [("readonly", False)]},
        copy=False,
        check_company=True,
    )
    amount_from = fields.Monetary(
        currency_field="company_currency_id",
        compute="_compute_total_amount",
        store=True,
    )
    amount_to = fields.Monetary(
        currency_field="company_currency_id",
        compute="_compute_total_amount",
        store=True,
    )
    amount_adjust = fields.Monetary(
        string="Total Adjust",
        currency_field="company_currency_id",
        compute="_compute_total_amount",
        store=True,
    )
    diff_amount = fields.Monetary(
        string="Difference amount",
        currency_field="company_currency_id",
        compute="_compute_total_amount",
        store=True,
    )
    total_amount = fields.Monetary(
        currency_field="company_currency_id",
        compute="_compute_total_amount",
        store=True,
    )
    tax_filing_line_ids = fields.One2many(
        comodel_name="account.tax.filing.line",
        inverse_name="filing_id",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.model
    def create(self, vals):
        # Set name based on sequence
        if vals.get("name", "Draft") == "Draft":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("account.tax.filing") or "Draft"
            )
        return super(AccountTaxFiling, self).create(vals)

    @api.onchange("date_range_id")
    def _onchange_date_range(self):
        # Set date_from and date_to based on date_range_id
        for rec in self:
            if rec.date_range_id:
                rec.update(
                    {
                        "date_from": rec.date_range_id.date_start,
                        "date_to": rec.date_range_id.date_end,
                    }
                )

    @api.depends("tax_filing_line_ids")
    def _compute_total_amount(self):
        for rec in self:
            balances = defaultdict(float)  # ใช้ float เพื่อสะสมค่า balance
            for line in rec.tax_filing_line_ids.filtered(lambda l: not l.display_type):
                balances[line.account_id] += line.balance
            amount_from = abs(balances.get(rec.account_from_id, 0))
            amount_to = abs(balances.get(rec.account_to_id, 0))
            amount_adjust = abs(balances.get(rec.account_adjust_id, 0))
            diff_amount = amount_adjust - (amount_from - amount_to)
            total_amount = (amount_from - amount_to) * -1
            if amount_adjust != 0:
                total_amount += amount_adjust

            rec.amount_from = amount_from
            rec.amount_to = amount_to
            rec.amount_adjust = amount_adjust
            rec.diff_amount = diff_amount
            rec.total_amount = total_amount

    @api.constrains("date_from", "date_to")
    def check_date_from_to(self):
        # Check date form can't be after date to
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(_("Start Date must not be after End Date"))

    def _get_account(self):
        accounts = self.account_from_id + self.account_to_id + self.account_adjust_id
        return accounts

    def _get_section(self):
        section = [("Journal Entries", 10), ("Invoice Lines", 30)]
        return section

    def action_compute_account_tax_filing_line(self):
        # Clear all lines before recompute (if any)
        self.tax_filing_line_ids.unlink()

        accounts = self._get_account()

        query = """
            SELECT aml.id, aml.account_id, aml.name,
            aml.date, aml.debit, aml.credit, aml.balance
            FROM account_move_line aml
            WHERE aml.account_id IN %s
            AND aml.date BETWEEN %s AND %s
            AND aml.parent_state = 'posted'
            AND aml.tax_filing_id IS NULL
            AND aml.company_id = %s
            AND NOT EXISTS (
                SELECT 1
                FROM account_tax_filing_line filing_line
                WHERE filing_line.move_line_id = aml.id
                AND filing_line.parent_state != 'cancel'
            )
            """
        self.env.cr.execute(
            query,
            (
                tuple(accounts.ids),
                self.date_from,
                self.date_to,
                self.company_id.id,
            ),
        )
        result = self.env.cr.dictfetchall()
        self.tax_filing_line_ids = [
            Command.create(
                {
                    "account_id": res["account_id"],
                    "name": res["name"],
                    "date": res["date"].strftime("%Y-%m-%d"),
                    "debit": res["debit"],
                    "credit": res["credit"],
                    "move_line_id": res["id"],
                    "balance": res["balance"],
                    "sequence": 20
                    if res["account_id"] == self.account_adjust_id.id
                    else 40,
                }
            )
            for res in result
        ]
        if self.tax_filing_line_ids:
            section_type = self._get_section()
            self.tax_filing_line_ids = [
                Command.create(
                    {
                        "display_type": "line_section",
                        "name": name,
                        "sequence": sequence,
                        "filing_id": self.id,
                    }
                )
                for name, sequence in section_type
            ]

    def prepare_invoice_line(self, account, amount, sign):
        return {
            "name": account.name,
            "account_id": account.id,
            "price_unit": amount * sign,
            "tax_filing_id": self.id,
        }

    def create_invoice_line(self, move_type):
        # toggle amount with sign
        sign = -1 if move_type == "out_invoice" else 1
        invoice_lines = []
        if self.account_from_id and self.amount_from > 0:
            invoice_lines.append(
                Command.create(
                    self.prepare_invoice_line(
                        self.account_from_id,
                        self.amount_from,
                        sign,
                    )
                )
            )
        if self.account_to_id and self.amount_to > 0:
            invoice_lines.append(
                Command.create(
                    self.prepare_invoice_line(
                        self.account_to_id,
                        self.amount_to,
                        sign * -1,
                    )
                )
            )
        if self.account_adjust_id and self.amount_adjust > 0:
            invoice_lines.append(
                Command.create(
                    self.prepare_invoice_line(
                        self.account_adjust_id,
                        self.amount_adjust,
                        sign * -1,
                    )
                )
            )
        return invoice_lines

    def create_invoice(self, move_type):
        # Create invoice
        invoice = {
            "move_type": move_type,
            "partner_id": self.partner_id.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": self.create_invoice_line(move_type),
        }
        return invoice

    def prepare_account_move_line(self, account, debit, credit, tax_filing_id=False):
        return {
            "name": account.name,
            "account_id": account.id,
            "partner_id": self.partner_id.id,
            "debit": debit,
            "credit": credit,
            "tax_filing_id": tax_filing_id,
        }

    def create_account_move_line(self):
        lines = []
        if self.account_from_id and self.amount_from > 0:
            lines.append(
                Command.create(
                    self.prepare_account_move_line(
                        self.account_from_id,
                        abs(self.amount_from),
                        0,
                        self.id,
                    ),
                )
            )
        if self.account_to_id and self.amount_to > 0:
            lines.append(
                Command.create(
                    self.prepare_account_move_line(
                        self.account_to_id,
                        0,
                        abs(self.amount_to),
                        self.id,
                    ),
                )
            )
        if self.account_adjust_id and self.amount_adjust > 0:
            lines.append(
                Command.create(
                    self.prepare_account_move_line(
                        self.account_adjust_id,
                        0,
                        abs(self.amount_adjust),
                        self.id,
                    ),
                )
            )
        if self.account_adjust_id and self.diff_amount != 0:
            lines.append(
                Command.create(
                    self.prepare_account_move_line(
                        self.account_adjust_id,
                        abs(self.diff_amount) if self.diff_amount > 0 else 0,
                        0 if self.diff_amount > 0 else abs(self.diff_amount),
                    ),
                )
            )
        return lines

    def create_journal_entry(self):
        journal_entry = {
            "move_type": "entry",
            "ref": self.name,
            "invoice_date": fields.Date.today(),
            "line_ids": self.create_account_move_line(),
        }
        return journal_entry

    def action_view_entries(self):
        return {
            "name": _("Journal Entries"),
            "view_mode": "form",
            "res_model": "account.move",
            "res_id": self.move_id.id,
            "type": "ir.actions.act_window",
        }

    def action_submit(self):
        for record in self:
            if not record.tax_filing_line_ids.filtered(lambda l: not l.display_type):
                raise UserError(_("You need to add a line before submit."))
        record.write({"state": "submit"})
        return True

    def action_create_invoice(self):
        for record in self:
            if record.state not in ["submit", "done"]:
                raise UserError(_("Can not create invoice in state %s", record.state))
            diff = record.total_amount
            move_type = "entry"
            if diff < 0:
                move_type = "in_invoice"
            elif diff > 0:
                if not record.account_adjust_id:
                    move_type = "out_invoice"

            if move_type != "entry":
                move = record.create_invoice(move_type)
            else:
                move = record.create_journal_entry()
            move = record.env["account.move"].create(move)
            record.write(
                {
                    "state": "done",
                    "move_id": move.id,
                }
            )
        return move

    def action_draft(self):
        return self.write({"state": "draft"})

    def action_cancel(self):
        return self.write({"state": "cancel"})
