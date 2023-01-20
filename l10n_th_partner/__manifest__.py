# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Partner",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization/Asia",
    "depends": ["partner_company_type", "partner_firstname", "hr"],
    "data": [
        "data/res.partner.company.type.csv",
        "data/res.partner.title.csv",
        "views/res_company_view.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_company_type_view.xml",
        "views/res_partner_view.xml",
        "views/res_users_view.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "post_init_hook": "post_init_hook",
    "maintainers": ["kittiu"],
}
