# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools.misc import get_lang


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_tax_report_branch(self):
        """Branch code on the Thai tax reports: the 5 digits branch code of a
        juristic person, 00000 for its head office, none for an individual"""
        if not self.is_company:
            return False
        return self._get_additional_identifier("TH_BRANCH_CODE") or "00000"

    def _get_tax_report_title(self):
        """Title of an individual on the Thai tax reports, in Thai if installed"""
        if self.is_company or not self.l10n_th_title:
            return False
        env = self.with_context(lang=get_lang(self.env, "th_TH").code).env
        titles = dict(self._fields["l10n_th_title"]._description_selection(env))
        return titles[self.l10n_th_title]
