# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID
from datetime import datetime


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    old_holidays = env['hr.holidays.public'].search(
        [('year', '=', datetime.now().year)], limit=1)
    old_holidays.unlink()
