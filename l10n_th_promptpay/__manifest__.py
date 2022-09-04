# Copyright 2020 Poonlap V.
# Licensed AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Thai Localization - PromptPay",
    "version": "15.0.1.0.0",
    "author": "Poonlap V.,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-thailand",
    "license": "AGPL-3",
    "category": "Accounting / Payment",
    "summary": "Use PromptPay QR code with transfer acquirer.",
    "depends": ["payment_transfer", "website_sale"],
    "data": [
        "data/payment_icon_data.xml",
        "views/payment_transfer_acquirer_form.xml",
        "views/payment_views.xml",
    ],
    "external_dependencies": {"python": ["promptpay"]},
    "installable": True,
    "application": False,
    "development_statue": "Alpha",
}
