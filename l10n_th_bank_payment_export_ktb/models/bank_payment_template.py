# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankPaymentTemplate(models.Model):
    _inherit = "bank.payment.template"

    bank = fields.Selection(
        selection_add=[("KRTHTHBK", "KTB")],
        ondelete={"KRTHTHBK": "cascade"},
    )
