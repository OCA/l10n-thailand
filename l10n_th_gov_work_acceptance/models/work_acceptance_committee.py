# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WorkAcceptanceCommittee(models.Model):
    _name = "work.acceptance.committee"
    _description = "Work Acceptance Committee"

    wa_id = fields.Many2one(
        comodel_name="work.acceptance",
        string="Work Acceptance",
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
    approve_role = fields.Selection(
        selection=[
            ("chairman", "Chairman"),
            ("committee", "Committee"),
        ],
        string="Role",
        required=True,
    )
    status = fields.Selection(
        selection=[
            ("accept", "Accepted"),
            ("not_accept", "No Accepted"),
            ("other", "Other"),
        ],
    )
    note = fields.Text(
        string="Note",
    )
    _sql_constraints = [
        (
            "employee_wa_uniq",
            "unique (employee_id,wa_id)",
            "The employee must be unique per work acceptance !",
        ),
    ]
