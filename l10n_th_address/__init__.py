# -*- coding: utf-8 -*-
# © 2017 Ecosoft (ecosoft.co.th).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from . import models
from odoo import api, SUPERUSER_ID


def _update_data_noupdate(cr, registry):
    cr.execute("""
        update ir_model_data
        set noupdate = true
        where model in ('res.country.province',
                        'res.country.district',
                        'res.country.township')
    """)
