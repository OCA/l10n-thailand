# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class WorkAcceptance(models.Model):
    _inherit = "work.acceptance"
    _tier_validation_manual_config = True  # We need more buttons

    wa_tier_validation = fields.Boolean(
        string="Paperless WA",
        readonly=True,
        default=True,
        states={"draft": [("readonly", False)]},
        tracking=True,
        help="If checked, WA created will be approved by committee by tier valiation."
        "Each committee will be notified (by email or inbox) to approve WA.\n"
        "If not checked, WA will be approved by paper outside Odoo, "
        "and the result of WA will be filled in by procurement officer",
    )
    work_acceptance_committee_ids = fields.One2many(
        comodel_name="work.acceptance.committee",
        inverse_name="wa_id",
        string="Work Acceptance Committees",
        copy=True,
    )
    completeness = fields.Float(
        string="Progress",
        compute="_compute_completeness",
        store=True,
    )

    @api.depends("work_acceptance_committee_ids.status")
    def _compute_completeness(self):
        for rec in self:
            committees = len(rec.work_acceptance_committee_ids)
            rec.completeness = 0
            if committees:
                reviewed = len(rec.work_acceptance_committee_ids.filtered("status"))
                rec.completeness = reviewed / committees * 100

    @api.model
    def _get_under_validation_exceptions(self):
        res = super()._get_under_validation_exceptions()
        res.extend(["evaluation_result_ids", "work_acceptance_committee_ids"])
        return res

    def _clear_data_committee(self):
        """Clear data work acceptance committee"""
        self.mapped("work_acceptance_committee_ids").write(
            {
                "status": "",
                "note": "",
            }
        )

    def button_draft(self):
        self._clear_data_committee()
        return super().button_draft()
