# Copyright 2024 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Partner data from Revenue Department",
    "summary": "Fill partner name and address from the Thai Revenue Department",
    "version": "20.0.1.0.0",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Localization / Accounting",
    "depends": ["web"],
    "data": [
        "security/ir.access.csv",
        "data/ir_config_parameter_data.xml",
        "data/l10n_th_partner_rd_mapping_data.xml",
        "views/l10n_th_partner_rd_mapping_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
