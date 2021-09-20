# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Thai Localization - Personal Income Tax",
    "version": "14.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization",
    "summary": "Calculate Personnal Income Tax Thailand",
    "depends": ["l10n_th_withholding_tax_cert"],
    "data": [
        "data/pit_rate_data.xml",
        "security/ir.model.access.csv",
        "wizard/create_pit_withholding_tax_cert.xml",
        "views/personal_income_tax_view.xml",
        "views/account_move_view.xml",
        "views/res_partner_view.xml",
        "views/account_payment.xml",
        "views/pit_move_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
