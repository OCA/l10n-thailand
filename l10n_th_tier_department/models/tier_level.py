# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class TierLevel(models.Model):
    _name = "tier.level"
    _description = "Tier Level"

    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
    )
    sequence = fields.Integer(default=10)
    level = fields.Integer(compute="_compute_level")
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Approver",
        required=True,
    )
    name = fields.Char(string="Description")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        help="Company related to this journal",
    )

    @api.depends("sequence")
    def _compute_level(self):
        TierLevel = self.env["tier.level"]
        for rec in self:
            tier_level_ids = TierLevel.search(
                [("department_id", "=", rec.department_id.id)], order="sequence"
            ).ids
            rec.level = (
                tier_level_ids.index(rec._origin.id) + 1
                if rec._origin.id in tier_level_ids
                else 0
            )
