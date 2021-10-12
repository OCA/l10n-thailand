from odoo import api, models


class IrSequenceDateRange(models.Model):
    _inherit = "ir.sequence.date_range"

    @api.onchange("date_to", "date_from", "number_next_actual")
    def _compute_preview(self):
        for record in self:
            return super(
                IrSequenceDateRange,
                record.with_context(ir_sequence_date_range_end=record.date_to),
            )._compute_preview()

    def _next(self):
        return super(
            IrSequenceDateRange,
            self.with_context(ir_sequence_date_range_end=self.date_to),
        )._next()
