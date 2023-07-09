# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Bank Payment Export SCB",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization / Accounting",
    "summary": "Bank Payment Export File SCB",
    "depends": [
        "account_check_payee",
        "l10n_th_bank_payment_export",
        "partner_address_street3",
    ],
    "data": [
        "data/report_action.xml",
        "views/bank_payment_export_view.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
