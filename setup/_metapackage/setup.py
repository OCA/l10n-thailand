import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-l10n-thailand",
    description="Meta package for oca-l10n-thailand Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-account_create_tax_cash_basis_entry_hook',
        'odoo12-addon-l10n_th_partner',
        'odoo12-addon-l10n_th_vendor_tax_invoice',
        'odoo12-addon-l10n_th_withholding_tax_cert',
        'odoo12-addon-l10n_th_withholding_tax_cert_form',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
