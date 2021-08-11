import pytz
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class IrSequence(models.Model):
    """
    This sub-class is to refactor the ir.sequence by changing
    the inextensible inner function `_interpolation_dict()` to a normal private class function.
    """
    _inherit = "ir.sequence"

    def _interpolation_dict(self):
        now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
        if self._context.get('ir_sequence_date'):
            effective_date = fields.Datetime.from_string(self._context.get('ir_sequence_date'))
        if self._context.get('ir_sequence_date_range'):
            range_date = fields.Datetime.from_string(self._context.get('ir_sequence_date_range'))

        sequences = {
            'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
            'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
        }
        res = {}
        for key, format in sequences.items():
            res[key] = effective_date.strftime(format)
            res['range_' + key] = range_date.strftime(format)
            res['current_' + key] = now.strftime(format)

        return res

    def _get_prefix_suffix(self):
        """
        Override the `_get_prefix_suffix()` to utilize the private `_interpolation_dict()`
        instead of an inner function.
        Note: the date and date_range parameters are dropped,
        because they have never been assigned by the invoking method.
        """
        d = self._interpolation_dict()

        try:
            interpolated_prefix = (self.prefix % d) if self.prefix else ''
            interpolated_suffix = (self.suffix % d) if self.suffix else ''
        except ValueError:
            raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % (self.get('name')))
        return interpolated_prefix, interpolated_suffix


class IrSequenceExt(models.Model):
    """
    This sub-class is to extend the functionality by adding more legend for prefix and suffix of sequences.
    """
    _inherit = "ir.sequence"

    preview = fields.Char("Preview", computed="_compute_preview")

    @api.onchange("prefix", "suffix", "padding", "number_increment", "use_date_range")
    def _compute_preview(self):
        self.preview = self.get_next_char(self.number_next_actual)

    def _interpolation_dict(self):
        res = super(IrSequenceExt, self)._interpolation_dict()
        res.update({
            "year_be": str(int(res["year"]) + 543),
            "range_year_be": str(int(res["range_year"]) + 543),
            "current_year_be": str(int(res["current_year"]) + 543),
        })
        res.update({
            "y_be": res["year_be"][-2:],
            "range_y_be": res["range_year_be"][-2:],
            "current_y_be": res["current_year_be"][-2:],
        })
        res.update({
            "qoy": str((int(res["month"]) - 1) // 3 + 1),
            "range_qoy": str((int(res["range_month"]) - 1) // 3 + 1),
            "current_qoy": str((int(res["current_month"]) - 1) // 3 + 1),
        })
        company_id = self.env.company if len(self.company_id) == 0 else self.company_id
        branch = company_id.branch.zfill(5) \
            if hasattr(company_id, "branch") else "00000"
        res.update({
            "b5": branch,
            "b4": branch[-4:],
            "b3": branch[-3:],
            "b2": branch[-2:],
            "b1": branch[-1:],
        })
        return res
