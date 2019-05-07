With this, 2 new tax related fields will be introduced in account.move.line

1. tax_invoice : Tax Invoice Number
2. tax_date : Tax Invoice Date

In customer invoice, both field will be defaulted by Odoo's document number and date.
But in supplier invoice, both field must be filled by user with tax invoice number and date from vendor.

Note: These 2 fields will be also be used in Thai VAT report, with the intention that every report should be coded out of account.move.line

**Preparing Undue Tax**

- Use Developer Mode
- In Chart of Account, add new account for Undue Tax, if not already exists.
- As admin, add access rights ``Show Full Accounting Features``
- Go to Invoicing > Configuration > Settings and select ``Cash Basis``, this will open cash basis options in Tax master data
- Go to Invoicing > Configuration > Accounting > Taxes, create new undue tax for both sales and purchase

**Case Customer Invoice and Payment**

As mentioned earlier, customer side operation do not affected by this module.
But we should still now see the new ``Tax Invoice Number`` and ``Tax Date`` field in account.move.line

- Create new customer invoice and choose to use sales' VAT or Undue VAT
- Process invoice and payment as per normal, Odoo document number and date should be used as Tax Invoice Number/Date
- To check Tax Invoice Number and Date in relevant journal items, go to Invoicing > Accounting > Journal Items, then click to expand

**Case Supplier Invoice/Payment**

**1) Case Input VAT**

- Create new vendor bill and choose Input VAT
- At vendor bill's tax table, fill in 2 new fields, ``Tax Invoice`` and ``Tax Date`` given by your vendor
- Validate this vendor bill, the given Tax Invoice Number and Tax Date should be used in account.move.line
- To check Tax Invoice Number and Date in relevant journal items, go to Invoicing > Accounting > Journal Items, then click to expand

**2) Case Undue Input VAT**

- Create new vendor bill and choose Undue Input VAT
- Validate vendor bill, journal entry will be created with Undue VAT
- Register payment as per normal, this will create new payment document as per normal
- From this process, the journal entry (cash basis) for clear undue is created, but it will be in state **Draft**
- Go to payment document, ​select ``Key-in tax invoice number/date from supplier``, and fill in Tax Invoice Number and Tax Date
- Click on Clear VAT button, the journal entry (cash basis) for clear undue will now be **Posted**
- To check Tax Invoice Number and Date in relevant journal items, go to Invoicing > Accounting > Journal Items, then click to expand
