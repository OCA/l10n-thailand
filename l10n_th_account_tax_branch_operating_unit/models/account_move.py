# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    domain_branch_ids = fields.Many2many(
        comodel_name="res.branch",
        compute="_compute_branch_domain",
        help="Helper field, the filtered tags_ids when record is saved",
    )

    @api.depends("operating_unit_id")
    def _compute_branch_domain(self):
        for rec in self:
            rec.domain_branch_ids = rec.operating_unit_id.branch_ids.ids or False

    @api.onchange("operating_unit_id")
    def _onchange_operating_unit(self):
        res = super()._onchange_operating_unit()
        # Default branch from OU
        if len(self.domain_branch_ids) == 1:
            self.branch_id = self.domain_branch_ids.id
        # Clear branch if it not in domain branch
        if self.branch_id._origin.id not in self.domain_branch_ids.ids:
            self.branch_id = False
        return res
