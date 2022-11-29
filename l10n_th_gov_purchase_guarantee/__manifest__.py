# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Government Purchase Guarantee",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Purchase",
    "depends": [
        "purchase_requisition",
        "account",
    ],
    "data": [
        "data/ir_sequence_data.xml",
        "data/purchase_guarantee_method_data.xml",
        "data/purchase_guarantee_type_data.xml",
        "security/ir.model.access.csv",
        "security/purchase_guarantee_security.xml",
        "views/purchase_guarantee_views.xml",
        "views/purchase_guarantee_method_views.xml",
        "views/purchase_guarantee_type_views.xml",
        "views/purchase_requisition_views.xml",
        "views/purchase_order_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
