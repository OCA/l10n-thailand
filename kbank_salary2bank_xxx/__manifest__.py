# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


{'name': 'TH Salary to Bank',
 'version': '11.0.0.0.0',
 'author': 'Ecosoft,Odoo Community Association (OCA)',
 'website': '???',
 'license': 'AGPL-3',
 'category': 'Human Resources',
 'depends': ['hr',
             'excel_import_export'
             ],
 'data': ['security/security.xml',
          'security/ir.model.access.csv',
          'views/kbank_salary_export_view.xml',
          'export_xlsx/actions.xml',
          'export_xlsx/templates.xml',
          ],
 'installable': True,
 'development_status': '???',
 'maintainers': ['kittiu'],
 }
