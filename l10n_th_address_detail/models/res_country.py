# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .res_partner import L10N_TH_ADDRESS_DETAILS

# Supported formatting: %(field)s placeholders and %% for a percent sign
STREET_FORMAT_PLACEHOLDER = re.compile(r"%\((\w+)\)s")
STREET_FORMAT_SPECIFIER = re.compile(r"%\(\w+\)s|%%")


class ResCountry(models.Model):
    _inherit = "res.country"

    l10n_th_street_format = fields.Text(
        string="Thai Street Format",
        help="Layout of Street (first line) and Street 2 (second line), "
        "generated from the Thai address details of the contacts. Available "
        "placeholders: "
        + ", ".join(f"%({fname})s" for fname in L10N_TH_ADDRESS_DETAILS)
        + ". A detail missing from the layout is not shown in the street lines.",
    )

    @api.constrains("l10n_th_street_format")
    def _check_l10n_th_street_format(self):
        for country in self.filtered("l10n_th_street_format"):
            street_format = country.l10n_th_street_format
            fnames = set(STREET_FORMAT_PLACEHOLDER.findall(street_format))
            leftover = STREET_FORMAT_SPECIFIER.sub("", street_format)
            if fnames - set(L10N_TH_ADDRESS_DETAILS) or "%" in leftover:
                raise ValidationError(
                    self.env._("The Thai street format contains an invalid key.")
                )
            if len([line for line in street_format.splitlines() if line.strip()]) > 2:
                raise ValidationError(
                    self.env._(
                        "The Thai street format has at most two lines: "
                        "Street and Street 2."
                    )
                )

    def write(self, vals):
        country_th = self.env.ref("base.th")
        street_format = country_th.l10n_th_street_format
        res = super().write(vals)
        if country_th in self and country_th.l10n_th_street_format != street_format:
            self.env["res.partner"]._l10n_th_update_street_lines()
        return res
