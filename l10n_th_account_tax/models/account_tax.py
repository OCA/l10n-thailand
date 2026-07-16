# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountTax(models.Model):
    _inherit = "account.tax"

    taxinv_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Tax Invoice Sequence",
        help="Optional sequence as Tax Invoice number",
        copy=False,
    )
    reverse_tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Reverse Tax (Credit Note)",
        domain="[('type_tax_use', '=', type_tax_use), "
        "('tax_exigibility', '=', 'on_invoice'), "
        "('company_id', '=', company_id)]",
        check_company=True,
        help="Replacement tax for credit notes when the original invoice is paid.",
    )

    @api.constrains("reverse_tax_id")
    def _check_reverse_tax_id(self):
        for tax in self:
            reverse_tax = tax.reverse_tax_id
            if not reverse_tax:
                continue
            if tax.tax_exigibility != "on_payment":
                raise ValidationError(
                    self.env._(
                        "Reverse Tax can only be set on a cash basis (undue) tax."
                    )
                )
            if reverse_tax.tax_exigibility != "on_invoice":
                raise ValidationError(
                    self.env._("Reverse Tax must be a due ('on invoice') tax.")
                )
            if reverse_tax.type_tax_use != tax.type_tax_use:
                raise ValidationError(
                    self.env._("Reverse Tax must have the same Tax Scope.")
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
