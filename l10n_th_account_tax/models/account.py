# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    wht_account = fields.Boolean(
        string="WHT Account",
        default=False,
        help="If check, this account is for withholding tax",
    )


class AccountTax(models.Model):
    _inherit = "account.tax"

    taxinv_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Tax Invoice Sequence",
        help="Optional sequence as Tax Invoice number",
        copy=False,
    )
    sequence_number_next = fields.Integer(
        string="Next Number",
        help="The next sequence number will be used for the next tax invoice.",
        compute="_compute_seq_number_next",
        inverse="_inverse_seq_number_next",
    )

    @api.depends(
        "taxinv_sequence_id.use_date_range", "taxinv_sequence_id.number_next_actual"
    )
    def _compute_seq_number_next(self):
        for tax in self:
            if tax.taxinv_sequence_id:
                sequence = tax.taxinv_sequence_id._get_current_sequence()
                tax.sequence_number_next = sequence.number_next_actual
            else:
                tax.sequence_number_next = 1

    def _inverse_seq_number_next(self):
        for tax in self:
            if tax.taxinv_sequence_id and tax.sequence_number_next:
                sequence = tax.taxinv_sequence_id._get_current_sequence()
                sequence.sudo().number_next = tax.sequence_number_next
