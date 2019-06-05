# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    'name': 'Thai Localization - Account Vendor Tax Invoice',
    'version': "12.0.1.1.0",
    'author': 'Ecosoft,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/l10n-thailand/',
    'category': 'Localization / Accounting',
    'depends': ['account',
                'account_create_tax_cash_basis_entry_hook'],
    'data': ['security/ir.model.access.csv',
             'views/account_invoice.xml',
             'views/account_payment_view.xml',
             'views/account_view.xml', ],
    'installable': True,
    'development_status': 'alpha',
    'maintainers': ['kittiu'],
}
