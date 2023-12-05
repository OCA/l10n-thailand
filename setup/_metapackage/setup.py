import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-thailand",
    description="Meta package for oca-l10n-thailand Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-l10n_th_account_tax>=16.0dev,<16.1dev',
        'odoo-addon-l10n_th_amount_to_text>=16.0dev,<16.1dev',
        'odoo-addon-l10n_th_base_location>=16.0dev,<16.1dev',
        'odoo-addon-l10n_th_fonts>=16.0dev,<16.1dev',
        'odoo-addon-l10n_th_partner>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
