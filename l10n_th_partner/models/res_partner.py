# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    branch = fields.Char(string="Tax Branch", help="Branch ID, e.g., 0000, 0001, ...")
    firstname = fields.Char(translate=True)
    lastname = fields.Char(translate=True)
    display_fullname = fields.Char(
        compute="_compute_display_fullname",
        store=True,
        translate=True,
    )
    name = fields.Char(translate=True)
    display_name = fields.Char(translate=True)

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

    @api.depends(
        "firstname", "lastname", "title", "partner_company_type_id", "company_type"
    )
    def _compute_display_fullname(self):
        for rec in self:
            # company
            if rec.company_type == "company":
                prefix, suffix = False, False
                if rec.partner_company_type_id.use_prefix_suffix:
                    prefix = rec.partner_company_type_id.prefix
                    suffix = rec.partner_company_type_id.suffix
                rec.display_fullname = " ".join(
                    p for p in (prefix, rec.name, suffix) if p
                )
                continue
            # individual
            no_space_title = self.env.company.no_space_title_name
            rec.display_fullname = (
                rec.title
                and "{}".format(not no_space_title and " " or "").join(
                    [rec.title.name or "", rec.name]
                )
                or rec.name
            )

    @api.onchange("company_type")
    def _onchange_company_type(self):
        if self.company_type == "company":
            self.title = False
        else:
            self.partner_company_type_id = False

    def _inverse_name_after_cleaning_whitespace(self):
        """Skip inverse name for case chaging only translation"""
        if not self.env.context.get("skip_inverse_name"):
            super()._inverse_name_after_cleaning_whitespace()
