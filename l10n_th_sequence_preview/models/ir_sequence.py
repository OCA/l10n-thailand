from odoo import api, fields, models


class IrSequencePreview(models.Model):
    """
    This sub-class adds a preview field.
    """

    _inherit = "ir.sequence"

    preview = fields.Char("Preview", compute="_compute_preview")

    @api.onchange(
        "prefix",
        "suffix",
        "padding",
        "use_date_range",
        "number_next_actual",
        "implementation",
    )
    def _compute_preview(self):
        if self.use_date_range:
            self.date_range_ids.onchange_sequence_id()
            self.preview = None
        else:
            self.preview = self.get_next_char(self.number_next_actual)
