*************
Configuration
*************
After installation

* Go to Contacts > Configuration > Import from Geonames.
  Select "Thailand" with "Thai" language, then click the import button.
  This will populate all province names in Thai language and other information.

.. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_tin_service/static/description/geonames.png
    :alt: Import geonames
    :width: 80 %
    :align: center

**********
How to Use
**********
Go to "Contacts" and create a new contact. This module is mainly for TIN (VAT) validation.
It is supposed that you already know a partner's (company) TIN which 13 digits number.
Type the number in "Tax ID" field.

 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_tin_service/static/description/input_tin.png
    :alt: Input Tax Indentification Number, VAT
    :width: 80 %
    :align: center

Press the tab key to move the cursor to another field, or click somewhere outside the "Tax ID" field.
This will activate TIN validation with a web service which provided by Revenue Department of Thailand.
If the TIN is valid, the module will get other information such as, name, address and fill out in the form automatically.

 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_tin_service/static/description/autofill_sample.png
    :alt: Auto-fill result
    :width: 80 %
    :align: center

For a company which has many branches. You can change the branch number which is 5 digits number.
The module will change the address accordingly.

 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_tin_service/static/description/main_branch.png
    :alt: Main branch
    :width: 80 %
    :align: center

 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_tin_service/static/description/another_branch.png
    :alt: Another branch
    :width: 80 %
    :align: center

************
Verification
************
This module verify the TIN and branch number. It the pair is not valid, the module will display a warning message.
Though, a user can still save the record, if needed.

Verify TIN
 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_tin_service/static/description/tin_validation.png
    :alt: Validate TIN
    :width: 80 %
    :align: center

Verify Branch number
 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_tin_service/static/description/branch_validation.png
    :alt: Validate Branch
    :width: 80 %
    :align: center

Validate Branch format
 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_tin_service/static/description/branch_format.png
    :alt: Verify Branch number format
    :width: 80 %
    :align: center
