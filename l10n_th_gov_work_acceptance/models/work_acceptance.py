# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class WorkAcceptance(models.Model):
    _inherit = "work.acceptance"
    _tier_validation_manual_config = True  # We need more buttons

    wa_tier_validation = fields.Boolean(
        string="Paperless WA",
        readonly=True,
        states={"draft": [("readonly", False)]},
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
            reviewed = len(rec.work_acceptance_committee_ids.filtered("status"))
            if committees:
                rec.completeness = reviewed / committees * 100
            else:
                rec.completeness = 0

    def _prepare_committee_line(self, line):
        return {
            "employee_id": line.employee_id.id,
            "approve_role": line.approve_role,
            "note": line.note,
        }

    @api.model
    def _get_under_validation_exceptions(self):
        res = super()._get_under_validation_exceptions()
        res.append("evaluation_result_ids")
        return res

    def action_view_evaluation(self):
        self.ensure_one()
        action = self.env.ref(
            "l10n_th_gov_work_acceptance.action_view_wa_evaluation_result"
        )
        result = action.sudo().read()[0]
        # result["domain"] = [("wa_id", "=", self.id)]
        return result
