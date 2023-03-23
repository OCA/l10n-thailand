# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Bank Payment Export BBL",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization",
    "summary": "Bank Payment Export File BBL",
    "depends": ["l10n_th_bank_payment_export", "l10n_th_account_tax"],
    "data": [
        "data/report_action.xml",
        "views/res_config_settings_views.xml",
        "views/bank_payment_export_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
