# Copyright 2025 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
{
    "name": "Thai Localization - Tax Filing",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": [
        "l10n_th_account_tax",
        "date_range",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/account_tax_filing_security.xml",
        "data/account_tax_filing_data.xml",
        "views/res_config_settings_views.xml",
        "views/account_tax_filing_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440", "Pani-k-folk"],
}
