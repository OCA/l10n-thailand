from odoo import models


class IrSequenceBe(models.Model):
    """
    This inherited-class adds a Buddhist-Era year
    as legends for prefix and suffix of sequences.
    """

    _inherit = "ir.sequence"

    def _interpolation_dict(self, date=None, date_range=None):
        res = super(IrSequenceBe, self)._interpolation_dict(
            date=date, date_range=date_range
        )
        res["year_be"] = str(int(res["year"]) + 543)
        res["range_year_be"] = str(int(res["range_year"]) + 543)
        res["current_year_be"] = str(int(res["current_year"]) + 543)
        res["y_be"] = res["year_be"][-2:]
        res["range_y_be"] = res["range_year_be"][-2:]
        res["current_y_be"] = res["current_year_be"][-2:]

        domain = [
            ("name", "=", "l10n_th_sequence_range_end"),
            ("state", "=", "installed"),
        ]
        if self.env["ir.module.module"].search_count(domain) == 1:
            res["range_end_year_be"] = (
                str(int(res["range_end_year"]) + 543) if res["range_end_year"] else None
            )
            res["range_end_y_be"] = (
                res["range_end_year_be"][-2:] if res["range_end_year"] else None
            )
        return res
