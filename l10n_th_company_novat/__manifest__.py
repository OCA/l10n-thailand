# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Comapny/Partner, VAT/NOVAT setup",
    "version": "14.0.1.0.1",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": [
        "hr_expense",
        "sale",
        "purchase",
        "account",
        "l10n_th_withholding_tax",
    ],
    "data": [
        "views/res_company_view.xml",
        "views/res_partner_view.xml",
        "views/account_move_view.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["kittiu"],
}
