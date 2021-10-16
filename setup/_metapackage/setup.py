import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-l10n-thailand",
    description="Meta package for oca-l10n-thailand Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-l10n_th_amount_to_text',
        'odoo13-addon-l10n_th_base_location',
        'odoo13-addon-l10n_th_expense_tax_invoice',
        'odoo13-addon-l10n_th_fonts',
        'odoo13-addon-l10n_th_hr_employee_identification_id',
        'odoo13-addon-l10n_th_partner',
        'odoo13-addon-l10n_th_promptpay',
        'odoo13-addon-l10n_th_tax_invoice',
        'odoo13-addon-l10n_th_tax_report',
        'odoo13-addon-l10n_th_withholding_tax',
        'odoo13-addon-l10n_th_withholding_tax_cert',
        'odoo13-addon-l10n_th_withholding_tax_cert_form',
        'odoo13-addon-l10n_th_withholding_tax_multi',
        'odoo13-addon-l10n_th_withholding_tax_report',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
