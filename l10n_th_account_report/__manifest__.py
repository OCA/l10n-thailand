# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


{'name': 'TH Accounting Reports',
 'version': '12.0.1.0.0',
 'author': 'Ecosoft,Odoo Community Association (OCA)',
 'website': '???',
 'license': 'AGPL-3',
 'category': 'Accounting',
 'depends': ['l10n_th_partner',
             'l10n_th_vendor_tax_invoice',
             'excel_import_export',
             'date_range',
             ],
 'data': ['security/ir.model.access.csv',
          'views/menuitems.xml',
          'report_vat/report_vat.xml',
          'report_vat/templates.xml',
          ],
 'installable': True,
 'development_status': '???',
 'maintainers': ['kittiu'],
 }
