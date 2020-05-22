# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _convert_entities_char(self, text):
        """ Hook Convert HTML Entities to characters
            Example : text.replace(b"&quot;", b'"')
        """
        return text

    @api.model
    def render_qweb_text(self, docids, data=None):
        """Delete space"""
        res = super().render_qweb_text(docids, data)
        lst = list(res)
        lst[0] = lst[0].strip()
        lst[0] = self._convert_entities_char(lst[0])
        res = tuple(lst)
        return res
