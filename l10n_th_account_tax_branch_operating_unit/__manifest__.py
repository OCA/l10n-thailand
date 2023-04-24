# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Tax Branch Operating Unit",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": ["l10n_th_account_tax", "account_operating_unit"],
    "data": [
        "security/ir.model.access.csv",
        "views/tax_branch_operating_unit_view.xml",
        "views/operating_unit_view.xml",
        "views/account_move_view.xml",
        "views/account_payment_view.xml",
        "views/withholding_tax_cert.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
