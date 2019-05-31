# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        """ If any purchase tax, user must fill in tax invoice / date """
        vendor_tax_invoices = self.filtered(
            lambda inv: inv.state != 'open').mapped('tax_line_ids').filtered(
                lambda l: l.tax_id.type_tax_use == 'purchase')
        if vendor_tax_invoices:
            # For purchase tax, case vat, do filling tax invoice
            if vendor_tax_invoices.filtered(
                    lambda l: l.tax_id.tax_exigibility != 'on_payment' and
                    (not l.tax_invoice_manual or not l.tax_date_manual)):
                raise UserError(_("Please fill in tax invoice and tax date"))
            # For purchase tax, case undue vat, not allow filling tax invoice
            if vendor_tax_invoices.filtered(
                    lambda l: l.tax_id.tax_exigibility == 'on_payment' and
                    (l.tax_invoice_manual or l.tax_date_manual)):
                raise UserError(
                    _("Please do not fill in tax invoice for undue tax"))
        return super().action_invoice_open()


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    tax_invoice_manual = fields.Char(
        string='Tax Invoice Number',
        copy=False,
        help="Used for purchase invoice, when vendor will provide number\n"
        "this will always overwrite invoice's number",
    )
    tax_invoice = fields.Char(
        compute='_compute_tax_invoice',
        help="- case sales invoice/refund, use invoice number\n"
        "- case purchase invoice/refund, user will manually keyin\n",
    )
    tax_date_manual = fields.Date(
        copy=False,
    )
    tax_date = fields.Date(
        compute='_compute_tax_invoice',
    )
    move_line_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='invoice_tax_line_id',
        string='Journal Items',
        readonly=True,
    )

    @api.multi
    def _compute_tax_invoice(self):
        for tax_line in self:
            tax = tax_line.tax_id
            if tax.type_tax_use == 'purchase':  # Vendor Tax
                tax_line.tax_invoice = tax_line.tax_invoice_manual
                tax_line.tax_date = tax_line.tax_date_manual
            else:  # Customer Tax
                tax_line.tax_invoice = (tax_line.invoice_id.reference or
                                        tax_line.invoice_id.number)
                tax_line.tax_date = tax_line.invoice_id.date_invoice
        return True
