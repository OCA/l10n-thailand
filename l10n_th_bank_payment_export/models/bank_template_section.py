# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankTemplateSection(models.Model):
    _name = "bank.template.section"
    _description = "Bank Template"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "sequence, id"

    name = fields.Char(
        required=True,
    )
    sequence = fields.Integer(
        default=10,
        required=True,
    )
    parent_id = fields.Many2one(
        comodel_name="bank.template.section",
        string="Parent Section",
    )
    child_ids = fields.One2many(
        comodel_name="bank.template.section",
        inverse_name="parent_id",
        string="Child Sections",
    )
    parent_path = fields.Char(index=True)
    data_level = fields.Selection(
        selection=[
            ("document", "Document"),
            ("payment", "Payment"),
            ("invoice", "Invoice"),
            ("wht", "Withholding Tax"),
            ("custom", "Custom Expression"),
        ],
        default="document",
        required=True,
        help="Determines what data the section iterates over.\n"
        "- Document: Rendered once using the export document.\n"
        "- Payment: Rendered once per payment line.\n"
        "- Invoice: Rendered once per invoice per payment.\n"
        "- Withholding Tax: Rendered once per withholding tax per payment.\n"
        "- Custom: Uses a custom Python expression to get iterables.",
    )
