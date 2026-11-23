# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    acc_holder_name_en = fields.Char(
        compute="_compute_account_holder_name_en",
        readonly=False,
        store=True,
        string="Account Holder Name (EN)",
        help="Account holder name, in case it is bank bahtnet",
    )

    @api.depends("partner_id.name")
    def _compute_account_holder_name_en(self):
        for bank in self:
            bank.acc_holder_name_en = bank.partner_id.name
