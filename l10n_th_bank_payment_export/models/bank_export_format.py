# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import html
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class BankExportFormat(models.Model):
    _name = "bank.export.format"
    _description = "Bank Export Format"

    name = fields.Char(
        required=True,
    )
    bank = fields.Selection(
        selection=[],
    )
    export_format_ids = fields.One2many(
        comodel_name="bank.export.format.line",
        inverse_name="bank_id",
    )


class BankExportFormatLine(models.Model):
    _name = "bank.export.format.line"
    _description = "Bank Export Format Line"
    _order = "sequence, id"

    bank_id = fields.Many2one(
        comodel_name="bank.export.format",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(
        default=10,
        required=True,
    )
    display_type = fields.Selection(
        [
            ("line_section", "Section"),
            ("line_note", "Note"),
        ],
        default=False,
        help="Technical field for UX purpose.",
    )
    lenght = fields.Integer(
        required=True,
    )
    lenght_from = fields.Integer(compute="_compute_lenght", store=True, string="From")
    lenght_to = fields.Integer(compute="_compute_lenght", store=True, string="To")
    name = fields.Char(string="Description")
    condition_line = fields.Text()
    match_group = fields.Char()
    end_line = fields.Boolean()
    need_loop = fields.Boolean()
    sub_loop = fields.Boolean()
    sub_value_loop = fields.Text()
    value_type = fields.Selection(
        selection=[
            ("fixed", "Fixed"),
            ("dynamic", "Dynamic"),
        ],
        required=True,
        default="fixed",
    )
    value_alignment = fields.Selection(
        selection=[
            ("ljust", "Left Justify"),
            ("rjust", "Right Justify"),
        ],
        string="Alignment",
        required=True,
        default="ljust",
    )
    value_blank_space = fields.Char(
        string="Blank Space",
        help="Blank space for fill in value",
    )
    value = fields.Text()

    @api.depends("lenght", "sequence")
    def _compute_lenght(self):
        for rec in self:
            # Retrieve all records for the given bank_id ordered by sequence
            export_format_lines = self.search(
                [("bank_id", "=", rec.bank_id.id)], order="sequence"
            )
            # Initialize the starting point for lenght_from
            previous_lenght_to = 0
            previous_lenght = 0
            previous_name = False

            # Iterate over the records and calculate lenght_from and lenght_to
            for line in export_format_lines:
                # Description and Lenght is duplicated,
                # so we need to adjust the lenght_from and lenght_to
                if line.name == previous_name and line.lenght == previous_lenght:
                    previous_lenght_to = previous_lenght_to - line.lenght

                line.lenght_from = previous_lenght_to + 1
                line.lenght_to = line.lenght_from + line.lenght - 1
                # Reset the starting point for lenght_from if end_line is True
                if line.end_line:
                    previous_lenght_to = 0
                    # Reset
                    previous_name = False
                else:
                    previous_lenght_to = line.lenght_to
                    previous_lenght = line.lenght
                    previous_name = line.name

    def _get_value(self, globals_dict):
        value = self.value
        if self.value_type == "dynamic" and value:
            value = safe_eval(value, globals_dict=globals_dict)
        # Support for HTML content
        # Credit: https://github.com/OCA/server-tools/tree/16.0/html_text
        if isinstance(value, Markup):
            doc = html.fromstring(value)
            words = " ".join(doc.xpath("//text()")).split()
            value = " ".join(words)
        # If value is False, return empty string
        if not value:
            value = ""
        text_line = getattr(value, self.value_alignment)(
            self.lenght, self.value_blank_space or " "
        )
        return text_line

    @api.constrains("lenght", "value")
    def _check_lenght(self):
        for rec in self:
            if rec.value_type == "fixed" and rec.value and len(rec.value) > rec.lenght:
                raise UserError(
                    _("Value %(value)s is longer than lenght %(lenght)s")
                    % {"value": rec.value, "lenght": rec.lenght}
                )
