# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Check KTB",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization",
    "summary": "Printing Check(Cheque) KTB",
    "depends": [
        "account_check_date",
        "account_check_payee",
        "account_check_printing_report_base",
        "l10n_th_amount_to_text",
        "l10n_th_fonts",
    ],
    "data": [
        "data/report_paperformat.xml",
        "report/account_check_writing_report.xml",
        "views/report_check_ktb_base.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "/l10n_th_check_ktb/static/src/scss/style_check_ktb.scss",
        ],
    },
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
