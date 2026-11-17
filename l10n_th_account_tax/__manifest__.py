# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - VAT and Withholding Tax",
    "version": "20.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": ["l10n_th", "l10n_account_withholding_tax"],
    "data": [
        "data/account_tax_tags_data.xml",
        "data/pit_rate_data.xml",
        "data/withholding_tax_cert_data.xml",
        "data/withholding_tax_type_income_data.xml",
        "security/ir.access.csv",
        "wizard/account_move_reversal_view.xml",
        "wizard/clear_tax_view.xml",
        "views/res_config_settings_views.xml",
        "views/account_tax_view.xml",
        "views/account_move_view.xml",
        "views/account_move_tax_invoice_views.xml",
        "views/withholding_tax_cert.xml",
        "views/withholding_tax_code_income.xml",
        "views/account_payment_view.xml",
        "views/personal_income_tax_view.xml",
        "views/res_partner_view.xml",
        "views/res_company_view.xml",
        "views/wht_report_views.xml",
        "report/wht_cert_report.xml",
        "data/mail_template_data.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "l10n_th_account_tax/static/src/scss/wht_cert_report.scss",
        ],
    },
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["kittiu", "Saran440"],
}
