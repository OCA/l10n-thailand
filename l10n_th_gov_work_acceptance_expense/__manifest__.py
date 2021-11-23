# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Government Work Acceptance for Expense",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Expense",
    "depends": [
        "hr_advance_from_purchase_request",
        "hr_expense_from_purchase_request",
        "hr_expense_work_acceptance",
        "l10n_th_gov_work_acceptance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/expense_views.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["kittiu"],
}
