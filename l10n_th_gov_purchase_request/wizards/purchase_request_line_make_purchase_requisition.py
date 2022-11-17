# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import UserError


class PurchaseRequestLineMakePurchaseRequisition(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.requisition"

    @api.model
    def view_init(self, fields):
        """Do not allow, if,
        - Some PRs is not approved
        - Some PRs' purchase type is not for Purchase Agreement"""
        context = self._context
        active_model = context.get("active_model")
        active_ids = context.get("active_ids")
        if active_model and active_ids:
            records = self.env[active_model].browse(active_ids)
            pr = records  # expect purchase.request
            if active_model == "purchase.request.line":
                pr = records.mapped("request_id")
            # Some PRs is not approved
            if pr.filtered(lambda l: l.state != "approved"):
                raise UserError(
                    _(
                        "Only approved document is allowed to "
                        "create purchase agreement"
                    )
                )
            if pr.filtered(lambda l: l.to_create != "purchase_agreement"):
                raise UserError(
                    _(
                        "Selected document's purchase type is not "
                        "allowed to create purchase agreement"
                    )
                )
        return super().view_init(fields)
