# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Report Thai tax branch",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "category": "Localization / Accounting",
    "summary": "Filter report thai tax with branch",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "depends": ["l10n_th_account_tax_report", "l10n_th_account_tax_branch"],
    "data": [
        "reports/tax_report.xml",
        "reports/tax_report_rd.xml",
        "reports/report_wht_qweb.xml",
        "reports/report_wht_qweb_rd.xml",
        "wizard/tax_report_wizard_view.xml",
        "wizard/withholding_tax_report_wizard_view.xml",
    ],
    "installable": True,
    "maintainers": ["Saran440"],
}
