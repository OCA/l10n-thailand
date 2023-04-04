# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Government Assets Management",
    "version": "15.0.2.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization / Accounting",
    "depends": [
        "account_asset_low_value",
        "l10n_th_account_asset_management",
        "purchase_work_acceptance",
    ],
    "data": [
        "data/ir_actions_server_data.xml",
        "views/account_asset_views.xml",
        "wizard/account_asset_remove.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
