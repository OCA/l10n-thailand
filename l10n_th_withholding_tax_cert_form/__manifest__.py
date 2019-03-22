# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Thai Localization - Withholding Tax Certificate Form',
    'version': '12.0.1.0.0',
    'author': 'Ecosoft',
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/l10n-thailand/',
    'category': 'Report',
    'depends': ['account',
                'web',
                'l10n_th_withholding_tax_cert',
                ],
    'data': [
        'data/paper_format.xml',
        'data/report_data.xml',
        'reports/layout.xml',
    ],
    'installable': True,
}
