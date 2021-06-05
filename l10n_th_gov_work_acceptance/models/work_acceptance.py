# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class WorkAcceptance(models.Model):
    _inherit = "work.acceptance"

    work_acceptance_committee_ids = fields.One2many(
        comodel_name="work.acceptance.committee",
        inverse_name="wa_id",
        string="Work Acceptance Committees",
        copy=True,
    )

    def _prepare_committee_line(self, line):
        return {
            "employee_id": line.employee_id.id,
            "approve_role": line.approve_role,
            "note": line.note,
        }

    @api.onchange("sheet_id")
    def _onchange_sheet_id(self):
        """ Get WA committee from PR's """
        super()._onchange_sheet_id()
        if self.env.context.get("default_purchase_id"):
            return
        purchase_requests = (
            self.sheet_id.purchase_request_id
            + self.sheet_id.advance_sheet_id.purchase_request_id
        )
        committees = purchase_requests.mapped("work_acceptance_committee_ids")
        lines = [(0, 0, self._prepare_committee_line(line)) for line in committees]
        committee_lines = committee_lines = [(5, 0, 0)]
        for line in lines:
            if line not in committee_lines:
                committee_lines.append(line)
        self.work_acceptance_committee_ids = committee_lines
