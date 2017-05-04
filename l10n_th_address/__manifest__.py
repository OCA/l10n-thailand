# -*- coding: utf-8 -*-
# © 2017 Ecosoft (ecosoft.co.th).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Partner Address in Thai',
    'version': '10.0.0.1.0',
    'category': 'Hidden',
    'description': """

Address for Thailand
====================

If country is selected as Thailand, new fields will show up.

* Province (Chanwat)
* District (Amphoe)
* Township (Tambon)

Choosing Township will realize Province, District, and Zip Code

    """,
    'author': 'Ecosoft',
    'website': 'www.ecosoft.co.th',
    'depends': ['sales_team'],
    'data': [
        'views/res_country_view.xml',
        'views/res_partner_view.xml',
        'security/ir.model.access.csv',
        'data/res.country.province.csv',
        'data/res.country.district.csv',
        'data/res.country.township.csv',
    ],
    'installable': True,
    'auto_install': False,
    'post_init_hook': '_update_data_noupdate',
}
