import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-l10n-thailand",
    description="Meta package for oca-l10n-thailand Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-l10n_th_partner',
        'odoo13-addon-l10n_th_tax_invoice',
        'odoo13-addon-l10n_th_withholding_tax_cert',
        'odoo13-addon-l10n_th_withholding_tax_cert_form',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
