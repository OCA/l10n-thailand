# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Check SCB Bank",
    "version": "13.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization / Check Printing",
    "summary": "Printing Check(Cheque) SCB Bank",
    "depends": [
        "l10n_th_amount_to_text",
        "account_check_printing_report_base",
        "account_check_date",
    ],
    "data": [
        "data/account_payment_check_report_data.xml",
        "data/report_data.xml",
        "report/report_check_scb_base.xml",
    ],
    "installable": True,
    "development_status": "alpha",
    "maintainers": ["Saran440"],
}
