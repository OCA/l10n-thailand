# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Government Purchase Report",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "category": "Localization / Purchase",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "depends": [
        "date_range",
        "report_xlsx_helper",
        "purchase_invoice_plan",
        "purchase_rfq_number",
        "purchase_work_acceptance_invoice_plan",
        "l10n_th_account_tax_expense",
        "l10n_th_gov_hr_expense",
        "l10n_th_gov_purchase_agreement",
        "l10n_th_gov_purchase_guarantee",
        "l10n_th_gov_purchase_request",
        "hr_expense_sequence",
    ],
    "data": [
        "data/report_data.xml",
        "security/ir.model.access.csv",
        "views/purchase_menu.xml",
        "wizard/purchase_report_wizard_view.xml",
        "wizard/non_purchase_report_wizard_view.xml",
        "wizard/purchase_tracking_report_wizard.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
