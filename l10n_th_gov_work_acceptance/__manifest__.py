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
        "base_tier_validation_formula",
        "base_tier_validation_forward",
        "base_tier_validation_server_action",
        "purchase_work_acceptance_evaluation",
        "purchase_work_acceptance_late_fines",
        "purchase_work_acceptance_tier_validation",
        "l10n_th_gov_purchase_request",
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
