# -*- coding: utf-8 -*-
{
    'name': "Thai Localization - PromptPay",

    'summary': """
        Use PromptPay QR code with transfer acquirer. 
        """,

    'description': """
        PromptPay is a service for wire transfer in Thailand which uses a mobile phone number or a company ID as a reference. 
        This module provides QR code to display on website payment page, or PDF report. A user can use a Thai bank's mobile application to scan the QR code and pay easily. 
    """,

    'author': "Poonlap V. <poonlap@tanabutr.co.th>",
    'website': "https://github.com/poonlap",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting / Payment',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['payment', 'payment_transfer', 'website_sale'],

    # always loaded
    'data': [
        'data/payment_icon_data.xml',
        'views/payment_transfer_acquirer_form.xml',
        'views/views.xml',
    ],

    'license': "MIT"
}
