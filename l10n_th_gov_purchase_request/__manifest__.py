# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Government Purchase Request",
    "version": "15.0.2.0.1",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Purchase",
    "depends": [
        "hr",
        "purchase_exception",
        "purchase_request_exception",
        "purchase_request_substate",
        "purchase_request_to_requisition",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/procurement_team.xml",
        "data/purchase_exception.xml",
        "data/purchase_request_exception.xml",
        "data/procurement_type.xml",
        "data/procurement_method.xml",
        "data/purchase_type.xml",
        "data/purchase_request_substate.xml",
        "views/procurement_method_views.xml",
        "views/procurement_type_views.xml",
        "views/purchase_type_views.xml",
        "views/purchase_request_views.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["kittiu"],
}
