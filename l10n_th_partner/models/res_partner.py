# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    branch = fields.Char(string="Tax Branch", help="Branch ID, e.g., 0000, 0001, ...")
    name_company = fields.Char(
        inverse="_inverse_name_company",
        index=True,
        translate=True,
    )
    firstname = fields.Char(translate=True)
    lastname = fields.Char(translate=True)
    name = fields.Char(translate=True)
    display_name = fields.Char(translate=True)

    @api.model
    def create(self, vals):
        """Add inverted company names at creation if unavailable."""
        context = dict(self.env.context)
        name = vals.get("name", context.get("default_name"))
        if vals.get("is_company", False) and name:
            vals["name_company"] = name
        return super().create(vals)

    def _inverse_name_company(self):
        for rec in self:
            if not rec.is_company or not rec.name:
                rec.name_company = False
            else:
                rec.name_company = rec.name

    @api.model
    def _get_computed_name(self, lastname, firstname):
        name = super()._get_computed_name(lastname, firstname)
        title = self.title.name
        if name and title:
            # disable space on title and name
            if self.env.company.no_space_title_name:
                return "".join(p for p in (title, name) if p)
            return " ".join(p for p in (title, name) if p)
        return name

    @api.depends(
        "title", "firstname", "lastname", "name_company", "partner_company_type_id"
    )
    def _compute_name(self):
        for rec in self:
            if not rec.is_company:
                super()._compute_name()
                continue
            prefix, suffix = False, False
            if rec.partner_company_type_id.use_prefix_suffix:
                prefix = rec.partner_company_type_id.prefix
                suffix = rec.partner_company_type_id.suffix
            rec.name = " ".join(p for p in (prefix, rec.name_company, suffix) if p)
            rec._inverse_name()
        return

    @api.onchange("company_type")
    def _onchange_company_type(self):
        if self.company_type == "company":
            self.title = False
        else:
            self.partner_company_type_id = False

    @api.model
    def _install_l10n_th_partner(self):
        records = self.search([("name_company", "=", False)])
        records._inverse_name_company()
        _logger.info("%d partners updated installing module.", len(records))

    def _inverse_name_after_cleaning_whitespace(self):
        """Skip inverse name for case chaging only translation"""
        if not self.env.context.get("skip_inverse_name"):
            super()._inverse_name_after_cleaning_whitespace()
        return
