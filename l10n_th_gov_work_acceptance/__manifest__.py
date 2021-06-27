# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Government Work Acceptance",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Purchase",
    "depends": [
        "hr",
        "purchase_work_acceptance",
        "purchase_work_acceptance_evaluation",
        "purchase_work_acceptance_late_fines",
        "hr_expense_work_acceptance",
        "hr_expense_from_purchase_request",
        "hr_expense_advance_clearing",
        "l10n_th_gov_purchase_request",
        "purchase_work_acceptance_tier_validation",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/evaluation_data.xml",
        "data/server_action.xml",
        "data/tier.definition.csv",
        "views/work_acceptance_views.xml",
        "views/purchase_views.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["kittiu"],
}
