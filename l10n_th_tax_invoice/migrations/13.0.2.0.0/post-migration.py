# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _auto_update_field_partner_id(env):
    _logger.info("Auto update new field 'partner_id' on upgrade to 13.0.2.0.0")
    env.cr.execute(
        """
        update account_move_tax_invoice tv set partner_id = (
            select partner_id from account_move_line where id = tv.move_line_id)
        where partner_id is null
    """
    )


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        _auto_update_field_partner_id(env)
