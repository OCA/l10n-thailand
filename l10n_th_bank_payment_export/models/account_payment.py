# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    export_status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("to_export", "To Export"),
            ("exported", "Exported"),
        ],
        default="draft",
        copy=False,
        readonly=True,
        tracking=True,
        help="it means status the money has already been sent to the bank.",
    )
    payment_export_id = fields.Many2one(
        comodel_name="bank.payment.export",
        string="Payment Export",
        index=True,
        copy=False,
        readonly=True,
        tracking=True,
        help="Link to Bank Payment Export",
    )
    bank_payment_template_id = fields.Many2one(
        comodel_name="bank.payment.template",
        tracking=True,
        help="it help default value from bank payment template",
    )
