# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID
from odoo.api import Environment

_logger = logging.getLogger(__name__)


def post_init_hook(cr, _):
    """Update partner company field name_company is equal name"""
    env = Environment(cr, SUPERUSER_ID, {})
    partner_company = env["res.partner"].search(
        [
            ("company_type", "=", "company"),
            ("name_company", "=", False),
        ]
    )
    for partner in partner_company:
        partner.name_company = partner.name
    _logger.info("partners updated installing module.")
