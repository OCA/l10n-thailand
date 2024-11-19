# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo import api, fields, models


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
            tax.sequence_number_next = 1
            if tax.taxinv_sequence_id:
                sequence = tax.taxinv_sequence_id._get_current_sequence()
                tax.sequence_number_next = sequence.number_next_actual

    def _inverse_seq_number_next(self):
        for tax in self:
            if tax.taxinv_sequence_id and tax.sequence_number_next:
                sequence = tax.taxinv_sequence_id._get_current_sequence()
                sequence.sudo().number_next = tax.sequence_number_next

    @api.model
    def _prepare_base_line_tax_repartition_grouping_key(
        self, base_line, base_line_grouping_key, tax_data, tax_rep_data
    ):
        grouping_key = super()._prepare_base_line_tax_repartition_grouping_key(
            base_line, base_line_grouping_key, tax_data, tax_rep_data
        )

        # Check company from record
        if base_line.get("record") and base_line.get("record").company_id.tax_zero_line:
            grouping_key["__keep_zero_line"] = True

        return grouping_key
