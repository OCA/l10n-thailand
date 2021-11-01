# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    to_clear_tax = fields.Boolean(
        default=False,
        copy=False,
        help="When defer journal entry posting, this will show button",
    )
    tax_invoice_ids = fields.One2many(
        comodel_name="account.move.tax.invoice",
        inverse_name="payment_id",
        copy=False,
        domain=[("reversing_id", "=", False), ("reversed_id", "=", False)],
    )
    tax_invoice_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Tax Invoice's Journal Entry",
        compute="_compute_tax_invoice_move_id",
    )
    wht_move_ids = fields.One2many(
        comodel_name="account.withholding.move",
        inverse_name="payment_id",
        string="Withholding",
        copy=False,
        help="All withholding moves, including non-PIT",
    )
    pit_move_ids = fields.One2many(
        comodel_name="account.withholding.move",
        inverse_name="payment_id",
        string="Personal Income Tax",
        domain=[("is_pit", "=", True)],
        copy=False,
    )
    wht_cert_ids = fields.One2many(
        comodel_name="withholding.tax.cert",
        inverse_name="payment_id",
        string="Withholding Tax Cert.",
        readonly=True,
    )

    def button_wht_certs(self):
        self.ensure_one()
        action = self.env.ref("l10n_th_account_tax.action_withholding_tax_cert_menu")
        result = action.sudo().read()[0]
        result["domain"] = [("id", "in", self.wht_cert_ids.ids)]
        return result

    def clear_tax_cash_basis(self):
        for payment in self:
            for tax_invoice in payment.tax_invoice_ids:
                if (
                    not tax_invoice.tax_invoice_number
                    or not tax_invoice.tax_invoice_date
                ):
                    raise UserError(_("Please fill in tax invoice and tax date"))
            payment.write({"to_clear_tax": False})
            moves = payment.tax_invoice_ids.mapped("move_id")
            for move in moves.filtered(lambda l: l.state == "draft"):
                move.ensure_one()
                move.action_post()
        return True

    def _compute_tax_invoice_move_id(self):
        for payment in self:
            payment.tax_invoice_move_id = payment.tax_invoice_ids.mapped("move_id")[:1]

    def button_journal_entries(self):
        return {
            "name": _("Journal Entries"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", [self.move_id.id, self.tax_invoice_move_id.id])],
        }

    def create_wht_cert(self):
        self.ensure_one()
        self.move_id.create_wht_cert()

    def _update_move_line_writeoff(self, line_vals_list, write_off_line):
        """ Update partner of move line, when write off has partner_id """
        for line in line_vals_list:
            if line["name"] == write_off_line["name"]:
                # partner
                if write_off_line.get("partner_id"):
                    line["partner_id"] = write_off_line["partner_id"]
                # wht
                wht_amount_base_company = self.currency_id._convert(
                    write_off_line["wht_amount_base"],
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )
                line["tax_base_amount"] = wht_amount_base_company
                line["wht_tax_id"] = write_off_line.get("wht_tax_id")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        """ Overwrite default partner_id from write_off_line """
        line_vals_list = super()._prepare_move_line_default_vals(write_off_line_vals)
        if isinstance(write_off_line_vals, list) and write_off_line_vals:  # multi
            for write_off_line in write_off_line_vals:
                self._update_move_line_writeoff(line_vals_list, write_off_line)
        elif isinstance(write_off_line_vals, dict) and write_off_line_vals:  # single
            self._update_move_line_writeoff(line_vals_list, write_off_line_vals)
        return line_vals_list
