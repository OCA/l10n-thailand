# -*- coding: utf-8 -*-
# © 2017 Ecosoft (ecosoft.co.th).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from . import models
from odoo import api, SUPERUSER_ID


def _update_data_noupdate(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    thailand = env.ref('base.th')
    thailand.sudo().write({
        'address_format': "%(street)s\n%(street2)s\n%(district_name)s "
        "%(township_name)s\n%(province_name)s %(zip)s"
    })
    cr.execute("""
        update ir_model_data
        set noupdate = true
        where model in ('res.country.province',
                        'res.country.district',
                        'res.country.township')
        and module = 'l10n_th_address'
        and noupdate = false
    """)
