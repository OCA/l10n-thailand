# Copyright 2026 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Base Location multi language",
    "version": "15.0.1.0.0",
    "category": "Localisation/Asia",
    "license": "AGPL-3",
    "summary": "Add English sub-district, district and state to Thai addresses",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "depends": ["l10n_th_base_location"],
    "data": [
        "views/res_city_zip_view.xml",
        "views/res_partner_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "maintainers": ["Saran440"],
    "installable": True,
}
