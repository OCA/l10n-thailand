# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import fields, models


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    buddhist_year = fields.Boolean(
        string="Buddhist Year",
        help="Change year part to buddhist year by, i.e., P2020 -> P2563, P20 -> P63",
    )

    def _get_prefix_suffix(self, date=None, date_range=None):
        self.ensure_one()
        prefix, suffix = super()._get_prefix_suffix(date=date, date_range=date_range)

        def _extract(s):
            res = {}
            result = re.search("%(.*)s", s)
            if result:
                p = result.group(1)
                for t in ["year", "weekday", "doy", "woy", "y"]:
                    if t in p:
                        res.update({t: True})
                        p = p.replace(t, "")
            return res

        def _to_buddhist_year(s, p):
            """ look for the last sequence of number(s) in a string and increment """
            is_year = p.get("year") or p.get("y")
            if is_year:
                i = 543
                numbers = re.compile(r"\d+")
                if numbers.findall(s):
                    lastoccr_sre = list(numbers.finditer(s))[-1]
                    lastoccr = lastoccr_sre.group()
                    lastoccr_incr = str(int(lastoccr) + i)
                    if len(lastoccr) > len(lastoccr_incr):
                        lastoccr_incr = lastoccr_incr.zfill(len(lastoccr))
                    if p.get("y"):
                        lastoccr_incr = lastoccr_incr[-2:]
                    return (
                        s[: lastoccr_sre.start()]
                        + lastoccr_incr
                        + s[lastoccr_sre.end() :]
                    )
            return s

        if prefix and self.buddhist_year:
            prefix = _to_buddhist_year(prefix, _extract(self.prefix))

        if suffix and self.buddhist_year:
            suffix = _to_buddhist_year(suffix, _extract(self.suffix))

        return prefix, suffix
