Tax Invoices
============

**Preparing Undue Tax**

- Use Developer Mode
- In Chart of Account, add new account for Undue Tax, if not already exists.
- As admin, add access rights ``Show Full Accounting Features``
- Go to Invoicing > Configuration > Settings and select ``Cash Basis``, this will open cash basis options in Tax master data
- Go to Invoicing > Configuration > Accounting > Taxes, create new undue tax for both sales and purchase

For Sales Taxes (tax scope = Sales), there is option to run Tax Invoice number by sequence model.
If set properly, Tax Invoice Number will be using this sequence instead of customer invoice number / payment number

* Goto Invoicing > Configuration > Accounting > Taxes
* For sales tax, choose 'Tax Invoice Sequence' (or create new one)
* Make sure you also set the same sequence for the same tax on payment too.
  I.e., Output VAT7% and Undue Output VAT7% must select the same sequence, both of them will result in same Tax Report

Note: this option is not avaiable for purchase tax, because the Tax Invoice Number is from vendor, and are filled manually.

Withholding Tax and Personal Income Tax (PIT)
=============================================

Setup account related to withholding tax will help set default tax amount
when create certificate from payment.

* Go to Invoicing > Configuration > Accounting > Chart of Accounts
* Search for withholding tax related account > Setup
* Check "WHT Account"
* Go to Invoicing > Configuration > Accounting > Withholding Tax
* Create withholding Tax (normal and personal income tax)

**Configured Withholding Tax by Product (optional)**

* Go to Invoicing > Customers or Vendors > Products
* Select product that you need withholding tax
* Add Withholding Tax on General Information Tab (Invoices) / Purchase Tab (Bills)

**Configure Personal Income Tax Rate**

#. Go to Invoicing > Configuration > Accounting > PIT Rate
#. Change range or tax rate (if any)

Configure PIT Withholding Tax as following,

#. Go to Invoicing > Configuration > Accounting > Withholing Tax
#. Create new Withholding Tax for PIT and check Personal Income Tax checkbox
#. PIT Rate that will be used to calculate the withholding amount will be shown
#. You can set default Withholding Tax on the Product's Purchase Tab
