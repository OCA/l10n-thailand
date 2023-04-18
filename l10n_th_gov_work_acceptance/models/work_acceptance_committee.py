# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
        index=True,
    )
    name = fields.Char(
        string="Committee Name",
        compute="_compute_default_name",
        store=True,
        readonly=False,
        required=True,
        index=True,
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
    note = fields.Text()
    _sql_constraints = [
        (
            "committee_wa_uniq",
            "unique (name, wa_id)",
            "The committee must be unique per work acceptance !",
        ),
    ]

    @api.depends("employee_id")
    def _compute_default_name(self):
        for rec in self:
            rec.name = rec.employee_id.display_name if rec.employee_id else ""

    @api.model
    def _get_under_validation_exceptions(self):
        """Extend for more field exceptions."""
        return ["message_follower_ids", "access_token", "status", "note"]

    def _check_allow_write_under_validation(self, vals):
        """Allow to add exceptions for fields that are allowed to be written
        even when the record is under validation."""
        exceptions = self._get_under_validation_exceptions()
        if any(val not in exceptions for val in vals):
            return False
        return True

    @api.model
    def create(self, vals):
        wa_id = vals.get("wa_id", False)
        if wa_id:
            work_acceptance = self.env["work.acceptance"].browse(wa_id)
            if (
                work_acceptance.state == "draft"
                and work_acceptance.review_ids
                and not work_acceptance.validated
                and not work_acceptance.rejected
                and not self._check_allow_write_under_validation(vals)
            ):
                raise ValidationError(_("The work acceptance is under validation."))
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            if (
                rec.wa_id.state == "draft"
                and rec.wa_id.review_ids
                and not rec.wa_id.validated
                and not rec.wa_id.rejected
                and not rec._check_allow_write_under_validation(vals)
            ):
                raise ValidationError(_("The work acceptance is under validation."))
        return super().write(vals)
