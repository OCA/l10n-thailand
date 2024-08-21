# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        move_lines = super().create(vals_list)
        for line in move_lines:
            invoice_inter_company = line.move_id.auto_invoice_id
            # If this is an inter company invoice, copy tax invoice number and date
            if (
                invoice_inter_company
                and invoice_inter_company.move_type == "out_invoice"
            ):
                tax_invoices = invoice_inter_company.tax_invoice_ids
                line.tax_invoice_ids.write(
                    {
                        "tax_invoice_number": tax_invoices.tax_invoice_number,
                        "tax_invoice_date": tax_invoices.tax_invoice_date,
                    }
                )
        return move_lines
