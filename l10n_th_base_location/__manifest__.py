# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Base Location",
    "version": "15.0.1.0.0",
    "category": "Localisation/Asia",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "depends": ["base_location_geonames_import"],
    "data": ["views/res_city_zip_view.xml", "wizard/geonames_import_view.xml"],
    "installable": True,
}
