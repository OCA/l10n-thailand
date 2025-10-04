# Copyright 2017 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Partner Address in Thai",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "depends": ["base_address_extended"],
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "data/res.city.csv",
        "data/res.subdistrict.csv",
        "views/res_partner_view.xml",
        "views/res_city_view.xml",
        "views/res_subdistrict_view.xml",
        "views/res_country_view.xml",
    ],
    "installable": True,
    "maintainers": ["Saran440"],
}
