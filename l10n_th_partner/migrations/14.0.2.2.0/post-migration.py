# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _auto_update_field_display_fullname(cr, env):
    _logger.info(
        "Add value 'display_fullname' to 'res_partner' on upgrade to 14.0.2.2.0"
    )
    cr.execute(
        "ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS display_fullname VARCHAR"
    )
    all_partner = env["res.partner"].search([])
    all_partner._compute_display_fullname()
    _logger.info("====== Done: Compute display fullname ======")


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        _auto_update_field_display_fullname(cr, env)
