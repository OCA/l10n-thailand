# Copyright 2024 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Account Payment Register Form Netting",
    "version": "16.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": ["l10n_th_account_payment_register_order", "account_payment_netting"],
    "data": [
        "views/account_register_payment_order.xml",
    ],
    "installable": True,
    "auto_install": True,
    "maintainers": ["Saran440"],
}
