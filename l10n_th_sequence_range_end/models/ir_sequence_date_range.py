from odoo import api, models


class IrSequenceDateRange(models.Model):
    _inherit = "ir.sequence.date_range"

    def _next(self):
        return super(
            IrSequenceDateRange,
            self.with_context(ir_sequence_date_range_end=self.date_to),
        )._next()
