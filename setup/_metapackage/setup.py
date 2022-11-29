import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-thailand",
    description="Meta package for oca-l10n-thailand Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-l10n_th_account_tax>=15.0dev,<15.1dev',
        'odoo-addon-l10n_th_amount_to_text>=15.0dev,<15.1dev',
        'odoo-addon-l10n_th_base_location>=15.0dev,<15.1dev',
        'odoo-addon-l10n_th_fonts>=15.0dev,<15.1dev',
        'odoo-addon-l10n_th_partner>=15.0dev,<15.1dev',
        'odoo-addon-l10n_th_promptpay>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
