# Copyright 2021 Ecosoft Co.,Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Thai Localization - Comapny No-VAT and Purchase Cosmetic VAT",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Purchasing",
    "depends": ["purchase", "l10n_th_company_novat"],
    "data": [
        "views/purchase_view.xml",
        "views/account_move_view.xml",
        "views/hr_expense_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["kittiu"],
}
