# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import calendar
import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountMoveTaxInvoice(models.Model):
    _name = "account.move.tax.invoice"
    _description = "Tax Invoice Info"

    tax_invoice_number = fields.Char(copy=False)
    tax_invoice_date = fields.Date(copy=False)
    report_late_mo = fields.Selection(
        [
            ("0", "0 month"),
            ("1", "1 month"),
            ("2", "2 months"),
            ("3", "3 months"),
            ("4", "4 months"),
            ("5", "5 months"),
            ("6", "6 months"),
        ],
        string="Report Late",
        default="0",
        required=True,
    )
    report_date = fields.Date(
        compute="_compute_report_date",
        store=True,
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line", index=True, copy=True, ondelete="cascade"
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        ondelete="restrict",
    )
    move_id = fields.Many2one(comodel_name="account.move", index=True, copy=True)
    move_state = fields.Selection(related="move_id.state", store=True)
    payment_id = fields.Many2one(
        comodel_name="account.payment",
        compute="_compute_payment_id",
        store=True,
        copy=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company", related="move_id.company_id", store=True
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency", related="company_id.currency_id"
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        related="move_line_id.account_id",
        store=True,
    )
    tax_line_id = fields.Many2one(
        comodel_name="account.tax",
        related="move_line_id.tax_line_id",
        store=True,
    )
    tax_base_amount = fields.Monetary(
        string="Tax Base",
        currency_field="company_currency_id",
        compute="_compute_tax_amount",
        store=True,
        copy=False,
        readonly=False,
    )
    balance = fields.Monetary(
        string="Tax Amount",
        currency_field="company_currency_id",
        compute="_compute_tax_amount",
        store=True,
        copy=False,
        readonly=False,
    )
    reversing_id = fields.Many2one(
        comodel_name="account.move", help="The move that reverse this move"
    )
    reversed_id = fields.Many2one(
        comodel_name="account.move", help="This move that this move reverse"
    )

    @api.depends("move_line_id.balance", "move_line_id.tax_base_amount")
    def _compute_tax_amount(self):
        """Amounts are positive on the usual side of the tax (debit for purchases,
        credit for sales) and negative otherwise, i.e. refunds and reversals.
        Manual tax invoices have no tax, the side comes from the journal."""
        for rec in self._origin:
            line = rec.move_line_id
            base = rec._get_undue_vat_base() if line.tax_line_id else None
            if base is None:
                base = line.tax_base_amount
            # 0% tax lines have no balance, the base lines have the same
            # direction (tax base amount is not reversed on reversed entries)
            direction = (
                line.balance or sum(rec._get_base_lines().mapped("balance")) or base
            )
            if not rec._is_purchase_tax_invoice():
                direction = -direction
            sign = -1 if direction < 0 else 1
            rec.tax_base_amount = sign * abs(base)
            rec.balance = sign * abs(line.balance)

    def _get_undue_vat_base(self):
        """On undue VAT entries, tax base amount of the tax line is the base of
        the whole invoice, the paid base is on the base lines of the entry"""
        if not self.move_id.tax_cash_basis_origin_move_id:
            return None
        return sum(self._get_base_lines().mapped("balance"))

    def _get_base_lines(self):
        """Journal items of the entry having the tax of the tax line"""
        line = self.move_line_id
        if not line.tax_line_id:
            return line.browse()
        return line.move_id.line_ids.filtered(
            lambda base_line: (
                not base_line.tax_line_id and line.tax_line_id in base_line.tax_ids
            )
        )

    @api.depends("move_line_id", "move_id.tax_cash_basis_rec_id")
    def _compute_payment_id(self):
        for rec in self:
            if rec.payment_id:
                continue
            move = rec.move_id
            partial = move.tax_cash_basis_rec_id
            if partial:
                # Undue VAT entry, payment of the document reconciled with the origin
                counterpart = (
                    partial.debit_move_id.move_id | partial.credit_move_id.move_id
                ) - move.tax_cash_basis_origin_move_id
                payment = counterpart.origin_payment_id
                rec.payment_id = len(payment) == 1 and payment
            else:
                origin_move = move.reversed_entry_id
                rec.payment_id = origin_move.tax_invoice_ids.payment_id[:1]

    @api.depends("report_late_mo", "tax_invoice_date")
    def _compute_report_date(self):
        for rec in self:
            if rec.tax_invoice_date:
                eval_date = rec.tax_invoice_date + relativedelta(
                    months=int(rec.report_late_mo)
                )
                # Check report date is not late, it will use tax invoice date
                if eval_date.month == rec.tax_invoice_date.month:
                    rec.report_date = rec.tax_invoice_date
                    continue
                last_date = calendar.monthrange(eval_date.year, eval_date.month)[1]
                rec.report_date = datetime.date(
                    eval_date.year, eval_date.month, last_date
                )
            else:
                rec.report_date = False

    @api.onchange("tax_invoice_date")
    def _onchange_tax_invoice_date(self):
        """Auto add late report if month of accounting date
        difference month of tax invoice"""
        if self.tax_invoice_date and self.move_id.date:
            # Replace to first date of the month and find diffference month
            accounting_date = self.move_id.date.replace(day=1)
            tax_invoice_date = self.tax_invoice_date.replace(day=1)
            difference = relativedelta(accounting_date, tax_invoice_date)
            # Check accounting date and tax invoice date is difference
            if (
                difference.years > 0
                or (difference.years == 0 and difference.months >= 6)
                or difference.months < 0
            ):
                report_late = "0"
            else:
                report_late = str(difference.months)
            self.report_late_mo = report_late

    def _is_purchase_tax_invoice(self):
        """Tax invoice issued by the vendor, also on manual journal entries
        which are not on sales"""
        self.ensure_one()
        move = self.move_id
        if move.is_invoice(include_receipts=True):
            return move.is_purchase_document(include_receipts=True)
        return self.tax_line_id.type_tax_use == "purchase" or (
            move.move_type == "entry"
            and not self.payment_id
            and move.journal_id.type != "sale"
            and self.tax_line_id.type_tax_use != "sale"
        )

    def _is_missing_vendor_info(self):
        """Purchase tax invoice without the vendor's number or date"""
        self.ensure_one()
        return self._is_purchase_tax_invoice() and not (
            self.tax_invoice_number and self.tax_invoice_date
        )

    def _raise_missing_vendor_info(self):
        raise UserError(self.env._("Please fill in tax invoice and tax date"))

    @api.constrains("move_id", "move_line_id")
    def _check_move_line(self):
        for rec in self.filtered("move_line_id"):
            if rec.move_line_id.move_id != rec.move_id:
                raise ValidationError(
                    self.env._(
                        "The journal item of a tax invoice must belong to its "
                        "journal entry."
                    )
                )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_last_tax_invoice(self):
        """Do not allow remove the last tax_invoice of move_line"""
        line_taxinv = {}
        for move_line in self.mapped("move_line_id"):
            line_taxinv.update({move_line.id: move_line.tax_invoice_ids.ids})
        for rec in self.filtered("move_line_id"):
            if len(line_taxinv[rec.move_line_id.id]) == 1 and not self.env.context.get(
                "force_remove_tax_invoice"
            ):
                raise UserError(self.env._("Cannot delete this last tax invoice line"))
            line_taxinv[rec.move_line_id.id].remove(rec.id)
