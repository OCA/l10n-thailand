# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round
from odoo.tools.misc import format_date


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
        string="WHT",
        compute="_compute_wht_tax_id",
        check_company=True,
        store=True,
        readonly=False,
    )

    @api.depends("product_id", "partner_id")
    def _compute_wht_tax_id(self):
        for rec in self:
            # From invoice, default from product
            if rec.move_id.move_type in ("out_invoice", "out_refund", "in_receipt"):
                rec.wht_tax_id = rec.product_id.wht_tax_id
            elif rec.move_id.move_type in ("in_invoice", "in_refund", "out_receipt"):
                partner_id = rec.partner_id or rec.move_id.partner_id
                if partner_id and partner_id.company_type == "company":
                    rec.wht_tax_id = rec.product_id.supplier_company_wht_tax_id
                    continue
                rec.wht_tax_id = rec.product_id.supplier_wht_tax_id
            else:
                rec.wht_tax_id = False

    def _get_wht_amount(self, currency, wht_date):
        """Calculate withholding tax and base amount based on currency.

        Args:
            currency: The currency for calculation
            wht_date: The date for currency conversion

        Returns:
            tuple: (amount_base, amount_wht)
        """
        # Get all WHT lines in one filtered call
        wht_lines = self.filtered("wht_tax_id")

        # Split PIT and WHT lines efficiently
        pit_lines = wht_lines.filtered("wht_tax_id.is_pit")
        non_pit_lines = wht_lines - pit_lines

        # Handle WHT case
        if non_pit_lines:
            # Get unique WHT tax in one operation
            wht_taxes = non_pit_lines.mapped("wht_tax_id")
            wht_taxes.ensure_one()
            # Calculate totals in one pass
            amount_base = sum(line.amount_currency for line in non_pit_lines)
            amount_wht = amount_base * (wht_taxes.amount / 100)
            return (amount_base, amount_wht)

        # Handle PIT case
        if pit_lines:
            pit_tax = pit_lines.mapped("wht_tax_id")
            pit_tax.ensure_one()
            move_lines = self.filtered(lambda line: line.wht_tax_id == pit_tax)

            # Calculate base amount efficiently
            amount_invoice_currency = sum(move_lines.mapped("amount_currency"))
            move = move_lines[0]
            company = move.company_id
            partner = move.partner_id

            # Convert invoice currency to payment currency
            amount_base = move.currency_id._convert(
                amount_invoice_currency, currency, company, wht_date
            )

            # Get effective PIT rate
            effective_pit = pit_tax.with_context(pit_date=wht_date).pit_id
            if not effective_pit:
                raise UserError(
                    self.env._("No effective PIT rate for date %s")
                    % format_date(self.env, wht_date)
                )

            # Calculate WHT amount
            amount_wht = effective_pit._compute_expected_wht(
                partner,
                amount_base,
                wht_date,
                currency,
                company,
            )
            return (amount_base, amount_wht)
        return (0.0, 0.0)

    def _get_tax_base_amount(self, sign, vals_list):
        self.ensure_one()
        base = abs(self.tax_base_amount)
        tax = abs(self.balance)
        prec = self.env.company.currency_id.decimal_places
        full_tax = abs(float_round(self.tax_line_id.amount / 100 * base, prec))
        # partial payment, we need to compute the base amount
        partial_payment = self.env.context.get("partial_payment", False)
        if (
            partial_payment
            and self.tax_line_id
            and float_compare(full_tax, tax, prec) != 0
        ):
            base = abs(float_round(tax * 100 / self.tax_line_id.amount, prec))
        return sign * base

    def _prepare_move_tax_invoice(self, sign, vals_list):
        self.ensure_one()
        tax_base_amount = self._get_tax_base_amount(sign, vals_list)
        # For case customer invoice, customer credit note and not manual reconcile
        # it default value following accounting date
        default_tax_invoice = self.move_id.move_type in [
            "out_invoice",
            "out_refund",
        ] and not self.env.context.get("invoice_net_refund")
        taxinv_dict = {
            "move_id": self.move_id.id,
            "move_line_id": self.id,
            "partner_id": self.partner_id.id,
            "tax_invoice_number": default_tax_invoice and "/" or False,
            "tax_invoice_date": default_tax_invoice and self.move_id.date or False,
            "tax_base_amount": tax_base_amount,
            "balance": sign * abs(self.balance),
            "reversed_id": (
                self.move_id.move_type == "entry"
                and self.move_id.reversed_entry_id.id
                or False
            ),
        }
        return taxinv_dict

    @api.model_create_multi
    def create(self, vals_list):
        move_lines = super().create(vals_list)
        TaxInvoice = self.env["account.move.tax.invoice"]
        sign = self.env.context.get("reverse_tax_invoice") and -1 or 1
        for line in move_lines:
            is_tax_invoice = bool(
                line.tax_line_id
                and (
                    line.tax_line_id.tax_exigibility == "on_invoice"
                    or line.move_id.tax_cash_basis_origin_move_id
                )
            )
            if is_tax_invoice or line.manual_tax_invoice:
                taxinv_dict = line._prepare_move_tax_invoice(sign, vals_list)
                taxinv = TaxInvoice.create(taxinv_dict)
                line.tax_invoice_ids |= taxinv
            # Assign back the reversing id
            for taxinv in line.tax_invoice_ids.filtered("reversed_id"):
                TaxInvoice.search([("move_id", "=", taxinv.reversed_id.id)]).write(
                    {"reversing_id": taxinv.move_id.id}
                )
        return move_lines

    def write(self, vals):
        TaxInvoice = self.env["account.move.tax.invoice"]
        # Add manual tax in journal entries
        if "manual_tax_invoice" in vals:
            if vals["manual_tax_invoice"]:
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
            # Unlink all tax invoice, when manual_tax_invoice change from True to False
            elif self.manual_tax_invoice and vals["manual_tax_invoice"] is False:
                self = self.with_context(force_remove_tax_invoice=True)
                self.mapped("tax_invoice_ids").unlink()
        return super().write(vals)

    def _add_deduction(
        self, wht_lines, wht_tax, partner_id, amount_deduct, currency, date
    ):
        amount_base, amount_wht = wht_lines._get_wht_amount(currency, date)
        # Rounding withholding tax for each type
        amount_wht = float_round(amount_wht, precision_rounding=currency.rounding)
        amount_deduct += amount_wht
        deduct = {
            "partner_id": partner_id,
            "wht_amount_base": amount_base,
            "wht_tax_id": wht_tax.id,
            "account_id": wht_tax.account_id.id,
            "name": wht_tax.display_name,
            "amount": amount_wht,
        }
        return deduct, amount_deduct

    def _get_partner_wht_lines(self, wht_tax_lines, partner_id):
        """
        Get move lines withholding tax by partner,
        Split this function to be able to other module inherit this function
        (l10n_th_account_tax_expense)
        """
        partner_wht_lines = wht_tax_lines.filtered(
            lambda line: line.partner_id.id == partner_id
        )
        return partner_wht_lines

    def _get_partner_wht(self, wht_tax_lines):
        """
        Get partner from move lines withholding tax,
        Split this function to be able to other module inherit this function
        (l10n_th_account_tax_expense)
        """
        return wht_tax_lines.mapped("partner_id").ids

    def _prepare_deduction_list(self, date, currency):
        deductions = []
        amount_deduct = 0
        wht_taxes = self.mapped("wht_tax_id")
        for wht_tax in wht_taxes:
            wht_tax_lines = self.filtered(
                lambda line, wht_tax=wht_tax: line.wht_tax_id == wht_tax
            )
            partner_ids = self._get_partner_wht(wht_tax_lines)
            for partner_id in partner_ids:
                partner_wht_lines = self._get_partner_wht_lines(
                    wht_tax_lines, partner_id
                )
                deduct, amount_deduct = self._add_deduction(
                    partner_wht_lines,
                    wht_tax,
                    partner_id,
                    amount_deduct,
                    currency,
                    date,
                )
                deductions.append(deduct)
        return (deductions, amount_deduct)


