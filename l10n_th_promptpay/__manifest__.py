# Copyright 2020 Poonlap V.
# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Thai Localization - PromptPay",
    "version": "18.0.1.0.0",
    "author": "Poonlap V., Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization / Accounting",
    "summary": "Use PromptPay QR code with transfer acquirer.",
    "depends": ["account", "account_qr_code_emv"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/promptpay_qr_wizard_views.xml",
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
    "development_statue": "Alpha",
    "maintainers": ["Saran440"],
}
