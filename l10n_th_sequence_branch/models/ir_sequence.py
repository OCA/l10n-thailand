# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class IrSequenceBranch(models.Model):
    """
    This inherited-class adds company branch
    as legends for prefix and suffix of sequences.
    """

    _inherit = "ir.sequence"

    def _interpolation_dict(self, date=None, date_range=None):
        res = super(IrSequenceBranch, self)._interpolation_dict(
            date=date, date_range=date_range
        )
        branch = self.company_id.branch.zfill(5) if self.company_id.branch else "00000"
        res["b5"] = branch
        res["b4"] = branch[-4:]
        res["b3"] = branch[-3:]
        res["b2"] = branch[-2:]
        res["b1"] = branch[-1:]
        return res
