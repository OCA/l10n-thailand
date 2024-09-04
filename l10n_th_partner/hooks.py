# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

def post_init_hook(cr):
    """Update partner company field name_company is equal name"""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        partner_company = env["res.partner"].search([("name_company", "=", False)])
        for partner in partner_company.filtered(lambda l: l.company_type == "company"):
            partner.name_company = partner.name
        _logger.info("partners updated installing module.")
