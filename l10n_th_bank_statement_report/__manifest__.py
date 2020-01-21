# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Thailand Localization - Bank Statement Report',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/l10n-thailand',
    'category': 'Report',
    'depends': [
        'account',
        'date_range',
        'report_xlsx_helper',
    ],
    'data': [
        'wizard/bank_statement_wizard_view.xml',
        'data/paper_format.xml',
        'data/menu_report.xml',
        'report/templates/bank_statement.xml',
        'view/report_template.xml',
        'view/report_bank_statement.xml',
    ],
    'installable': True,
    'maintainers': ['Saran440'],
}
