# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_asset_vals(self, aml):
        res = super()._prepare_asset_vals(aml)
        work_acceptance = aml.move_id.wa_id
        if work_acceptance:
            res.update({"date_start": work_acceptance.date_accept})
        return res
