{
    'name': 'Thailand Localization - VAT Reports',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-thailand',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'depends': [
        'account',
        'report_xlsx',
        'date_range',
        'l10n_th_partner',
        'l10n_th_vendor_tax_invoice',
        'l10n_th_withholding_tax_cert',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/paper_format.xml',
        'data/report_data.xml',
        'wizard/report_vat.xml',
        'report/vat_report.xml',
    ],
    'installable': True,
}
