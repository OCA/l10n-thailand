# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Thai Localization - Tax branch",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "category": "Localization / Accounting",
    "summary": "Add branch in line tax and withholding tax",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "depends": ["l10n_th_account_tax", "account_multi_branch_company"],
    "data": [
        "views/account_move_view.xml",
        "views/account_payment_view.xml",
        "views/withholding_tax_cert.xml",
    ],
    "installable": True,
    "maintainers": ["Saran440"],
}
