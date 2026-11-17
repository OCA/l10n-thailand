# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_invoice_ids = fields.One2many(
        comodel_name="account.move.tax.invoice", inverse_name="move_line_id"
    )
    manual_tax_invoice = fields.Boolean(
        copy=False, help="Create Tax Invoice for this debit/credit line"
    )

    def _get_withholding_taxes(self):
        self.ensure_one()
        return self.tax_ids.flatten_taxes_hierarchy().filtered("is_withholding_tax")

    @api.constrains("tax_ids")
    def _check_single_withholding_tax(self):
        """One line is one type of income, so it can be withheld only once."""
        invalid_lines = self.filtered(
            lambda line: len(line._get_withholding_taxes()) > 1
        )
        if invalid_lines:
            raise ValidationError(
                self.env._(
                    "Only one withholding tax is allowed per line.\n%(lines)s",
                    lines="\n".join(
                        "- {}: {}".format(
                            line.display_name,
                            ", ".join(line._get_withholding_taxes().mapped("name")),
                        )
                        for line in invalid_lines
                    ),
                )
            )

    def _is_tax_invoice_line(self):
        """VAT lines of Thai companies need a tax invoice.
        Withholding tax lines do not."""
        self.ensure_one()
        tax = self.tax_line_id
        return bool(
            tax
            and self.move_id.country_code == "TH"
            and not tax.is_withholding_tax
            and (
                tax.tax_exigibility == "on_invoice"
                or self.move_id.tax_cash_basis_origin_move_id
            )
        )

    def _prepare_move_tax_invoice(self):
        self.ensure_one()
        move = self.move_id
        return {
            "move_id": move.id,
            "move_line_id": self.id,
            "partner_id": self.partner_id.id,
            "reversed_id": move.move_type == "entry" and move.reversed_entry_id.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.filtered(
            lambda line: (
                (line.manual_tax_invoice and line.move_id.country_code == "TH")
                or line._is_tax_invoice_line()
            )
        )._create_tax_invoices()
        return lines

    def _create_tax_invoices(self):
        # Created by the system, also for users without access to tax invoices
        tax_invoices = (
            self.env["account.move.tax.invoice"]
            .sudo()
            .create([line._prepare_move_tax_invoice() for line in self])
        )
        # Reversed journal entry, link back the tax invoices of the origin
        for tax_invoice in tax_invoices.filtered("reversed_id"):
            tax_invoice.reversed_id.tax_invoice_ids.reversing_id = tax_invoice.move_id
        return tax_invoices

    def write(self, vals):
        """Tax invoice for a line without tax, e.g. VAT recorded manually
        on a journal entry"""
        if "manual_tax_invoice" not in vals:
            return super().write(vals)
        manual_lines = self.filtered(
            lambda line: (
                line.move_id.country_code == "TH"
                and not line._is_tax_invoice_line()
                and line.manual_tax_invoice != vals["manual_tax_invoice"]
            )
        )
        res = super().write(vals)
        if vals["manual_tax_invoice"]:
            manual_lines.filtered(
                lambda line: not line.tax_invoice_ids
            )._create_tax_invoices()
        else:
            manual_lines.tax_invoice_ids.sudo().with_context(
                force_remove_tax_invoice=True
            ).unlink()
        return res

    def copy_data(self, default=None):
        """Reversal of a journal entry keeps its manual tax invoices"""
        vals_list = super().copy_data(default=default)
        if "move_reverse_cancel" in self.env.context:
            for line, vals in zip(self, vals_list, strict=True):
                vals.setdefault("manual_tax_invoice", line.manual_tax_invoice)
        return vals_list