class AccountMove(models.Model):
    _inherit = "account.move"

    tax_invoice_ids = fields.One2many(
        comodel_name="account.move.tax.invoice",
        inverse_name="move_id",
        copy=False,
    )
    wht_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="move_id",
        string="Withholding Tax Cert.",
        readonly=True,
    )
    wht_move_ids = fields.One2many(
        comodel_name="account.withholding.move",
        inverse_name="move_id",
        string="Withholding",
        copy=False,
        help="All withholding moves, including non-PIT",
    )
    wht_cert_status = fields.Selection(
        selection=[
            ("none", "Not yet created"),
            ("draft", "Draft"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        compute="_compute_wht_cert_status",
    )
    has_wht = fields.Boolean(
        compute="_compute_has_wht",
    )

    def _compute_has_wht(self):
        """Has WHT when
        1. Has wht_move_ids
        2. Is not invoice (move_type == 'entry' and not sale type)
        """
        for rec in self:
            wht_tax = bool(rec.wht_move_ids)
            not_inv = (
                rec.move_type == "entry"
                and not rec.origin_payment_id.payment_type == "inbound"
            )
            rec.has_wht = wht_tax and not_inv

    @api.depends("wht_cert_ids.state")
    def _compute_wht_cert_status(self):
        for rec in self:
            rec.wht_cert_status = False
            if not rec.has_wht:
                continue
            if not rec.wht_cert_ids:
                rec.wht_cert_status = "none"
            elif "draft" in rec.wht_cert_ids.mapped("state"):
                rec.wht_cert_status = "draft"
            elif rec.wht_cert_ids.mapped("state") == ["done"]:
                rec.wht_cert_status = "done"
            elif rec.wht_cert_ids.mapped("state") == ["cancel"]:
                rec.wht_cert_status = "cancel"

    def button_wht_certs(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_th_account_tax.action_withholding_tax_cert_menu"
        )
        action["domain"] = [("id", "in", self.wht_cert_ids.ids)]
        return action

    def js_assign_outstanding_line(self, line_id):
        move_line = self.env["account.move.line"].browse(line_id)
        if move_line.payment_id:
            self = self.with_context(net_invoice_payment=True)
        self = self.with_context(net_invoice_refund=True)
        return super().js_assign_outstanding_line(line_id)

    def js_remove_outstanding_partial(self, partial_id):
        # If you unreconcile with Journal Entry, it will create reverse tax cash basis
        # Which raise error require tax number and tax invoice so we send context to
        # skip this error.
        self = self.with_context(net_invoice_refund=True)
        return super().js_remove_outstanding_partial(partial_id)

    def _get_movelines_from_model(self, model, active_ids):
        move_lines = self.env["account.move.line"]
        if model == "account.move":
            move_lines = self.env[model].browse(active_ids).mapped("line_ids")
        elif model == "account.move.line":
            move_lines = self.env[model].browse(active_ids)
        return move_lines

    def _post(self, soft=True):
        """Additional tax invoice info (tax_invoice_number, tax_invoice_date)
        Case sales tax, use Odoo's info, as document is issued out.
        Case purchase tax, use vendor's info to fill back."""

        def handle_purchase_taxes(move):
            for tax_invoice in move.tax_invoice_ids.filtered(
                lambda tax: tax.tax_line_id.type_tax_use == "purchase"
                or (
                    tax.move_id.move_type == "entry"
                    and not tax.payment_id
                    and tax.move_id.journal_id.type != "sale"
                    and tax.tax_line_id.type_tax_use != "sale"
                )
            ):
                if (
                    not tax_invoice.tax_invoice_number
                    or not tax_invoice.tax_invoice_date
                ):
                    if tax_invoice.payment_id:  # Defer posting for payment
                        tax_invoice.payment_id.write({"to_clear_tax": True})
                        # Auto post tax cash basis when reset to draft
                        if tax_invoice.move_id.reversed_entry_id:
                            moves = (
                                tax_invoice.move_id
                                + tax_invoice.move_id.reversed_entry_id
                            )
                            tax_invoice.move_id.reversed_entry_id.write(
                                {"state": "posted"}
                            )
                            tax_account_id = tax_invoice.account_id
                            line_reconcile = moves.mapped("line_ids").filtered(
                                lambda line,
                                tax_account_id=tax_account_id: line.account_id
                                != tax_account_id
                                and line.reconciled
                            )
                            line_reconcile.reconcile()
                        continue
                    # Skip Error when found refund
                    elif self.env.context.get("net_invoice_refund"):
                        continue
                    else:
                        raise UserError(
                            self.env._("Please fill in tax invoice and tax date")
                        )

        def handle_sales_taxes(move):
            for tax_invoice in move.tax_invoice_ids.filtered(
                lambda tax: tax.tax_line_id.type_tax_use == "sale"
                or tax.move_id.journal_id.type == "sale"
            ):
                tinv_number, tinv_date = self._get_tax_invoice_number(
                    move, tax_invoice, tax_invoice.tax_line_id
                )
                tax_invoice.write(
                    {
                        "tax_invoice_number": tinv_number,
                        "tax_invoice_date": tinv_date,
                    }
                )

        def handle_withholding_taxes(move):
            # Normal case, create withholding.move only when withholding
            wht_movelines = move.line_ids.filtered(
                lambda line: line.account_id.wht_account and line.wht_tax_id
            )
            withholding_moves = [
                Command.create(self._prepare_withholding_move(wht_ml))
                for wht_ml in wht_movelines
            ]
            move.write({"wht_move_ids": [Command.clear()] + withholding_moves})

            # On payment JE, keep track of move when PIT not withheld,
            # use data from vendor bill
            payment_id = move.origin_payment_id
            if payment_id and not payment_id.wht_move_ids.mapped("is_pit"):
                active_ids = self.env.context.get("active_ids", [])
                model = self.env.context.get("active_model")
                move_lines = self._get_movelines_from_model(model, active_ids)
                line_pit = move_lines.filtered("wht_tax_id.is_pit")
                if not line_pit:
                    return

                line_wht_moves = [
                    Command.create(
                        self._prepare_withholding_move(line, pit_no_wht=True)
                    )
                    for line in line_pit
                ]
                move.write({"wht_move_ids": line_wht_moves})

        # Purchase Taxes
        for move in self:
            handle_purchase_taxes(move)

        res = super()._post(soft=soft)

        # Sales Taxes
        for move in self:
            handle_sales_taxes(move)

        # Withholding Tax:
        # - Create account.withholding.move, for every withholding tax line
        # - For case PIT, it is possible that there is no withholidng amount
        #   but still need to keep track the withholding.move base amount
        for move in self:
            handle_withholding_taxes(move)

        # When post, do remove the existing certs
        self.mapped("wht_cert_ids").unlink()
        return res

    def _prepare_withholding_move(self, wht_ml, pit_no_wht=False):
        """Prepare dict for account.withholding.move"""
        if pit_no_wht:
            amount_income = abs(wht_ml.balance)
            amount_wht = 0.0
        else:
            amount_income = wht_ml.tax_base_amount
            amount_wht = abs(wht_ml.balance)

        return {
            "partner_id": wht_ml.partner_id.id,
            "amount_income": amount_income,
            "amount_wht": amount_wht,
            "wht_tax_id": wht_ml.wht_tax_id.id,
            "wht_cert_income_type": wht_ml.wht_tax_id.wht_cert_income_type,
            "company_id": wht_ml.company_id.id,
        }

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
            number = number if number and number != "/" else False
        if not number:
            if sequence:
                if move != origin_move:  # Case reversed entry, use origin
                    tax_invoices = origin_move.tax_invoice_ids.filtered(
                        lambda tax_inv: tax_inv.tax_line_id == tax
                    )
                    number = (
                        tax_invoices and tax_invoices[0].tax_invoice_number or False
                    )
                else:  # Normal case, use new sequence
                    number = sequence.next_by_id(sequence_date=move.date)
            else:  # Now sequence for this tax, use config (payment/invoice number)
                number = (
                    tax_invoice.payment_id.name
                    if self.env.company.customer_tax_invoice_number == "payment"
                    else tax_invoice.move_id.ref
                ) or origin_move.name
        return (number, invoice_date)

    def copy(self, default=None):
        """
        For case reverse move,
        Tax number and date must have value from wizard reversal.
        """
        self.ensure_one()
        new = super().copy(default)
        tax_number = self.env.context.get("tax_invoice_number")
        tax_date = self.env.context.get("tax_invoice_date")
        if tax_number or tax_date:
            new.tax_invoice_ids.write(
                {
                    "tax_invoice_number": tax_number,
                    "tax_invoice_date": tax_date,
                }
            )
        return new

    def _reverse_moves(self, default_values_list=None, cancel=False):
        self = self.with_context(reverse_tax_invoice=True)
        # NOTE: Reverse cash basis document,
        # from move with cash basis and reset to draft Credit Note of move
        if self.mapped("tax_cash_basis_origin_move_id") and len(self) == len(
            self.mapped("tax_cash_basis_origin_move_id")
        ):
            self = self.with_context(net_invoice_refund=1)

        return super()._reverse_moves(
            default_values_list=default_values_list, cancel=cancel
        )

    def button_cancel(self):
        res = super().button_cancel()
        for rec in self:
            # Create the mirror only for those posted
            for line in rec.wht_move_ids:
                line.copy(
                    {
                        "amount_income": -line.amount_income,
                        "amount_wht": -line.amount_wht,
                        "calendar_year": line.calendar_year,
                    }
                )
                line.cancelled = True
            # Cancel all certs
            rec.wht_cert_ids.action_cancel()
        return res

    def button_draft(self):
        res = super().button_draft()
        self.mapped("wht_cert_ids").action_cancel()
        return res

    def create_wht_cert(self):
        """
        Create/replace one withholding tax cert from withholding move
        Group by partner and income type, regardless of wht_tax_id
        """
        self.ensure_one()
        if self.wht_move_ids.filtered(lambda wht: not wht.wht_cert_income_type):
            raise UserError(
                self.env._("Please select Type of Income on every withholding moves")
            )
        certs = self._preapare_wht_certs()
        self.env["withholding.tax.cert"].create(certs)

    def _preapare_wht_certs(self):
        """Create withholding tax certs, 1 cert per partner"""
        self.ensure_one()
        AccountWithholdingTax = self.env["account.withholding.tax"]
        wht_move_groups = self.env["account.withholding.move"].read_group(
            domain=[("move_id", "=", self.id)],
            fields=[
                "partner_id",
                "wht_cert_income_type",
                "wht_cert_income_desc",
                "wht_tax_id",
                "amount_income",
                "amount_wht",
            ],
            groupby=[
                "partner_id",
                "wht_cert_income_type",
                "wht_tax_id",
                "wht_cert_income_desc",
            ],
            lazy=False,
        )
        # Create 1 cert for 1 vendor
        partners = self.wht_move_ids.mapped("partner_id")
        cert_list = []
        for partner in partners:
            cert_line_vals = []
            wht_tax_set = set()
            wht_moves = list(
                filter(lambda wht: wht["partner_id"][0] == partner.id, wht_move_groups)
            )
            for wht_move in wht_moves:
                cert_line_vals.append(
                    Command.create(
                        {
                            "wht_cert_income_type": wht_move["wht_cert_income_type"],
                            "wht_cert_income_desc": wht_move["wht_cert_income_desc"],
                            "base": wht_move["amount_income"],
                            "amount": wht_move["amount_wht"],
                            "wht_tax_id": wht_move["wht_tax_id"][0],
                        }
                    )
                )
                wht_tax_set.add(wht_move["wht_tax_id"][0])
            cert_vals = {
                "move_id": self.id,
                "payment_id": self.origin_payment_id.id,
                "partner_id": partner.id,
                "date": self.date,
                "wht_line": cert_line_vals,
            }
            # Default income_tax_form
            wht_tax = AccountWithholdingTax.browse(wht_tax_set)
            income_tax_form = wht_tax.mapped("income_tax_form")
            if len(income_tax_form) == 1:
                cert_vals.update({"income_tax_form": income_tax_form[0]})
            cert_list.append(cert_vals)
        return cert_list

    @api.depends(
        "posted_before", "state", "journal_id", "date", "move_type", "origin_payment_id"
    )
    def _compute_name(self):
        """Skip sequence for cash basis entries from vendor bills."""

        payment_context = self.env.context.get("payment_id")
        if payment_context:
            cash_basis_moves = self.filtered(
                lambda m: m.tax_cash_basis_origin_move_id
                and m.tax_cash_basis_origin_move_id.move_type == "in_invoice"
            )
            for move in cash_basis_moves:
                move.name = False

            self = self - cash_basis_moves

        return super()._compute_name()
