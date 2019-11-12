# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Thai Localization - Withholding Tax Certificate Form",
    "version": "13.0.1.0.0",
    "author": "Ecosoft,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-thailand",
    "category": "Report",
    "depends": ["account", "web", "l10n_th_withholding_tax_cert"],
    "external_dependencies": {"python": ["num2words"]},
    "data": ["data/paper_format.xml", "reports/layout.xml", "data/report_data.xml"],
    "installable": True,
}
