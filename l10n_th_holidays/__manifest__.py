# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Thailand Localization - Holidays',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-thailand',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'depends': [
        'hr_holidays_public',
    ],
    'data': [
        'data/holidays_public.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
    'installable': True,
}
