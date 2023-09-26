# Copyright 2023 Ecosoft Co., Ltd. (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Purchase Guarantee Sequence Option",
    "summary": "Manage sequence options for purchase.guarantee",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Purchase",
    "depends": [
        "base_sequence_option",
        "l10n_th_gov_purchase_guarantee",
    ],
    "data": ["data/purchase_guarantee_sequence_option.xml"],
    "demo": ["demo/purchase_guarantee_demo_options.xml"],
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
    "installable": True,
}
