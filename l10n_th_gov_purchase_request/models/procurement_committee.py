# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProcurementCommittee(models.Model):
    _name = "procurement.committee"
    _description = "Procurement Committee"

    request_id = fields.Many2one(
        comodel_name="purchase.request",
        string="Purchase Request",
        ondelete="cascade",
        index=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        ondelete="restrict",
        required=True,
        index=True,
    )
    name = fields.Char(
        related="employee_id.name",
    )
    department_id = fields.Many2one(
        related="employee_id.department_id",
    )
    email = fields.Char(
        related="employee_id.work_email",
    )
    phone = fields.Char(
        related="employee_id.work_phone",
    )
    committee_type = fields.Selection(
        selection=[
            ("procurement", "Procurement Committee"),
            ("work_acceptance", "Work Acceptance Committee"),
        ],
        string="Committee Type",
    )
    approve_role = fields.Selection(
        selection=[
            ("chairman", "Chairman"),
            ("committee", "Committee"),
        ],
        string="Role",
        required=True,
    )
    note = fields.Text(
        string="Note",
    )

    _sql_constraints = [
        (
            "employee_request_uniq",
            "unique (employee_id,request_id)",
            "Committee has to be unique",
        ),
    ]
