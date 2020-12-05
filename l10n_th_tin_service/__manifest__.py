# Copyright 2020 Poonlap V.
# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Thai Localization - TIN Service",
    "version": "13.0.1.0.0",
    "author": "Poonlap V.,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localisation/Asia",
    "summary": "Verify Tax ID and get partner's information from web services.",
    "depends": ["l10n_th_partner", "l10n_th_base_location"],
    "data": ["views/res_partner_view.xml"],
    "external_dependencies": {"python": ["zeep"]},
    "installable": True,
    "application": False,
    "development_statue": "Alpha",
    "maintainers": ["poonlap"],
}
