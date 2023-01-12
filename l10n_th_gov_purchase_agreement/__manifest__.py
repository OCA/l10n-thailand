# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Government Purchase Agreement",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Purchase",
    "depends": [
        "purchase",
        "purchase_requisition",
        "purchase_invoice_plan",
        "agreement_legal",
    ],
    "data": [
        "views/purchase_views.xml",
        "views/purchase_requisition_views.xml",
        "views/agreement_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["newtratip"],
}
