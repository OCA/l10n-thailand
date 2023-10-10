# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import calendar
import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
        string="Partner",
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
    to_clear_tax = fields.Boolean(related="payment_id.to_clear_tax")
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
        """Compute without undue vat"""
        for rec in self._origin.filtered(lambda l: not l.payment_id):
            sign = 1 if rec.move_id.move_type not in ["in_refund", "out_refund"] else -1
            rec.tax_base_amount = sign * rec.move_line_id.tax_base_amount or 0.0
            rec.balance = sign * abs(rec.move_line_id.balance) or 0.0

    @api.depends("move_line_id")
    def _compute_payment_id(self):
        for rec in self:
            if not rec.payment_id:
                origin_move = rec.move_id.reversed_entry_id
                payment = origin_move.tax_invoice_ids.mapped("payment_id")
                rec.payment_id = (
                    payment and payment.id or self.env.context.get("payment_id", False)
                )

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

    def unlink(self):
        """Do not allow remove the last tax_invoice of move_line"""
        line_taxinv = {}
        for move_line in self.mapped("move_line_id"):
            line_taxinv.update({move_line.id: move_line.tax_invoice_ids.ids})
        for rec in self.filtered("move_line_id"):
            if len(line_taxinv[rec.move_line_id.id]) == 1 and not self.env.context.get(
                "force_remove_tax_invoice"
            ):
                raise UserError(_("Cannot delete this last tax invoice line"))
            line_taxinv[rec.move_line_id.id].remove(rec.id)
        return super().unlink()
