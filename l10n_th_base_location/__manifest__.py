# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Base Location",
    "version": "18.0.1.0.0",
    "category": "Localisation/Asia",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "depends": ["base_location_geonames_import", "base_address_extended"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_config_parameter.xml",
        "views/res_partner_view.xml",
        "views/res_company_view.xml",
        "views/res_city_view.xml",
        "views/res_subdistrict_view.xml",
        "views/res_country_view.xml",
        "views/res_city_zip_view.xml",
        "wizard/geonames_import_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "maintainers": ["Saran440"],
    "installable": True,
}
