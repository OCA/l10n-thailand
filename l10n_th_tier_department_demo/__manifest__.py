# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Tier Department Level Demo",
    "version": "18.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization / Tools",
    "depends": [
        "l10n_th_tier_department",
        "hr_expense_advance_clearing",
        "hr_expense_tier_validation",
        "purchase_request_tier_validation",
    ],
    "data": [
        "data/hr_expense_tier_definition.xml",
        "data/purchase_request_tier_definition.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
