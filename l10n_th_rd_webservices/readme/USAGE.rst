***********
Preparation
***********
After installation

* Go to Setting > Invoicing 
  Check "Use Thailand Revenue Department web services".
   .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/settings.png
    :alt: Tax Setting
    :width: 80 %
    :align: center

* Go to Contacts > Configuration > Import from Geonames.
  Select "Thailand" and import. This will populate provices and other information.
   .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/geonames.png
    :alt: Import geonames
    :width: 80 %
    :align: center

**********
How to Use
**********
Create a contact. This module is mainly for TIN (VAT) validation. It is supposed that you already know a partner's (company) TIN. 
TIN is 13 digits number. Type the number in "Tax ID" field. 

 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/input_tin.png
    :alt: Input Tax Indentification Number, VAT
    :width: 80 %
    :align: center

Click tab or activate to move the cursor, or click other fields. This will activate TIN validation with a web service which provided by Revenue Department.
If the TIN is valid, the module will quries other information such as, name, address and fill out in the form automatically.

 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/autofill_sample.png
    :alt: Auto-fill result
    :width: 80 %
    :align: center

For a company which has many branches. You can change the branch number which is 5 digits number. The module will change the address accordingly.

 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/main_branch.png
    :alt: Main branch
    :width: 80 %
    :align: center

 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/another_branch.png
    :alt: Another branch
    :width: 80 %
    :align: center

************
Verification
************
Verification of TIN and branch are made, if they are not correct, the module will display a warning message.
Though, a user can still save the recorde, if needed.

Verify TIN
 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/tin_validation.png
    :alt: Validate TIN
    :width: 80 %
    :align: center

Verify Branch number
 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/branch_validation.png
    :alt: Validate Branch
    :width: 80 %
    :align: center

Validate Branch format
 .. figure:: https://raw.githubusercontent.com/OCA/l10n-thailand/13.0/l10n_th_rd_webservices/static/description/branch_format.png
    :alt: Verify Branch number format
    :width: 80 %
    :align: center




