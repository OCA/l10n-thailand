Tax Invoice
===========

With this, 2 new tax related fields will be introduced in account.move.tax.invoice

1. tax_invoice_number : Tax Invoice Number
2. tax_invoice_date : Tax Invoice Date

In customer invoice, both field will be defaulted by Odoo's document number and date.
But in supplier invoice, both field must be filled by user with tax invoice number and date from vendor.

Note: The new table account.move.tax.invoice is the main source of Thai VAT Report

**Case Customer Invoice and Payment**

- Create new customer invoice and choose to use sales' VAT or Undue VAT
- Process invoice and payment as per normal, Odoo document number and date should be used as Tax Invoice Number/Date

**Case Supplier Invoice/Payment**

**1) Case Input VAT**

- Create new vendor bill and choose Input VAT
- At vendor bill's tax invoice tab, fill in 2 new fields, ``Tax Invoice`` and ``Tax Date`` given by your vendor
- Validate this vendor bill, the given Tax Invoice Number and Tax Date are set in account.move.tax.invoice

**2) Case Undue Input VAT**

- Create new vendor bill and choose Undue Input VAT
- Validate vendor bill, journal entry will be created with Undue VAT
- Register payment as per normal, this will create new payment document as per normal
- From this process, the journal entry (cash basis) for clear undue is created, but it will be in state **Draft**
- Go to payment document, in tax invoice tab, fill in Tax Invoice Number and Tax Date
- Click on Clear VAT button, the journal entry (cash basis) for clear undue will now be **Posted**

Withholding Tax
===============

From bills / invoices that require withheld tax,

- Create invoice and Fill withholding tax in Field WT at Invoice Lines tab.
- Post > Register Payment.
- System will auto computed amount include withholding tax.

**Note**

- if you configured withholding tax on product, it fill withholding tax in field WT automatic.
- for invoices with withholding tax,

    - you can't make payment to multiple invoices belongs to multiple partners.
    - you can only make payment to multiple invoices belongs to the same partner (using Group Payments).
