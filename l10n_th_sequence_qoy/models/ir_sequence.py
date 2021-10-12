from datetime import datetime

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class IrSequenceQoy(models.Model):
    """
    This inherited-class adds a Budist-Era year
    as legends for prefix and suffix of sequences.
    """
    _inherit = "ir.sequence"

    def _interpolation_dict(self, date=None, date_range=None):
        res = super(IrSequenceQoy, self)._interpolation_dict(
            date=date, date_range=date_range
        )
        res["qoy"] = str((int(res["month"]) - 1) // 3 + 1)
        res["range_qoy"] = str((int(res["range_month"]) - 1) // 3 + 1)
        res["current_qoy"] = str((int(res["current_month"]) - 1) // 3 + 1)

        domain = [
            ("name", "=", "l10n_th_sequence_range_end"),
            ("state", "=", "installed"),
        ]
        if self.env["ir.module.module"].search_count(domain) == 1:
            res["range_end_qoy"] = str((int(res["range_end_month"]) - 1) // 3 + 1) \
                if res["range_end_year"] else None
        return res
