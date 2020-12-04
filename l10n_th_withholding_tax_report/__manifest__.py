# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thailand Localization - Withholding Tax Report",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": [
        "account",
        "report_xlsx_helper",
        "date_range",
        "l10n_th_partner",
        "l10n_th_withholding_tax_cert",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/paper_format.xml",
        "data/report_data.xml",
        "templates/layouts.xml",
        "templates/report_template.xml",
        "report/report_withholding_tax_qweb.xml",
        "wizard/withholding_tax_report_wizard_view.xml",
        "views/menu.xml",
    ],
    "installable": True,
}
