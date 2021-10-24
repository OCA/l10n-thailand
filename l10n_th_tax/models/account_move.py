# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import calendar
import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.misc import format_date


class AccountMoveTaxInvoice(models.Model):
    _name = "account.move.tax.invoice"
    _description = "Tax Invoice Info"

    tax_invoice_number = fields.Char(string="Tax Invoice Number", copy=False)
    tax_invoice_date = fields.Date(string="Tax Invoice Date", copy=False)
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
        string="Report Date",
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
        comodel_name="account.account", related="move_line_id.account_id"
    )
    tax_line_id = fields.Many2one(
        comodel_name="account.tax", related="move_line_id.tax_line_id"
    )
    tax_base_amount = fields.Monetary(
        string="Tax Base", currency_field="company_currency_id", copy=False
    )
    balance = fields.Monetary(
        string="Tax Amount", currency_field="company_currency_id", copy=False
    )
    reversing_id = fields.Many2one(
        comodel_name="account.move", help="The move that reverse this move"
    )
    reversed_id = fields.Many2one(
        comodel_name="account.move", help="This move that this move reverse"
    )

    @api.depends("move_line_id")
    def _compute_payment_id(self):
        for rec in self:
            if not rec.payment_id:
                origin_move = rec.move_id.reversed_entry_id
                payment = origin_move.tax_invoice_ids.mapped("payment_id")
                rec.payment_id = (
                    payment and payment.id or self._context.get("payment_id", False)
                )

    @api.depends("report_late_mo", "tax_invoice_date")
    def _compute_report_date(self):
        for rec in self:
            if rec.tax_invoice_date:
                eval_date = rec.tax_invoice_date + relativedelta(
                    months=int(rec.report_late_mo)
                )
                last_date = calendar.monthrange(eval_date.year, eval_date.month)[1]
                rec.report_date = datetime.date(
                    eval_date.year, eval_date.month, last_date
                )
            else:
                rec.report_date = False

    def unlink(self):
        """ Do not allow remove the last tax_invoice of move_line """
        line_taxinv = {}
        for move_line in self.mapped("move_line_id"):
            line_taxinv.update({move_line.id: move_line.tax_invoice_ids.ids})
        for rec in self.filtered("move_line_id"):
            if len(line_taxinv[rec.move_line_id.id]) == 1 and not self._context.get(
                "force_remove_tax_invoice"
            ):
                raise UserError(_("Cannot delete this last tax invoice line"))
            line_taxinv[rec.move_line_id.id].remove(rec.id)
        return super().unlink()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_invoice_ids = fields.One2many(
        comodel_name="account.move.tax.invoice", inverse_name="move_line_id"
    )
    manual_tax_invoice = fields.Boolean(
        copy=False, help="Create Tax Invoice for this debit/credit line"
    )
    wht_tax_id = fields.Many2one(
        comodel_name="account.withholding.tax",
        string="WT",
        compute="_compute_wht_tax_id",
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "account_id")
    def _compute_wht_tax_id(self):
        for rec in self:
            # From invoice, default from product
            if rec.move_id.move_type in ("out_invoice", "out_refund", "in_receipt"):
                rec.wht_tax_id = rec.product_id.wht_tax_id
            elif rec.move_id.move_type in ("in_invoice", "in_refund", "out_receipt"):
                rec.wht_tax_id = rec.product_id.supplier_wht_tax_id
            elif (
                rec.payment_id
                and rec.payment_id.wht_tax_id.account_id == rec.account_id
            ):
                rec.wht_tax_id = rec.payment_id.wht_tax_id
            else:
                rec.wht_tax_id = False

    def _get_wht_base_amount(self, currency, currency_date):
        self.ensure_one()
        wht_base_amount = 0
        if not currency or self.currency_id == currency:
            # Same currency
            wht_base_amount = self.amount_currency
        elif currency == self.company_currency_id:
            # Payment expressed on the company's currency.
            wht_base_amount = self.balance
        else:
            # Foreign currency on payment different than the one set on the journal entries.
            wht_base_amount = self.company_currency_id._convert(
                self.balance, currency, self.company_id, currency_date
            )
        return wht_base_amount

    def _get_wht_amount(self, currency, wht_date):
        """ Calculate withholding tax and base amount based on currency """
        wht_lines = self.filtered("wht_tax_id")
        pit_lines = wht_lines.filtered("wht_tax_id.is_pit")
        wht_lines = wht_lines - pit_lines
        # Mixing PIT and WHT or > 1 type, no auto deduct
        if pit_lines and wht_lines:
            return (0, 0)
        # WHT
        if wht_lines:
            wht_tax = wht_lines.mapped("wht_tax_id")
            if len(wht_tax) != 1:
                return (0, 0)
            amount_base = 0
            amount_wt = 0
            for line in wht_lines:
                base_amount = line._get_wht_base_amount(currency, wht_date)
                amount_wt += line.wht_tax_id.amount / 100 * base_amount
                amount_base += base_amount
            return (amount_base, amount_wt)
        # PIT
        if pit_lines:
            pit_tax = pit_lines.mapped("wht_tax_id")
            pit_tax.ensure_one()
            move_lines = self.filtered(lambda l: l.wht_tax_id == pit_tax)
            amount_invoice_currency = sum(move_lines.mapped("amount_currency"))
            move = move_lines[0]
            company = move.company_id
            partner = move.partner_id
            # Convert invoice currency to payment currency
            amount_base = move.currency_id._convert(
                amount_invoice_currency, currency, company, wht_date
            )
            effective_pit = pit_tax.with_context(pit_date=wht_date).pit_id
            if not effective_pit:
                raise UserError(
                    _("No effective PIT rate for date %s")
                    % format_date(self.env, wht_date)
                )
            amount_wt = effective_pit._compute_expected_wt(
                partner,
                amount_base,
                pit_date=wht_date,
                currency=currency,
                company=company,
            )
            return (amount_base, amount_wt)

    def _checkout_tax_invoice_amount(self):
        for line in self:
            if not line.manual_tax_invoice and line.tax_invoice_ids:
                tax = sum(line.tax_invoice_ids.mapped("balance"))
                if float_compare(abs(line.balance), abs(tax), 2) != 0:
                    raise UserError(_("Invalid Tax Amount"))

    @api.model_create_multi
    def create(self, vals_list):
        move_lines = super().create(vals_list)
        TaxInvoice = self.env["account.move.tax.invoice"]
        sign = self._context.get("reverse_tax_invoice") and -1 or 1
        for line in move_lines:
            if (line.tax_line_id and line.tax_exigible) or line.manual_tax_invoice:
                taxinv = TaxInvoice.create(
                    {
                        "move_id": line.move_id.id,
                        "move_line_id": line.id,
                        "partner_id": line.partner_id.id,
                        "tax_invoice_number": sign < 0 and "/" or False,
                        "tax_invoice_date": sign < 0 and fields.Date.today() or False,
                        "tax_base_amount": sign * abs(line.tax_base_amount),
                        "balance": sign * abs(line.balance),
                        "reversed_id": (
                            line.move_id.move_type == "entry"
                            and line.move_id.reversed_entry_id.id
                            or False
                        ),
                    }
                )
                line.tax_invoice_ids |= taxinv
            # Assign back the reversing id
            for taxinv in line.tax_invoice_ids.filtered("reversed_id"):
                TaxInvoice.search([("move_id", "=", taxinv.reversed_id.id)]).write(
                    {"reversing_id": taxinv.move_id.id}
                )
        return move_lines

    def write(self, vals):
        if "manual_tax_invoice" in vals:
            if vals["manual_tax_invoice"]:
                TaxInvoice = self.env["account.move.tax.invoice"]
                for line in self:
                    taxinv = TaxInvoice.create(
                        {
                            "move_id": line.move_id.id,
                            "move_line_id": line.id,
                            "partner_id": line.partner_id.id,
                            "tax_base_amount": abs(line.tax_base_amount),
                            "balance": abs(line.balance),
                        }
                    )
                    line.tax_invoice_ids |= taxinv
            else:
                self = self.with_context(force_remove_tax_invoice=True)
                self.mapped("tax_invoice_ids").unlink()
        return super().write(vals)


