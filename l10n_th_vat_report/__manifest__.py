# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Thailand Localization - VAT Reports',
    'version': '12.0.1.0.2',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-thailand',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'depends': [
        'date_range',
        'report_xlsx_helper',
        'l10n_th_partner',
        'l10n_th_vendor_tax_invoice',
    ],
    'data': [
        'data/paper_format.xml',
        'data/report_data.xml',
        'reports/vat_report.xml',
        'wizard/vat_report_wizard_view.xml',
    ],
    'installable': True,
}
