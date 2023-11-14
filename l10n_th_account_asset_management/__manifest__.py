# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Assets Management",
    "version": "15.0.2.2.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": [
        "account_asset_number",
        "account_asset_transfer",
        "web_tree_image_tooltip",
    ],
    "data": [
        "data/account_asset_parent_data.xml",
        "data/account_asset_sub_state_data.xml",
        "security/ir.model.access.csv",
        "views/account_asset_parent_views.xml",
        "views/account_asset_sub_state_views.xml",
        "views/account_asset_views.xml",
        "wizard/account_asset_remove.xml",
        "wizard/account_asset_transfer.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
