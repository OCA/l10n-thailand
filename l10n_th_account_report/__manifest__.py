# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{

    'name': 'Thailand Localization - Accounting Reports',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-thailand',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'depends': ['excel_import_export',
                'date_range',
                'l10n_th_partner',
                'l10n_th_vendor_tax_invoice',
                'l10n_th_withholding_tax_cert',
                ],
    'data': ['security/ir.model.access.csv',
             'views/menuitems.xml',
             'report_vat/report_vat.xml',
             'report_vat/templates.xml',
             'report_pnd/report_pnd.xml',
             'report_pnd/templates.xml',
             ],
    'installable': True,
    'development_status': 'alpha',
    'maintainers': ['kittiu'],
 }
