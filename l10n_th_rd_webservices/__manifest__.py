# Copyright 2020 Poonlap V.
# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Thai Localization - RD Web Services",
    "version": "13.0.1.0.0",
    "author": "Poonlap V.,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localisation/Asia",
    "summary": "Verify Tax Identification ID and get partner's information from Revenue Department web services (SOAP).",
    "depends": ["l10n_th_partner"],
    "data": [
        "views/res_partner_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "external_dependencies": {"python": ["zeep"]},
    "installable": True,
    "application": False,
    "development_statue": "Alpha",
}
