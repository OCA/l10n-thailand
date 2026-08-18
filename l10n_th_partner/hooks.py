# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Update partner company field name_company is equal name"""
    partner_company = env["res.partner"].search(
        [
            ("name_company", "=", False),
            ("is_company", "=", True),
        ]
    )
    for partner in partner_company:
        partner.name_company = partner.name
    _logger.info("partners updated installing module.")
