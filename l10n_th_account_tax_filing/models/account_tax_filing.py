# Copyright 2025 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountTaxFiling(models.Model):
    _name = "account.tax.filing"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Account Tranfer Tax Filing"
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
            ("cancel", "Cancel"),
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
    line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="tax_filing_id",
        string="Journal items",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    adjust_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="tax_filing_adjust_id",
        string="Adjust lines",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    has_adjustment = fields.Boolean(
        copy=False,
        readonly=True,
    )
    amount_from = fields.Monetary(
        currency_field="company_currency_id",
        copy=False,
        readonly=True,
    )
    amount_to = fields.Monetary(
        currency_field="company_currency_id",
        copy=False,
        readonly=True,
    )
    amount_adjust = fields.Monetary(
        currency_field="company_currency_id",
        copy=False,
        readonly=True,
    )
    total_amount = fields.Monetary(
        currency_field="company_currency_id",
        copy=False,
        readonly=True,
    )

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

    @api.constrains("date_from", "date_to")
    def check_date_from_to(self):
        # Check date form can't be after date to
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(_("Start Date must not be after End Date"))

    @api.model
    def create(self, vals):
        # Set name based on sequence
        if vals.get("name", "Draft") == "Draft":
            vals["name"] = (
                self.env["ir.sequence"].next_by_code("account.tax.filing") or "Draft"
            )
        return super(AccountTaxFiling, self).create(vals)

    def compute_account_amount(self):
        self.ensure_one()
        amount_adjust = 0
        amount_from = 0
        amount_to = 0

        query = """
            SELECT
            account_id, sum(balance) AS amount
            FROM account_move_line
            WHERE tax_filing_id = %s OR tax_filing_adjust_id = %s
            group by account_id
        """
        self.env.cr.execute(query, (self.id, self.id))
        results = self.env.cr.fetchall()

        for account_id, amount in results:
            if account_id == self.account_adjust_id.id:
                amount_adjust = abs(amount)
            elif account_id == self.account_from_id.id:
                amount_from = abs(amount)
            elif account_id == self.account_to_id.id:
                amount_to = abs(amount)

        results = {
            "amount_adjust": amount_adjust,
            "amount_from": amount_from,
            "amount_to": amount_to,
        }
        return results

    def recompute_account_move_line(self):
        self.ensure_one()
        # Reset the line_ids and adjust_line_ids and account
        self.write(
            {
                "account_from_id": self.env.company.account_from_id,
                "account_to_id": self.env.company.account_to_id,
                "account_adjust_id": self.env.company.account_adjust_id,
                "adjust_line_ids": False,
                "line_ids": False,
                "has_adjustment": False,
            }
        )
        lines = []
        adjust_lines = []

        if self.account_adjust_id:
            condition = "WHERE account_id IN ({}, {}, {})".format(
                self.account_from_id.id,
                self.account_to_id.id,
                self.account_adjust_id.id,
            )
        else:
            condition = "WHERE account_id IN ({}, {})".format(
                self.account_from_id.id, self.account_to_id.id
            )

        query = """
            SELECT
            account_id, ARRAY_AGG(id) AS lines
            FROM account_move_line
            {condition}
            AND date BETWEEN %s AND %s
            AND parent_state = 'posted'
            AND tax_filing_id IS NULL
            AND tax_filing_adjust_id IS NULL
            AND is_tax_filing = False
            AND company_id = %s
            group by account_id
        """.format(
            condition=condition
        )
        self.env.cr.execute(query, (self.date_from, self.date_to, self.company_id.id))
        results = self.env.cr.fetchall()

        for account_id, line in results:
            if account_id == self.account_adjust_id.id:
                adjust_lines.extend(line)
                self.has_adjustment = True
            else:
                lines.extend(line)

        self.write(
            {
                "adjust_line_ids": [(6, 0, adjust_lines)],
                "line_ids": [(6, 0, lines)],
            }
        )

    def prepare_invoice_line(self, account, amount, sign):
        return {
            "name": account.name,
            "account_id": account.id,
            "price_unit": amount * sign,
            "is_tax_filing": True,
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
            "is_tax_filing": True,
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
        if self.has_adjustment and amount != 0:
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
            if not record.line_ids:
                raise UserError(_("You need to add a line before confirm."))
            record.write(record.compute_account_amount())
            record.state = "submit"

    def action_create_invoice(self):
        for record in self:
            if record.state != "confirm":
                raise UserError(
                    _("Only confirmed tax filing can be used to create invoice")
                )

            # Check condition for create move_type
            diff = record.amount_from - record.amount_to
            if record.account_adjust_id:
                if diff > 0:
                    diff -= record.amount_adjust
                    if diff > 0:
                        move = record.create_invoice("in_invoice")
                    elif diff <= 0:
                        move = record.create_journal_entry()
                elif diff <= 0:
                    diff += record.amount_adjust
                    move = record.create_journal_entry()
            else:
                if diff > 0:
                    move = record.create_invoice("in_invoice")
                elif diff < 0:
                    move = record.create_invoice("out_invoice")
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
        return self.with_context(skip_tax_filing_check=True).write(
            {
                "state": "cancel",
                "line_ids": False,
                "adjust_line_ids": False,
            }
        )
