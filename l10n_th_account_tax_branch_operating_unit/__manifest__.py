# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Thai Localization - Tax branch Operating Unit",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "category": "Localization / Accounting",
    "summary": "Add branch in line tax and withholding tax",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "depends": ["l10n_th_account_tax_branch", "account_operating_unit"],
    "data": [
        "views/res_branch_view.xml",
        "views/operating_unit_view.xml",
        "views/account_move_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