class AccountMove(models.Model):
    _inherit = "account.move"

    tax_invoice_ids = fields.One2many(
        comodel_name="account.move.tax.invoice",
        inverse_name="move_id",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )
    wht_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="move_id",
        string="Withholding Tax Cert.",
        readonly=True,
    )
    wht_cert_cancel = fields.Boolean(
        compute="_compute_wht_cert_cancel",
        store=True,
        help="This document has WT Cert(s) and all are cancelled or not WT Cert",
    )

    @api.depends("wht_cert_ids.state")
    def _compute_wht_cert_cancel(self):
        for record in self:
            wht_state = list(set(record.wht_cert_ids.mapped("state")))
            wht_cancel = False
            if not wht_state or (len(wht_state) == 1 and "cancel" in wht_state):
                wht_cancel = True
            record.wht_cert_cancel = wht_cancel

    def button_wht_certs(self):
        self.ensure_one()
        action = self.env.ref("l10n_th_tax.action_withholding_tax_cert_menu")
        result = action.sudo().read()[0]
        result["domain"] = [("id", "in", self.wht_cert_ids.ids)]
        return result

    def _post(self, soft=True):
        """Additional tax invoice info (tax_invoice_number, tax_invoice_date)
        Case sales tax, use Odoo's info, as document is issued out.
        Case purchase tax, use vendor's info to fill back."""
        # Purchase Taxes
        for move in self:
            for tax_invoice in move.tax_invoice_ids.filtered(
                lambda l: l.tax_line_id.type_tax_use == "purchase"
                or (
                    l.move_id.move_type == "entry"
                    and not l.payment_id
                    and l.move_id.journal_id.type != "sale"
                )
            ):
                if (
                    not tax_invoice.tax_invoice_number
                    or not tax_invoice.tax_invoice_date
                ):
                    if tax_invoice.payment_id:  # Defer posting for payment
                        tax_invoice.payment_id.write({"to_clear_tax": True})
                        return self.browse()  # return False
                    elif self.mapped("move_type") == ["entry", "entry"]:
                        # Case Invoice reconcile with Refund, not perfect yet!
                        return self.browse()  # return False
                    else:
                        raise UserError(_("Please fill in tax invoice and tax date"))

        # TOFIX: this operation does cause serious impact in some case.
        # I.e., When a normal invoice with amount 0.0 line, deletion is prohibited,
        #       because it can set back the invoice status of invoice.
        #       Until there is better way to resolve, please keep this commented.
        # Cleanup, delete lines with same account_id and sum(amount) == 0
        # cash_basis_account_ids = (
        #     self.env["account.tax"]
        #     .search([("cash_basis_transition_account_id", "!=", False)])
        #     .mapped("cash_basis_transition_account_id.id")
        # )
        # for move in self:
        #     accounts = move.line_ids.mapped("account_id")
        #     partners = move.line_ids.mapped("partner_id")
        #     for account in accounts:
        #         for partner in partners:
        #             lines = move.line_ids.filtered(
        #                 lambda l: l.account_id == account
        #                 and l.partner_id == partner
        #                 and not l.tax_invoice_ids
        #                 and l.account_id.id not in cash_basis_account_ids
        #             )
        #             if sum(lines.mapped("balance")) == 0:
        #                 lines.unlink()

        res = super()._post(soft)

        # Sales Taxes
        for move in self:
            for tax_invoice in move.tax_invoice_ids.filtered(
                lambda l: l.tax_line_id.type_tax_use == "sale"
                or l.move_id.journal_id.type == "sale"
            ):
                tinv_number, tinv_date = self._get_tax_invoice_number(
                    move, tax_invoice, tax_invoice.tax_line_id
                )
                tax_invoice.write(
                    {"tax_invoice_number": tinv_number, "tax_invoice_date": tinv_date}
                )

        # Check amount tax invoice with move line
        for move in self:
            move.line_ids._checkout_tax_invoice_amount()
        return res

    def _get_tax_invoice_number(self, move, tax_invoice, tax):
        """Tax Invoice Numbering for Customer Invioce / Receipt
        - If move_type in ("out_invoice", "out_refund")
          - If number is (False, "/"), consider it no valid number then,
            - If sequence -> use sequence
            - If not sequence -> use move number
        - Else,
          - If no number
            - If move_type = "entry" and has reversed entry, use origin number
        """
        origin_move = move.move_type == "entry" and move.reversed_entry_id or move
        sequence = tax_invoice.tax_line_id.taxinv_sequence_id
        number = tax_invoice.tax_invoice_number
        invoice_date = tax_invoice.tax_invoice_date or origin_move.date
        if move.move_type in ("out_invoice", "out_refund"):
            number = False if number in (False, "/") else number
        if not number:
            if sequence:
                if move != origin_move:  # Case reversed entry, use origin
                    tax_invoices = origin_move.tax_invoice_ids.filtered(
                        lambda l: l.tax_line_id == tax
                    )
                    number = (
                        tax_invoices and tax_invoices[0].tax_invoice_number or False
                    )
                    if not number:
                        raise ValidationError(
                            _("Cannot set tax invoice number, number already exists.")
                        )
                else:  # Normal case, use new sequence
                    number = sequence.next_by_id(sequence_date=move.date)
            else:  # Now sequence for this tax, use document number
                number = tax_invoice.payment_id.name or origin_move.name
        return (number, invoice_date)

    def _reverse_moves(self, default_values_list=None, cancel=False):
        self = self.with_context(reverse_tax_invoice=True)
        return super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    def _create_tax_cash_basis_moves(self):
        """This method is called from the move lines that
        create cash basis entry. We want to use the same payment_id when
        create account.move.tax.invoice"""
        move_lines = self.debit_move_id | self.credit_move_id
        payment = move_lines.mapped("payment_id")
        if len(payment) == 1:
            self = self.with_context(payment_id=payment.id)
        return super()._create_tax_cash_basis_moves()
