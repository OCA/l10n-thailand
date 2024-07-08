# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Department(models.Model):
    _inherit = "hr.department"

    tier_level_ids = fields.One2many(
        string="Approval Level",
        comodel_name="tier.level",
        inverse_name="department_id",
    )

    def find_reviewer_level(self, level=0):
        self.ensure_one()
        num_level = len(self.tier_level_ids)
        if not (level and num_level):
            return self.env.user
        tier_level_ids = self.tier_level_ids.sorted(key=lambda t: t.level)
        return (
            tier_level_ids[level - 1].user_id
            if level <= num_level
            else tier_level_ids[-1].user_id
        )
