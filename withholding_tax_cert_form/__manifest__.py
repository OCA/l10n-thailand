# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Withholding Tax Cert Form',
    'category': 'Report',
    'description': """
Reporting
==========================

""",
    'version': '1.0',
    'author': 'Saran Lim.',
    'depends': [
        'account',
        'web',
        'l10n_th_withholding_tax_cert',
    ],
    'data': [
        'data/paper_format.xml',
        'data/report_data.xml',
        'reports/layout.xml',
    ],
}
