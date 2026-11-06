# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
SUPPORTED_FIELD_TYPES = ("char", "text", "many2one")


class L10nThPartnerRdMapping(models.Model):
    _name = "l10n_th.partner.rd.mapping"
    _description = "Thai RD Partner Field Mapping"
    _order = "sequence, id"
    _rec_name = "field_id"

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Partner Field",
        required=True,
        ondelete="cascade",
        domain=[
            ("model", "=", "res.partner"),
            ("store", "=", True),
            ("readonly", "=", False),
            ("ttype", "in", SUPPORTED_FIELD_TYPES),
        ],
    )
    template = fields.Char(
        required=True,
        help="Text written to the partner field. Placeholders such as {house_no} "
        "or {vHouseNumber} are replaced by the Revenue Department data, unknown "
        "or empty ones by nothing; the form lists all placeholders. For a "
        "relational field, the result is searched by name.",
    )

    _field_uniq = models.Constraint(
        "unique(field_id)",
        "A partner field can only be mapped once.",
    )

    @api.constrains("field_id")
    def _check_field_id(self):
        for mapping in self:
            field = mapping.field_id
            if field.model != "res.partner" or field.ttype not in SUPPORTED_FIELD_TYPES:
                raise ValidationError(
                    self.env._(
                        "Field %(field)s cannot be filled from the Revenue "
                        "Department: only text and many2one fields of contacts "
                        "are supported.",
                        field=field.display_name,
                    )
                )

    def _render(self, values):
        """Fill the template placeholders, then collapse the blanks left by
        the empty ones."""
        self.ensure_one()
        text = PLACEHOLDER_RE.sub(lambda m: values.get(m[1]) or "", self.template)
        return " ".join(text.split())

    def _get_partner_value(self, partner, values):
        """Return the value to write on ``partner`` for this mapping."""
        self.ensure_one()
        text = self._render(values)
        field = partner._fields[self.field_id.name]
        if field.type != "many2one":
            return text
        if not text:
            return False
        comodel = partner.env[field.comodel_name]
        domain = [(comodel._rec_name or "display_name", "=", text)]
        if "country_id" in comodel._fields:
            domain.append(("country_id.code", "=", "TH"))
        return comodel.search(domain, limit=1).id
