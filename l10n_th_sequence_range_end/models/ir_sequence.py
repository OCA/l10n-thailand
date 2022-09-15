# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class IrSequence(models.Model):
    """
    This sub-class adds support for range_end legends
    for prefix and suffix of sequences.
    """

    _inherit = "ir.sequence"

    def _interpolation_dict(self, date=None, date_range=None):
        res = super(IrSequence, self)._interpolation_dict(
            date=date, date_range=date_range
        )
        range_end_date = fields.Datetime.from_string(
            self._context.get("ir_sequence_date_range_end")
        )
        sequences = {
            "year": "%Y",
            "month": "%m",
            "day": "%d",
            "y": "%y",
            "doy": "%j",
            "woy": "%W",
            "weekday": "%w",
            "h24": "%H",
            "h12": "%I",
            "min": "%M",
            "sec": "%S",
        }
        for key, fmt in sequences.items():
            res["range_end_" + key] = (
                range_end_date.strftime(fmt) if range_end_date else None
            )

        return res
