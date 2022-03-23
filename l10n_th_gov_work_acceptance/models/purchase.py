# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    wa_tier_validation = fields.Boolean(
        string="Paperless WA",
        help="If checked, WA created will be approved by committee by tier valiation."
        "Each committee will be notified (by email or inbox) to approve WA.\n"
        "If not checked, WA will be approved by paper outside Odoo, "
        "and the result of WA will be filled in by procurement officer",
    )

    def _prepare_committee_line(self, line):
        return {
            "employee_id": line.employee_id.id,
            "approve_role": line.approve_role,
            "note": line.note,
        }

    def _get_committee_line(self, purchase_requests):
        committees = purchase_requests.mapped("work_acceptance_committee_ids")
        lines = [(0, 0, self._prepare_committee_line(line)) for line in committees]
        return lines

    def action_view_wa(self):
        result = super().action_view_wa()
        purchase_requests = self.order_line.mapped("purchase_request_lines.request_id")
        lines = self._get_committee_line(purchase_requests)
        committee_lines = []
        for line in lines:
            if line not in committee_lines:
                committee_lines.append(line)
        result["context"]["default_work_acceptance_committee_ids"] = committee_lines
        result["context"]["default_wa_tier_validation"] = self.wa_tier_validation
        return result
