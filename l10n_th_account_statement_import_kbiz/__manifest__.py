{
    'name': 'Import Kasikorn KBiz Bank Statement',
    'category': 'Banking addons',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Ross Golder, Odoo Community Association (OCA)',
    'website': "https://www.golder.org",
    'depends': [
        'account_statement_import',
    ],
    'data': [
        'views/view_account_statement_import.xml',
    ],
    'installable': True,
}
