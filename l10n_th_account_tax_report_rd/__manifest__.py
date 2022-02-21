# Copyright 2022 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Thailand Localization - VAT and Withholding Tax Reports with RD Format",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": [
        "l10n_th_fonts",
        "l10n_th_account_tax_report",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/paper_format.xml",
        "data/report_data.xml",
        "reports/rd_tax_report.xml",
        "reports/report_rd_withholding_tax_qweb.xml",
        "wizard/rd_tax_report_wizard_view.xml",
        "wizard/rd_withholding_tax_report_wizard_view.xml",
    ],
    "installable": True,
    "maintainers": ["ps-tubtim"],
    "development_status": "Alpha",
}
