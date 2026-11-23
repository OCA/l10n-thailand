# Copyright 2026 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Bank Payment Export KBank",
    "version": "18.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization / Accounting",
    "summary": "Bank Payment Export File KBANK",
    "depends": ["l10n_th_account_tax", "l10n_th_bank_payment_export"],
    "data": [
        "data/bank.template.csv",
        "data/bank.template.section.csv",
        "data/bank.template.line.csv",
        "views/bank_template_view.xml",
        "views/res_partner_views.xml",
        "views/bank_payment_export_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
