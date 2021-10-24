# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        """ Use Bill Reference and Date from Expense Line as Tax Invoice """
        # Expense Taxes
        for move in self:
            for tax_invoice in move.tax_invoice_ids.filtered(
                lambda l: l.tax_line_id.type_tax_use == "purchase"
            ):
                if tax_invoice.move_line_id.expense_id:
                    tinv_number = tax_invoice.move_line_id.expense_id.reference
                    tinv_date = tax_invoice.move_line_id.expense_id.date
                    tax_invoice.write(
                        {
                            "tax_invoice_number": tinv_number,
                            "tax_invoice_date": tinv_date,
                        }
                    )
                    bill_partner = tax_invoice.move_line_id.expense_id.bill_partner_id
                    if bill_partner:
                        tax_invoice.write({"partner_id": bill_partner.id})
        return super()._post(soft)
