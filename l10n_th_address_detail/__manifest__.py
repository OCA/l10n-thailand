# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Address Details",
    "summary": "Thai address details (house no., soi, road...), "
    "sub-districts and districts",
    "version": "20.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization",
    "depends": ["base_address_extended", "contacts"],
    "data": [
        "security/ir.access.csv",
        "data/res.city.csv",
        "data/l10n_th.res.city.subdistrict.csv",
        "views/res_city_subdistrict_views.xml",
        "views/res_city_views.xml",
        "views/res_country_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
