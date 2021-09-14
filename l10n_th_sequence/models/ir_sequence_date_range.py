from odoo import fields, models, api
from odoo.addons.base.models.ir_sequence import _predict_nextval


class IrSequenceDateRangeExt(models.Model):
    _inherit = "ir.sequence.date_range"

    preview = fields.Char("Preview", compute="_compute_preview")

    @api.onchange("date_to", "date_from", "number_next_actual")
    def _compute_preview(self):
        for record in self:
            record.preview = record.with_context(
                ir_sequence_date_range=record.date_from,
                ir_sequence_date_range_end=record.date_to,
            ).sequence_id.get_next_char(record.number_next_actual)

    def onchange_sequence_id(self):
        self._compute_preview()

    def _next(self):
        return super(IrSequenceDateRangeExt, self.with_context(
            ir_sequence_date_range_end=self.date_to
        ))._next()

    def _get_number_next_actual(self):
        """Return number from ir_sequence row when no_gap implementation,
        and number from postgres sequence when standard implementation.
        This override method adds support for onchange's pseudo-record."""
        for seq in self:
            if seq.sequence_id.implementation != 'standard':
                seq.number_next_actual = seq.number_next
            else:
                seq_id = "%03d_%03d" % (seq.sequence_id.ids[0], seq.ids[0])
                seq.number_next_actual = _predict_nextval(self, seq_id)
