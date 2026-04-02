# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_bank_payment_profile_id = fields.Many2one(
        comodel_name="bank.payment.profile",
        string="Bank Payment Profile",
        company_dependent=True,
        check_company=True,
        help="Default bank payment profile on each partner.",
    )
