# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Base Check",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization",
    "summary": "Printing Check (Cheque)",
    "depends": [
        "account_check_date",
        "account_check_payee",
        "account_check_printing_report_base",
        "l10n_th_amount_to_text",
        "l10n_th_fonts",
    ],
    "data": [
        "data/report_paperformat.xml",
        "data/report_data.xml",
        "report/report_check_base_thailand.xml",
        "views/account_payment_views.xml",
        "wizard/account_payment_register_views.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "/l10n_th_base_check/static/src/scss/style_check_printing.scss",
        ],
    },
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
