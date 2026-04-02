# Copyright 2024 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class BankTemplate(models.Model):
    _name = "bank.template"
    _description = "Bank Template"

    name = fields.Char(
        required=True,
    )
    bank = fields.Selection(
        selection=[],
    )
    line_ending = fields.Selection(
        selection=[
            ("crlf", "\\r\\n (Windows)"),
            ("lf", "\\n (Unix)"),
            ("none", "No line ending"),
        ],
        default="crlf",
        required=True,
    )
    template_line_ids = fields.One2many(
        comodel_name="bank.template.line",
        inverse_name="template_id",
        string="Template Lines",
    )

    def _get_line_ending(self):
        """Return the line ending string based on configuration."""
        self.ensure_one()
        endings = {
            "crlf": "\r\n",
            "lf": "\n",
            "none": "",
        }
        return endings.get(self.line_ending, "\r\n")


class BankTemplateLine(models.Model):
    _name = "bank.template.line"
    _description = "Bank Template Line"
    _order = "sequence, id"

    template_id = fields.Many2one(
        comodel_name="bank.template",
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
    name = fields.Char(string="Description")
    section_id = fields.Many2one(
        comodel_name="bank.template.section",
        index=True,
    )
    # --- Data Source ---
    source_type = fields.Selection(
        selection=[
            ("fixed", "Fixed Value"),
            ("expression", "Python Expression"),
        ],
        default="fixed",
    )
    fixed_value = fields.Char(help="Static text to output.")
    expression = fields.Text(help="Python expression for dynamic value")

    # --- Information ---
    field_length = fields.Integer()
    align = fields.Selection(
        selection=[("ljust", "Left"), ("rjust", "Right")],
        default="ljust",
    )
    padding = fields.Char()

    # Computed position display
    position_from = fields.Integer(
        compute="_compute_position", store=True, string="From"
    )
    position_to = fields.Integer(compute="_compute_position", store=True, string="To")
    condition = fields.Text()

    @api.depends(
        "field_length",
        "sequence",
        "display_type",
        "template_id.template_line_ids.sequence",
        "template_id.template_line_ids.field_length",
        "template_id.template_line_ids.display_type",
    )
    def _compute_position(self):
        templates = self.mapped("template_id")
        for template in templates:
            columns = template.template_line_ids.sorted(lambda r: (r.sequence, r.id))
            current_from = 1
            for col in columns:
                if col.display_type:
                    col.position_from = 0
                    col.position_to = 0
                    current_from = 1
                    continue

                length = col.field_length or 0
                col.position_from = current_from
                col.position_to = current_from + length - 1 if length else current_from
                current_from = col.position_to + 1

    @api.constrains("field_length", "source_type", "fixed_value")
    def _check_field_length(self):
        for rec in self:
            if (
                rec.source_type == "fixed"
                and rec.fixed_value
                and len(rec.fixed_value) > rec.field_length
            ):
                raise UserError(
                    self.env._(
                        f"Value {rec.fixed_value} is longer than "
                        f"length {rec.field_length}"
                    )
                )

    @api.onchange("source_type")
    def onchange_source_type(self):
        if self.source_type == "fixed":
            self.expression = False
        elif self.source_type == "expression":
            self.fixed_value = False

    def _get_value(self, globals_dict):
        if self.source_type == "expression":
            value = safe_eval(self.expression, globals_dict=globals_dict)
        else:
            value = self.fixed_value

        # If value is False, return empty string
        if not value:
            value = ""

        value_str = str(value)
        # Ensure it does not exceed length
        max_length = int(self.field_length)
        if len(value_str) > max_length:
            value_str = value_str[:max_length]

        text_line = getattr(value_str, self.align)(max_length, self.padding or " ")
        return text_line
