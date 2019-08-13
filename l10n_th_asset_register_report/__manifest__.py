# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Thailand Localization - Asset Register Report',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/l10n-thailand',
    'category': 'Report',
    'depends': [
        'account',
        'account_asset_management',
        'date_range',
        'report_xlsx_helper',
    ],
    'data': [
        'wizard/asset_register_wizard_view.xml',
        'data/paper_format.xml',
        'data/menu_report.xml',
        'report/templates/asset_register.xml',
        'view/report_template.xml',
        'view/report_asset_register.xml',
    ],
    'installable': True,
}
