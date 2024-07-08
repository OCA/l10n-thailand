# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Base Bank Payment Export",
    "version": "16.0.1.0.0",
    "summary": "Base export payment text file to bank",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization / Accounting",
    "depends": ["account", "partner_bank_code", "report_xlsx_helper"],
    "data": [
        "security/ir.model.access.csv",
        "security/bank_payment_export_security.xml",
        "data/bank_payment_export_sequence.xml",
        "data/report_action.xml",
        "data/server_action.xml",
        "templates/report_template.xml",
        "views/bank_payment_template_view.xml",
        "views/account_payment_view.xml",
        "views/bank_payment_export_view.xml",
        "views/res_bank_views.xml",
        "views/partner_view.xml",
        "wizard/account_payment_register_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
