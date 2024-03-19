# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountPaymentDeductionPerm(models.Model):
    _name = "account.payment.deduction.perm"
    _inherit = "account.payment.deduction"
    _description = "Payment Deduction Line Permanemt Model"

    payment_id = fields.Many2one(
        comodel_name="account.payment.register.perm",
        readonly=True,
        ondelete="cascade",
    )
