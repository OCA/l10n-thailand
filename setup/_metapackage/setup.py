import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-thailand",
    description="Meta package for oca-l10n-thailand Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-l10n_th_account_asset_management',
        'odoo14-addon-l10n_th_amount_to_text',
        'odoo14-addon-l10n_th_base_location',
        'odoo14-addon-l10n_th_company_novat',
        'odoo14-addon-l10n_th_expense_tax_invoice',
        'odoo14-addon-l10n_th_expense_withholding_tax',
        'odoo14-addon-l10n_th_fonts',
        'odoo14-addon-l10n_th_gov_purchase_agreement',
        'odoo14-addon-l10n_th_gov_purchase_guarantee',
        'odoo14-addon-l10n_th_gov_purchase_request',
        'odoo14-addon-l10n_th_partner',
        'odoo14-addon-l10n_th_promptpay',
        'odoo14-addon-l10n_th_sequence_be',
        'odoo14-addon-l10n_th_sequence_branch',
        'odoo14-addon-l10n_th_sequence_preview',
        'odoo14-addon-l10n_th_sequence_qoy',
        'odoo14-addon-l10n_th_sequence_range_end',
        'odoo14-addon-l10n_th_sequence_refactored',
        'odoo14-addon-l10n_th_tax_invoice',
        'odoo14-addon-l10n_th_tax_report',
        'odoo14-addon-l10n_th_withholding_tax',
        'odoo14-addon-l10n_th_withholding_tax_cert',
        'odoo14-addon-l10n_th_withholding_tax_cert_form',
        'odoo14-addon-l10n_th_withholding_tax_report',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
