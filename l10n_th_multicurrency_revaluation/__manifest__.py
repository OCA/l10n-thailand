# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Multicurrency Revaluation",
    "version": "15.0.1.0.1",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization",
    "summary": "Manage revaluation for multicurrency environment for Thai",
    "depends": ["account", "report_xlsx_helper"],
    "data": [
        "views/res_config_view.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/account_view.xml",
        "views/account_move_line_views.xml",
        "views/account_move_views.xml",
        "wizard/print_currency_unrealized_report_view.xml",
        "wizard/wizard_currency_revaluation_view.xml",
        "wizard/wizard_reverse_currency_revaluation_view.xml",
        "report/report.xml",
        "report/unrealized_currency_gain_loss.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "l10n_th_multicurrency_revaluation/static/src/scss/reports.scss",
        ],
    },
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
