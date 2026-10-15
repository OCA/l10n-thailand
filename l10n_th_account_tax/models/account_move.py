# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

from odoo import Command, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain

from .withholding_tax_cert import L10N_TH_WTH_CONDITION_TAX_PAYER


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
        string="Withholding Tax Certificates",
        readonly=True,
    )
    has_wht = fields.Boolean(
        string="Has Withholding Tax",
        compute="_compute_has_wht",
        store=True,
        help="Journal entry withholding a purchase withholding tax, "
        "for which withholding tax certificates can be created",
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

    @api.depends(
        "country_code",
        "move_type",
        "line_ids.balance",
        "line_ids.tax_ids",
        "line_ids.tax_line_id",
        "line_ids.partner_id",
    )
    def _compute_has_wht(self):
        for move in self:
            currency = move.company_id.currency_id
            move.has_wht = any(
                currency.compare_amounts(amounts["base"], 0.0) > 0
                for amounts in move._get_wht_cert_source_values().values()
            )

    @api.depends("has_wht", "wht_cert_ids.state")
    def _compute_wht_cert_status(self):
        for move in self:
            active_certs = move.wht_cert_ids.filtered(lambda c: c.state != "cancel")
            if not move.has_wht:
                move.wht_cert_status = False
            elif not move.wht_cert_ids:
                move.wht_cert_status = "none"
            elif not active_certs:
                move.wht_cert_status = "cancel"
            elif "draft" in active_certs.mapped("state"):
                move.wht_cert_status = "draft"
            else:
                move.wht_cert_status = "done"

    def button_wht_certs(self):
        return self.env["withholding.tax.cert"]._get_wht_certs_action(
            [("id", "in", self.wht_cert_ids.ids)]
        )

    def action_create_wht_cert(self):
        """Create withholding tax certificates and show them"""
        self.create_wht_cert()
        return self.button_wht_certs()

    def _get_pit_taxes(self):
        """PIT taxes on the product lines of a vendor bill"""
        self.ensure_one()
        if self.move_type not in ("in_invoice", "in_receipt"):
            return self.env["account.tax"]
        lines = self.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        return lines.tax_ids.flatten_taxes_hierarchy().filtered("is_pit")

    def _get_pit_deducted_amount(self):
        """PIT withheld by the payments of this invoice, in invoice currency.
        Same computation as standard withholding_deducted_amount_currency."""
        self.ensure_one()
        deducted = 0.0
        if not self.is_invoice(include_receipts=True):
            return deducted
        for line in self.line_ids.filtered(lambda l: l.display_type == "payment_term"):
            partial_fname, counterpart_line_fname, amount_fname = (
                ("matched_credit_ids", "credit_move_id", "credit_amount_currency")
                if line.debit
                else ("matched_debit_ids", "debit_move_id", "debit_amount_currency")
            )
            partials_by_move = line[partial_fname].grouped(
                lambda p, fname=counterpart_line_fname: p[fname].move_id
            )
            for counterpart_move, partials in partials_by_move.items():
                ratio = sum(
                    partial[amount_fname] / counterpart_amount
                    for partial in partials
                    if (
                        counterpart_amount := partial[
                            counterpart_line_fname
                        ].amount_currency
                    )
                )
                deducted += sum(
                    pit_line.currency_id._convert(
                        from_amount=-pit_line.amount_currency * ratio,
                        to_currency=self.currency_id,
                        company=self.company_id,
                        date=counterpart_move.date,
                        round=False,
                    )
                    for pit_line in counterpart_move.line_ids.filtered(
                        "tax_line_id.is_pit"
                    )
                )
        return deducted

    @api.depends(
        "withholding_total_amount_currency",
        "line_ids.matched_debit_ids",
        "line_ids.matched_credit_ids",
    )
    def _compute_deducted_withholding_amount(self):
        """PIT is computed on payments only (0% on invoices), so its deduction
        must not reduce the residual of other withholding taxes"""
        res = super()._compute_deducted_withholding_amount()
        for move in self:
            move.withholding_deducted_amount_currency -= move._get_pit_deducted_amount()
        return res

    def _get_wht_cert_source_values(self):
        """Return withholding amounts of this journal entry, from journal items.

        - Base: journal items carrying a purchase withholding tax in tax_ids
          (e.g. expense line of a manual entry, "WH Base Counterpart" of a payment)
        - Withheld amount: tax lines of this withholding tax

        Amounts are signed in company currency, positive for a normal withholding.
        Thai companies only.
        :return: {(partner, tax): {"base": float, "amount": float}}
        """
        self.ensure_one()
        values = defaultdict(lambda: {"base": 0.0, "amount": 0.0})
        if (
            self.country_code != "TH"
            or self.move_type != "entry"
            or self.tax_cash_basis_origin_move_id
        ):
            return values
        for line in self.line_ids:
            partner = line.partner_id or self.partner_id
            if line.tax_line_id:
                tax = line.tax_line_id
                if tax.is_withholding_tax and tax.type_tax_use == "purchase":
                    values[(partner, tax)]["amount"] -= line.balance
                continue
            for tax in line._get_withholding_taxes():
                if tax.type_tax_use == "purchase":
                    values[(partner, tax)]["base"] += line.balance
        return values

    def _prepare_wht_cert_vals(self, partner, income_tax_form, tax_values):
        self.ensure_one()
        return {
            "move_id": self.id,
            "payment_id": self.origin_payment_id.id,
            "partner_id": partner.id,
            "company_id": self.company_id.id,
            "company_partner_id": self.company_id.partner_id.id,
            "date": self.date,
            "income_tax_form": income_tax_form,
            "tax_payer": L10N_TH_WTH_CONDITION_TAX_PAYER.get(
                self.origin_payment_id.l10n_th_wth_condition, "withholding"
            ),
            "wht_line": [
                Command.create(
                    {
                        "wht_tax_id": tax.id,
                        "wht_cert_income_type": tax._get_wht_cert_income_type(),
                        "base": amounts["base"],
                        "amount": amounts["amount"],
                    }
                )
                for tax, amounts in tax_values
            ],
        }

    def create_wht_cert(self):
        """Create one withholding tax certificate per partner and income tax
        form, except for those already having an active certificate."""
        self.ensure_one()
        if self.state != "posted":
            raise UserError(
                self.env._("Withholding tax certificates need a posted entry.")
            )
        currency = self.company_id.currency_id
        partner_taxes = defaultdict(list)
        for (partner, tax), amounts in self._get_wht_cert_source_values().items():
            if currency.compare_amounts(amounts["base"], 0.0) <= 0:
                continue
            if not partner:
                raise UserError(
                    self.env._(
                        "Please set a partner on journal items with withholding "
                        "tax %(tax)s.",
                        tax=tax.display_name,
                    )
                )
            form = tax._get_wht_cert_income_tax_form(partner)
            partner_taxes[(partner, form)].append((tax, amounts))
        # By taxes, as the income tax form can be changed on the certificate
        active_partner_taxes = {
            (cert.partner_id, tax)
            for cert in self.wht_cert_ids
            if cert.state != "cancel"
            for tax in cert.wht_line.wht_tax_id
        }
        vals_list = []
        for (partner, form), tax_values in partner_taxes.items():
            new_tax_values = [
                (tax, amounts)
                for tax, amounts in tax_values
                if (partner, tax) not in active_partner_taxes
            ]
            if new_tax_values:
                vals_list.append(
                    self._prepare_wht_cert_vals(partner, form, new_tax_values)
                )
        if not vals_list:
            raise UserError(
                self.env._("There is no withholding tax certificate to create.")
            )
        certs = self.env["withholding.tax.cert"].create(vals_list)
        # Default description and income code, as when the user selects the type
        for line in certs.wht_line.filtered("wht_cert_income_type"):
            line._onchange_wht_cert_income_type()
            if line.wht_tax_id.l10n_th_income_tax_type == "others":
                line.wht_cert_income_desc = (
                    line.wht_tax_id.l10n_th_income_tax_type_others
                    or line.wht_cert_income_desc
                )
        return certs

    def copy(self, default=None):
        """Reversal of vendor bills, tax invoice of the vendor credit note
        from the reversal wizard"""
        new_moves = super().copy(default)
        tax_number = self.env.context.get("tax_invoice_number")
        tax_date = self.env.context.get("tax_invoice_date")
        if "move_reverse_cancel" in self.env.context and (tax_number or tax_date):
            new_moves.tax_invoice_ids.sudo().write(
                {"tax_invoice_number": tax_number, "tax_invoice_date": tax_date}
            )
        return new_moves

    def _is_undue_vat_on_hold(self):
        """Undue purchase VAT entry waiting for the vendor's tax invoice,
        it is posted when the tax is cleared"""
        self.ensure_one()
        return bool(
            self.state == "draft"
            and self.tax_cash_basis_origin_move_id
            and self.tax_invoice_ids.filtered(
                lambda tinv: tinv._is_missing_vendor_info()
            )
        )

    def _check_purchase_tax_invoices(self):
        """Purchase tax invoices are issued by the vendor, their number and
        date must be filled in before posting."""
        self.ensure_one()
        for tax_invoice in self.tax_invoice_ids.filtered(
            lambda tinv: tinv._is_missing_vendor_info()
        ):
            # Reversed journal entry, use the tax invoice of the origin
            origin = self.move_type == "entry" and self.reversed_entry_id
            origin_tax_invoice = (
                origin
                and origin.tax_invoice_ids.filtered(
                    lambda tinv, ti=tax_invoice: (
                        tinv.tax_line_id == ti.tax_line_id
                        and tinv.account_id == ti.account_id
                    )
                )[:1]
            )
            if not origin_tax_invoice:
                tax_invoice._raise_missing_vendor_info()
            tax_invoice.sudo().write(
                {
                    "tax_invoice_number": origin_tax_invoice.tax_invoice_number,
                    "tax_invoice_date": origin_tax_invoice.tax_invoice_date,
                }
            )

    def _get_tax_invoice_number(self, tax_invoice):
        """Number of a sales tax invoice, issued by us:
        - Tax invoice sequence on the tax, the reversed journal entry
          keeps the number of the origin
        - Undue VAT, payment or invoice number, following the config
        - Otherwise, the document number
        """
        self.ensure_one()
        origin_move = self.move_type == "entry" and self.reversed_entry_id or self
        sequence = tax_invoice.tax_line_id.taxinv_sequence_id
        if sequence:
            if origin_move != self:
                return origin_move.tax_invoice_ids.filtered(
                    lambda tinv: tinv.tax_line_id == tax_invoice.tax_line_id
                )[:1].tax_invoice_number
            return sequence.sudo().next_by_id(sequence_date=self.date)
        cash_basis_origin = self.tax_cash_basis_origin_move_id
        if cash_basis_origin:
            if self.company_id.customer_tax_invoice_number == "payment":
                return tax_invoice.payment_id.name or cash_basis_origin.name
            return cash_basis_origin.name
        return origin_move.name

    def _set_sales_tax_invoices(self):
        """Sales tax invoices are issued by us, number them on posting"""
        self.ensure_one()
        for tax_invoice in self.tax_invoice_ids.filtered(
            lambda tinv: not tinv._is_purchase_tax_invoice()
        ):
            vals = {}
            if tax_invoice.tax_invoice_number in (False, "/"):
                vals["tax_invoice_number"] = self._get_tax_invoice_number(tax_invoice)
            if not tax_invoice.tax_invoice_date:
                vals["tax_invoice_date"] = self.date
            if vals:
                tax_invoice.sudo().write(vals)

    @api.model
    def _get_th_moves_domain(self, additional_domain=None):
        """No standard Thai tax invoices, replaced by the tax invoices of this
        module, for purchases and sales"""
        return Domain.FALSE

    def _post(self, soft=True):
        moves = self
        # Undue VAT entries created on payment wait for the tax invoice
        if self.env.context.get("hold_undue_vat"):
            moves = self.filtered(lambda move: not move._is_undue_vat_on_hold())
        for move in moves:
            move._check_purchase_tax_invoices()
        posted = super(AccountMove, moves)._post(soft=soft)
        for move in posted:
            move._set_sales_tax_invoices()
        return posted

    def write(self, vals):
        """Standard also posts the draft undue VAT entries when posting the
        reconciled documents, keep those waiting for the tax invoice"""
        if vals.get("state") != "posted":
            return super().write(vals)
        on_hold = self.filtered(lambda move: move._is_undue_vat_on_hold())
        res = super(AccountMove, self - on_hold).write(vals)
        other_vals = {
            key: value
            for key, value in vals.items()
            if key not in ("state", "posted_before")
        }
        if on_hold and other_vals:
            super(AccountMove, on_hold).write(other_vals)
        # Number sales undue VAT entries posted this way
        for move in (self - on_hold).filtered("tax_cash_basis_origin_move_id"):
            move._set_sales_tax_invoices()
        return res

    def button_draft(self):
        res = super().button_draft()
        self.wht_cert_ids.action_cancel()
        return res

    def button_cancel(self):
        res = super().button_cancel()
        self.wht_cert_ids.action_cancel()
        return res

    def _prepare_product_base_line_for_taxes_computation(self, product_line):
        """Compute withholding taxes on manual journal entries of Thai companies
        too. Standard only computes them on journal entries created by payments."""
        base_line = super()._prepare_product_base_line_for_taxes_computation(
            product_line
        )
        if (
            self.country_code == "TH"
            and self.move_type == "entry"
            and not self.origin_payment_id
            and not self.tax_cash_basis_origin_move_id
            and product_line._get_withholding_taxes()
        ):
            base_line["calculate_withholding_taxes"] = True
        return base_line
