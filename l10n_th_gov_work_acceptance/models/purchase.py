# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_committee_line(self, line):
        return {
            "employee_id": line.employee_id.id,
            "approve_role": line.approve_role,
            "note": line.note,
        }

    def action_view_wa(self):
        result = super().action_view_wa()
        purchase_requests = self.order_line.mapped("purchase_request_lines.request_id")
        committees = purchase_requests.mapped("work_acceptance_committee_ids")
        lines = [(0, 0, self._prepare_committee_line(line)) for line in committees]
        committee_lines = []
        for line in lines:
            if line not in committee_lines:
                committee_lines.append(line)
        result["context"]["default_work_acceptance_committee_ids"] = committee_lines
        return result
