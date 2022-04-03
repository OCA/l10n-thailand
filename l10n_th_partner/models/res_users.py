# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def name_get(self):
        """Overwrite name_get for display with title"""
        res = [(rec.id, rec.display_fullname) for rec in self]
        return res

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        """Overwrite name_search for search with title"""
        args = args or []
        domain = []
        if name:
            domain = [("display_fullname", operator, name)]
        return self.search(domain + args, limit=limit).name_get()
