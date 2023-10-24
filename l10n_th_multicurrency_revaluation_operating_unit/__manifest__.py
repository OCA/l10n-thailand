# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Custom Currency Revaluation with OU",
    "version": "15.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Localization",
    "summary": "Add Operating Unit to Currency Revaluation",
    "depends": ["operating_unit", "l10n_th_multicurrency_revaluation"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Anut"],
}
