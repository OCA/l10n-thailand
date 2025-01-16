# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
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
    has_adjustment = fields.Boolean(
        copy=False,
        readonly=True,
    )
    amount_from = fields.Monetary(
        default=0.0,
        currency_field="company_currency_id",
        copy=False,
        readonly=True,
    )
    amount_to = fields.Monetary(
        default=0.0,
        currency_field="company_currency_id",
        copy=False,
        readonly=True,
    )
    amount_adjust = fields.Monetary(
        string="Total Adjust",
        default=0.0,
        currency_field="company_currency_id",
        copy=False,
        readonly=True,
    )
    total_amount = fields.Monetary(
        string="Total Invoice",
        currency_field="company_currency_id",
        readonly=True,
        compute="_compute_total_amount",
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
            amount_from = abs(
                sum(
                    rec.tax_filing_line_ids.filtered(
                        lambda line: line.account_id == rec.account_from_id
                    ).mapped("balance")
                )
            )
            amount_to = abs(
                sum(
                    rec.tax_filing_line_ids.filtered(
                        lambda line: line.account_id == rec.account_to_id
                    ).mapped("balance")
                )
            )
            amount_adjust = abs(
                sum(
                    rec.tax_filing_line_ids.filtered(
                        lambda line: line.account_id == rec.account_adjust_id
                    ).mapped("balance")
                )
            )
            rec.write(
                {
                    "amount_from": amount_from,
                    "amount_to": amount_to,
                    "amount_adjust": amount_adjust,
                    "total_amount": (amount_from - amount_to) * -1,
                }
            )

    @api.constrains("date_from", "date_to")
    def check_date_from_to(self):
        # Check date form can't be after date to
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(_("Start Date must not be after End Date"))

    def action_compute_account_tax_filing_line(self):
        # Clear all lines before recompute (if any)
        self.tax_filing_line_ids.unlink()

        if self.account_adjust_id:
            condition = "WHERE aml.account_id IN ({}, {}, {})".format(
                self.account_from_id.id,
                self.account_to_id.id,
                self.account_adjust_id.id,
            )
        else:
            condition = "WHERE aml.account_id IN ({}, {})".format(
                self.account_from_id.id, self.account_to_id.id
            )
        query = """
            SELECT aml.id, aml.account_id, aml.name,
                aml.date, aml.debit, aml.credit, aml.balance
            FROM account_move_line aml
            LEFT JOIN account_tax_filing_line filing_line ON filing_line.move_line_id = aml.id
            LEFT JOIN account_move am ON am.id = aml.move_id
            {condition}
                AND aml.date BETWEEN %s AND %s
                AND aml.parent_state = 'posted'
                AND filing_line.id IS NULL
                AND am.tax_filing_id IS NULL
                AND aml.company_id = %s
            """.format(
            condition=condition
        )
        self.env.cr.execute(query, (self.date_from, self.date_to, self.company_id.id))
        result = self.env.cr.dictfetchall()
        adjust_lines = [
            {
                "display_type": "line_section",
                "name": "Journal Entries",
                "filing_id": self.id,
            }
        ]
        lines = [
            {
                "display_type": "line_section",
                "name": "Invoice Lines",
                "filing_id": self.id,
            }
        ]
        for res in result:
            line_data = {
                "account_id": res["account_id"],
                "name": res["name"],
                "date": res["date"].strftime("%Y-%m-%d"),
                "debit": res["debit"],
                "credit": res["credit"],
                "move_line_id": res["id"],
                "balance": res["balance"],
                "filing_id": self.id,
            }
            if res["account_id"] == self.account_adjust_id.id:
                adjust_lines.append(line_data)
            else:
                lines.append(line_data)

        if len(adjust_lines) == 1:
            adjust_lines.pop(0)
            lines.pop(0)

        self.has_adjustment = bool(adjust_lines)
        self.tax_filing_line_ids.create(adjust_lines + lines)

    def prepare_invoice_line(self, account, amount, sign):
        return {
            "name": account.name,
            "account_id": account.id,
            "price_unit": amount * sign,
        }

    def create_invoice_line(self, move_type):
        # toggle amount with sign
        sign = -1 if move_type == "out_invoice" else 1
        invoice_lines = []
        if self.amount_from > 0:
            invoice_lines.append(
                (
                    0,
                    0,
                    self.prepare_invoice_line(
                        self.account_from_id, self.amount_from, sign
                    ),
                )
            )
        if self.amount_to > 0:
            invoice_lines.append(
                (
                    0,
                    0,
                    self.prepare_invoice_line(
                        self.account_to_id, self.amount_to, sign * -1
                    ),
                )
            )
        return invoice_lines

    def create_invoice(self, move_type):
        # Create invoice
        invoice = {
            "move_type": move_type,
            "partner_id": self.partner_id.id,
            "invoice_date": fields.Date.today(),
            "tax_filing_id": self.id,
            "invoice_line_ids": self.create_invoice_line(move_type),
        }
        return invoice

    def prepare_account_move_line(self, account, debit, credit):
        return {
            "name": account.name,
            "account_id": account.id,
            "partner_id": self.partner_id.id,
            "debit": debit,
            "credit": credit,
        }

    def create_account_move_line(self):
        amount = self.amount_from - self.amount_to
        lines = []
        if self.amount_from > 0:
            lines.append(
                (
                    0,
                    0,
                    self.prepare_account_move_line(
                        self.account_from_id, self.amount_from, 0
                    ),
                )
            )
        if self.amount_to > 0:
            lines.append(
                (
                    0,
                    0,
                    self.prepare_account_move_line(
                        self.account_to_id, 0, self.amount_to
                    ),
                )
            )
        if self.account_adjust_id and amount != 0:
            lines.append(
                (
                    0,
                    0,
                    self.prepare_account_move_line(
                        self.account_adjust_id,
                        0 if amount > 0 else abs(amount),
                        abs(amount) if amount > 0 else 0,
                    ),
                )
            )
        return lines

    def create_journal_entry(self):
        journal_entry = {
            "move_type": "entry",
            "ref": self.name,
            "invoice_date": fields.Date.today(),
            "tax_filing_id": self.id,
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
            if not record.tax_filing_line_ids:
                raise UserError(_("You need to add a line before submit."))
        record.write({"state": "submit"})
        return True

    def action_create_invoice(self):
        for record in self:
            if record.state != "submit":
                raise UserError(
                    _("Only submitted tax filing can be used to create invoice")
                )
            diff = record.total_amount * -1
            move_type = "entry"

            if record.account_adjust_id:
                if diff > 0:
                    if diff - record.amount_adjust > 0:
                        move_type = "in_invoice"
            else:
                if diff > 0:
                    move_type = "in_invoice"
                elif diff < 0:
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
        # Clear all lines before recompute (if any)
        self.tax_filing_line_ids.unlink()
        return self.write({"state": "cancel"})
