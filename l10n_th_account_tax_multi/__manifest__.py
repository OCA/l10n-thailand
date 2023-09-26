# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Tax with Payment Multi Deduction",
    "version": "15.0.1.0.1",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": ["l10n_th_account_tax", "account_payment_multi_deduction"],
    "data": ["wizard/account_payment_register_view.xml"],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["kittiu"],
    "auto_install": True,
}
