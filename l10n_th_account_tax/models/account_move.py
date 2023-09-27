# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
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
        """Calculate withholding tax and base amount based on currency"""
        wht_lines = self.filtered("wht_tax_id")
        pit_lines = wht_lines.filtered("wht_tax_id.is_pit")
        wht_lines = wht_lines - pit_lines
        # Mixing PIT and WHT or > 1 type, no auto deduct
        if pit_lines and wht_lines or not self:
            return (0, 0)
        # WHT
        if wht_lines:
            wht_tax = wht_lines.mapped("wht_tax_id")
            if len(wht_tax) != 1:
                return (0, 0)
            amount_base = 0
            amount_wht = 0
            for line in wht_lines:
                base_amount = line._get_wht_base_amount(currency, wht_date)
                amount_wht += line.wht_tax_id.amount / 100 * base_amount
                amount_base += base_amount
            return (amount_base, amount_wht)
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
            amount_wht = effective_pit._compute_expected_wht(
                partner,
                amount_base,
                pit_date=wht_date,
                currency=currency,
                company=company,
            )
            return (amount_base, amount_wht)

    # def _checkout_tax_invoice_amount(self):
    #     for line in self:
    #         if not line.manual_tax_invoice and line.tax_invoice_ids:
    #             tax = sum(line.tax_invoice_ids.mapped("balance"))
    #             if float_compare(abs(line.balance), abs(tax), 2) != 0:
    #                 raise UserError(_("Invalid Tax Amount"))

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

    @api.model_create_multi
    def create(self, vals_list):
        move_lines = super().create(vals_list)
        TaxInvoice = self.env["account.move.tax.invoice"]
        sign = self.env.context.get("reverse_tax_invoice") and -1 or 1
        for line in move_lines:
            is_tax_invoice = (
                True
                if line.tax_line_id
                and (
                    line.tax_line_id.tax_exigibility == "on_invoice"
                    or line.move_id.tax_cash_basis_origin_move_id
                )
                else False
            )
            if is_tax_invoice or line.manual_tax_invoice:
                tax_base_amount = line._get_tax_base_amount(sign, vals_list)
                # For case customer invoice, customer credit note and not manual reconcile
                # it default value in tax invoice
                default_tax_invoice = line.move_id.move_type in [
                    "out_invoice",
                    "out_refund",
                ] and not self.env.context.get("invoice_net_refund")
                taxinv = TaxInvoice.create(
                    {
                        "move_id": line.move_id.id,
                        "move_line_id": line.id,
                        "partner_id": line.partner_id.id,
                        "tax_invoice_number": default_tax_invoice and "/" or False,
                        "tax_invoice_date": default_tax_invoice
                        and fields.Date.today()
                        or False,
                        "tax_base_amount": tax_base_amount,
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

    def _add_deduction(
        self, wht_lines, wht_tax, partner_id, amount_deduct, currency, date
    ):
        amount_base, amount_wht = wht_lines._get_wht_amount(currency, date)
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

    def _prepare_deduction_list(self, currency=False, date=False):
        if not currency:
            currency = self.env.company.currency_id
        if not date:
            date = fields.Date.context_today(self)

        deductions = []
        amount_deduct = 0
        wht_taxes = self.mapped("wht_tax_id")
        for wht_tax in wht_taxes:
            wht_tax_lines = self.filtered(lambda l: l.wht_tax_id == wht_tax)
            # Get partner, first from extended module (l10n_th_account_tax_expense)
            if hasattr(wht_tax_lines, "expense_id") and wht_tax_lines.filtered(
                "expense_id"
            ):  # From expense, group by bill_partner_id of expense, or default partner
                partner_ids = list(
                    {
                        x.bill_partner_id.id
                        or x.employee_id.sudo().address_home_id.commercial_partner_id.id
                        or x.employee_id.sudo().user_partner_id.id
                        for x in wht_tax_lines.mapped("expense_id")
                    }
                )
                for partner_id in partner_ids:
                    partner_wht_lines = wht_tax_lines.filtered(
                        lambda l: l.expense_id.bill_partner_id.id == partner_id
                        or (
                            not l.expense_id.bill_partner_id
                            and l.partner_id.id == partner_id
                        )
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
            else:
                partner_ids = wht_tax_lines.mapped("partner_id").ids
                for partner_id in partner_ids:
                    partner_wht_lines = wht_tax_lines.filtered(
                        lambda l: l.partner_id.id == partner_id
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
        1. Has wht_tax_id
        2. Is not invoice (move_type == 'entry')
        """
        for rec in self:
            wht_tax = True if rec.line_ids.mapped("wht_tax_id") else False
            not_inv = rec.move_type == "entry"
            rec.has_wht = wht_tax and not_inv

    @api.depends("wht_cert_ids.state")
    def _compute_wht_cert_status(self):
        for rec in self:
            if not rec.has_wht:
                rec.wht_cert_status = False
                continue
            if not rec.wht_cert_ids:
                rec.wht_cert_status = "none"
            elif "draft" in rec.wht_cert_ids.mapped("state"):
                rec.wht_cert_status = "draft"
            elif rec.wht_cert_ids.mapped("state") == ["done"]:
                rec.wht_cert_status = "done"
            elif rec.wht_cert_ids.mapped("state") == ["cancel"]:
                rec.wht_cert_status = "cancel"
            else:
                rec.wht_cert_status = False

    def button_wht_certs(self):
        self.ensure_one()
        action = self.env.ref("l10n_th_account_tax.action_withholding_tax_cert_menu")
        result = action.sudo().read()[0]
        result["domain"] = [("id", "in", self.wht_cert_ids.ids)]
        return result

    def js_assign_outstanding_line(self, line_id):
        move_line = self.env["account.move.line"].browse(line_id)
        if move_line.payment_id:
            self = self.with_context(net_invoice_payment=True)
        self = self.with_context(net_invoice_refund=True)
        return super().js_assign_outstanding_line(line_id)

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
                    and l.tax_line_id.type_tax_use != "sale"
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
                            line_reconcile = moves.mapped("line_ids").filtered(
                                lambda l: l.account_id != tax_invoice.account_id
                                and l.reconciled
                            )
                            line_reconcile.reconcile()
                        continue
                    elif self.env.context.get("net_invoice_refund"):
                        continue
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

        res = super()._post(soft=soft)

        # Sales Taxes (exclude reconcile manual)
        if not self.env.context.get("net_invoice_refund"):
            for move in self:
                for tax_invoice in move.tax_invoice_ids.filtered(
                    lambda l: l.tax_line_id.type_tax_use == "sale"
                    or l.move_id.journal_id.type == "sale"
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

        # Check amount tax invoice with move line
        # kittiu: There are case that we don't want to check
        # for move in self:
        #     move.line_ids._checkout_tax_invoice_amount()

        # Withholding Tax:
        # - Create account.withholding.move, for every withholding tax line
        # - For case PIT, it is possible that there is no withholidng amount
        #   but still need to keep track the withholding.move base amount
        for move in self:
            # Normal case, create withholding.move only when withholding
            wht_moves = move.line_ids.filtered("account_id.wht_account")
            withholding_moves = [
                (0, 0, self._prepare_withholding_move(wht_move))
                for wht_move in wht_moves
            ]
            move.write({"wht_move_ids": [(5, 0, 0)] + withholding_moves})
            # On payment JE, keep track of move when PIT not withheld, use data from vendor bill
            if move.payment_id and not move.payment_id.wht_move_ids.mapped("is_pit"):
                if self.env.context.get("active_model") == "account.move":
                    bills = self.env["account.move"].browse(
                        self.env.context.get("active_ids", [])
                    )
                    bill_wht_lines = bills.mapped("line_ids").filtered(
                        "wht_tax_id.is_pit"
                    )
                    bill_wht_moves = [
                        (0, 0, self._prepare_withholding_move(bill_wht_move))
                        for bill_wht_move in bill_wht_lines
                    ]
                    move.write({"wht_move_ids": bill_wht_moves})
        # When post, do remove the existing certs
        self.mapped("wht_cert_ids").unlink()
        return res

    def _prepare_withholding_move(self, wht_move):
        """Prepare dict for account.withholding.move"""
        amount_income = wht_move.tax_base_amount
        amount_wht = abs(wht_move.balance)
        # In case, PIT is not withhold, but need to track from invoice
        if wht_move.move_id.move_type == "in_invoice":
            amount_income = abs(wht_move.balance)
            amount_wht = 0.0
        if wht_move.move_id.move_type == "in_refund":
            amount_income = -abs(wht_move.balance)
            amount_wht = 0.0
        return {
            "partner_id": wht_move.partner_id.id,
            "amount_income": amount_income,
            "amount_wht": amount_wht,
            "wht_tax_id": wht_move.wht_tax_id.id,
            "wht_cert_income_type": wht_move.wht_tax_id.wht_cert_income_type,
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
                number = (
                    tax_invoice.payment_id.name
                    if self.env.company.customer_tax_name == "payment"
                    else tax_invoice.move_id.ref
                ) or origin_move.name
        return (number, invoice_date)

    def _reverse_moves(self, default_values_list=None, cancel=False):
        self = self.with_context(reverse_tax_invoice=True)
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
        if self.wht_move_ids.filtered(lambda l: not l.wht_cert_income_type):
            raise UserError(
                _("Please select Type of Income on every withholding moves")
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
                filter(lambda l: l["partner_id"][0] == partner.id, wht_move_groups)
            )
            for wht_move in wht_moves:
                cert_line_vals.append(
                    (
                        0,
                        0,
                        {
                            "wht_cert_income_type": wht_move["wht_cert_income_type"],
                            "wht_cert_income_desc": wht_move["wht_cert_income_desc"],
                            "base": wht_move["amount_income"],
                            "amount": wht_move["amount_wht"],
                            "wht_tax_id": wht_move["wht_tax_id"][0],
                        },
                    )
                )
                wht_tax_set.add(wht_move["wht_tax_id"][0])
            cert_vals = {
                "move_id": self.id,
                "payment_id": self.payment_id.id,
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

    def _serialize_tax_grouping_key(self, grouping_dict):
        return "-".join(str(v) for v in grouping_dict.values())

    def _compute_base_line_taxes(self, base_line):
        move = base_line.move_id

        if move.is_invoice(include_receipts=True):
            handle_price_include = True
            sign = -1 if move.is_inbound() else 1
            quantity = base_line.quantity
            is_refund = move.move_type in ("out_refund", "in_refund")
            price_unit_wo_discount = (
                sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
            )
        else:
            handle_price_include = False
            quantity = 1.0
            tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
            is_refund = (tax_type == "sale" and base_line.debit) or (
                tax_type == "purchase" and base_line.credit
            )
            price_unit_wo_discount = base_line.amount_currency

        return base_line.tax_ids._origin.with_context(
            force_sign=move._get_tax_force_sign()
        ).compute_all(
            price_unit_wo_discount,
            currency=base_line.currency_id,
            quantity=quantity,
            product=base_line.product_id,
            partner=base_line.partner_id,
            is_refund=is_refund,
            handle_price_include=handle_price_include,
            include_caba_tags=move.always_tax_exigible,
        )

    def mount_base_lines(self, recompute_tax_base_amount, taxes_map):
        for line in self.line_ids.filtered(
            lambda line: not line.tax_repartition_line_id
        ):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = self._compute_base_line_taxes(line)

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tax_tag_ids = compute_all_vals["base_tags"] or [(5, 0, 0)]

            for tax_vals in compute_all_vals["taxes"]:
                grouping_dict = self._get_tax_grouping_key_from_base_line(
                    line, tax_vals
                )
                grouping_key = self._serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env["account.tax.repartition.line"].browse(
                    tax_vals["tax_repartition_line_id"]
                )
                # NOTE: comment it because not used
                # tax = (
                #     tax_repartition_line.invoice_tax_id
                #     or tax_repartition_line.refund_tax_id
                # )
                taxes_map_entry = taxes_map.setdefault(
                    grouping_key,
                    {
                        "tax_line": None,
                        "amount": 0.0,
                        "tax_base_amount": 0.0,
                        "grouping_dict": False,
                    },
                )
                taxes_map_entry["amount"] += tax_vals["amount"]
                taxes_map_entry["tax_base_amount"] += self._get_base_amount_to_display(
                    tax_vals["base"], tax_repartition_line, tax_vals["group"]
                )
                taxes_map_entry["grouping_dict"] = grouping_dict

    def _recompute_tax_lines(
        self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None
    ):
        """Overwrite core odoo for create tax lines with zero taxes"""
        self.ensure_one()
        in_draft_mode = self != self._origin
        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env["account.move.line"]
        for line in self.line_ids.filtered("tax_repartition_line_id"):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = self._serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    "tax_line": line,
                    "amount": 0.0,
                    "tax_base_amount": 0.0,
                    "grouping_dict": False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        # NOTE: Overwrite add new function for fix too complex
        # ==== Mount base lines ====
        self.mount_base_lines(recompute_tax_base_amount, taxes_map)

        # ==== Pre-process taxes_map ====
        taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
            if taxes_map_entry["tax_line"] and not taxes_map_entry["grouping_dict"]:
                if not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry["tax_line"]
                continue

            currency = self.env["res.currency"].browse(
                taxes_map_entry["grouping_dict"]["currency_id"]
            )

            # NOTE: OVERWRITE HERE
            # Don't create tax lines with zero balance.
            # if currency.is_zero(taxes_map_entry['amount']):
            #     if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
            #         self.line_ids -= taxes_map_entry['tax_line']
            #     continue

            # tax_base_amount field is expressed using the company currency.
            tax_base_amount = currency._convert(
                taxes_map_entry["tax_base_amount"],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self),
            )

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry["tax_line"]:
                    taxes_map_entry["tax_line"].tax_base_amount = tax_base_amount
                continue

            balance = currency._convert(
                taxes_map_entry["amount"],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self),
            )
            to_write_on_line = {
                "amount_currency": taxes_map_entry["amount"],
                "currency_id": taxes_map_entry["grouping_dict"]["currency_id"],
                "debit": balance > 0.0 and balance or 0.0,
                "credit": balance < 0.0 and -balance or 0.0,
                "tax_base_amount": tax_base_amount,
            }

            if taxes_map_entry["tax_line"]:
                # Update an existing tax line.
                if (
                    tax_rep_lines_to_recompute
                    and taxes_map_entry["tax_line"].tax_repartition_line_id
                    not in tax_rep_lines_to_recompute
                ):
                    continue

                taxes_map_entry["tax_line"].update(to_write_on_line)
            else:
                # Create a new tax line.
                create_method = (
                    in_draft_mode
                    and self.env["account.move.line"].new
                    or self.env["account.move.line"].create
                )
                tax_repartition_line_id = taxes_map_entry["grouping_dict"][
                    "tax_repartition_line_id"
                ]
                tax_repartition_line = self.env["account.tax.repartition.line"].browse(
                    tax_repartition_line_id
                )

                if (
                    tax_rep_lines_to_recompute
                    and tax_repartition_line not in tax_rep_lines_to_recompute
                ):
                    continue

                tax = (
                    tax_repartition_line.invoice_tax_id
                    or tax_repartition_line.refund_tax_id
                )
                taxes_map_entry["tax_line"] = create_method(
                    {
                        **to_write_on_line,
                        "name": tax.name,
                        "move_id": self.id,
                        "company_id": self.company_id.id,
                        "company_currency_id": self.company_currency_id.id,
                        "tax_base_amount": tax_base_amount,
                        "exclude_from_invoice_tab": True,
                        **taxes_map_entry["grouping_dict"],
                    }
                )

            if in_draft_mode:
                taxes_map_entry["tax_line"].update(
                    taxes_map_entry["tax_line"]._get_fields_onchange_balance(
                        force_computation=True
                    )
                )
