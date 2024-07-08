# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Thai Localization - Government Expense",
    "version": "15.0.1.2.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Human Resources",
    "depends": [
        "hr_expense_advance_clearing",
        "hr_expense_advance_overdue_reminder",
        "l10n_th_gov_purchase_request",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/hr_expense_views.xml",
        "views/purchase_request_views.xml",
        "views/reminder_definition_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ps-tubtim"],
}
