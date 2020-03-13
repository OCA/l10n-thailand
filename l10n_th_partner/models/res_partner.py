# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    branch = fields.Char(string="Tax Branch", help="Branch ID, e.g., 0000, 0001, ...")
    company_name = fields.Char(
        string="Company name", inverse="_inverse_company_name", index=True
    )

    def _inverse_company_name(self):
        for rec in self:
            if not rec.is_company or not rec.name:
                rec.company_name = False
            else:
                rec.company_name = rec.name

    @api.model
    def _get_computed_name(self, lastname, firstname):
        name = super()._get_computed_name(lastname, firstname)
        title = self.title.name
        if name and title:
            return " ".join(p for p in (title, name) if p)
        return name

    @api.depends(
        "title", "firstname", "lastname", "company_name", "partner_company_type_id"
    )
    def _compute_name(self):
        for rec in self:
            if not rec.is_company:
                super()._compute_name()
                continue
            prefix = rec.partner_company_type_id.prefix
            suffix = rec.partner_company_type_id.suffix
            rec.name = " ".join(p for p in (prefix, rec.company_name, suffix) if p)
            rec._inverse_name()

    @api.onchange("company_type")
    def _onchange_company_type(self):
        if self.company_type == "company":
            self.title = False
        else:
            self.partner_company_type_id = False

    @api.model
    def _install_l10n_th_partner(self):
        records = self.search([("company_name", "=", False)])
        records._inverse_company_name()
        _logger.info("%d partners updated installing module.", len(records))
