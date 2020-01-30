# Copyright 2019 Trinity Roots Co., Ltd (https://trinityroots.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
{
    "name": "Thai Localization - Address for Thailand",
    "version": "13.0.1.0.0",
    "author": "Trinity Roots,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localisation/Asia",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_zip_view.xml",
        "views/res_province_view.xml",
        "views/res_amphur_view.xml",
        "views/res_tambon_view.xml",
        "views/address_thai_menu.xml",
        "views/res_company_view.xml",
        "views/res_partner_view.xml",
        "data/province_data.xml",
        "data/amphur_data.xml",
        "data/tambon_data.xml",
        "data/zip_data.xml",
    ],
    "installable": True,
    "development_status": "alpha",
    "maintainers": ["Kiattipong"],
}
