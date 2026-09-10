# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class BankTemplate(models.Model):
    _inherit = "bank.template"

    bank = fields.Selection(
        selection_add=[("KASITHBK", "KBank")],
        ondelete={"KASITHBK": "cascade"},
    )
    kbank_transfer_type = fields.Selection(
        selection=[
            ("same_bank", "Same Bank"),
            ("other_bank", "Other Bank"),
        ],
        string="Transfer Type",
    )


class BankTemplateLine(models.Model):
    _inherit = "bank.template.line"

    def _get_value(self, globals_dict):
        if self.template_id.bank == "KASITHBK":
            value = (
                safe_eval(self.expression, globals_dict=globals_dict)
                if self.source_type == "expression"
                else self.fixed_value
            )
            text = str(value or "")
            if any(ord(char) < 32 for char in text):
                raise ValidationError(
                    self.env._(
                        "KBank field %s contains a line break or control character.",
                        self.name,
                    )
                )
            if self.padding == "0" and len(text) > self.field_length:
                raise ValidationError(
                    self.env._("KBank field %s exceeds its allowed length.", self.name)
                )
        return super()._get_value(globals_dict)
