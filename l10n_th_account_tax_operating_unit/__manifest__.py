# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - VAT and Withholding Tax Operating Unit",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": ["l10n_th_account_tax", "account_operating_unit"],
    "data": [
        "security/security.xml",
        "views/account_move_tax_invoice_views.xml",
        "views/withholding_tax_cert_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
