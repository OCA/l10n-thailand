# -*- coding: utf-8 -*-
# © 2017 Ecosoft (ecosoft.co.th).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Partner Address in Thai',
    'version': '10.0.0.1.0',
    'category': 'Hidden',
    'author': 'Ecosoft,Odoo Community Association (OCA)',
    'website': 'http://ecosoft.co.th',
    'depends': ['sales_team'],
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/res.country.province.csv',
        'data/res.country.district.csv',
        'data/res.country.township.csv',
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
