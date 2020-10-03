# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Withholding Tax Certificate",
    "version": "13.0.2.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": ["account", "l10n_th_withholding_tax"],
    "data": [
        "security/account_security.xml",
        "security/ir.model.access.csv",
        "wizard/create_withholding_tax_cert.xml",
        "views/withholding_tax_cert.xml",
        "views/account_payment_view.xml",
        "views/account_move_view.xml",
    ],
    "installable": True,
    "development_status": "beta",
    "maintainers": ["kittiu"],
}
