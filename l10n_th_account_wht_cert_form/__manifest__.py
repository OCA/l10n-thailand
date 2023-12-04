# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Withholding Tax Certificate Form",
    "version": "16.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Report",
    "depends": [
        "l10n_th_account_tax",
        "l10n_th_amount_to_text",
        "l10n_th_fonts",
    ],
    "data": [
        "data/paper_format.xml",
        "reports/withholding_tax_cert_form_view.xml",
        "data/mail_template.xml",
        "data/withholding_tax_cert_data.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "l10n_th_account_wht_cert_form/static/src/scss/style_report.scss",
        ],
    },
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["Saran440"],
}
