## Withholding Tax

**Vendor bills and customer invoices**

- Create the bill or invoice and set the withholding tax in `Taxes` of
  the lines. Only one withholding tax is allowed per line.
- Post it, then click Pay (Register Payment)
- In the payment wizard, select `Withhold` (pay and withhold, or withhold
  only), the withholding lines are proposed from the taxes of the bill.
  Their base and amount can be edited.
- Create the payment. The amounts withheld are recorded on the payment
  with the `WH Base` and `Counterpart` lines.

**Manual journal entries**

Set the withholding tax in `Taxes` of a journal item. The withholding
tax line is computed directly on the entry.

**Withholding tax certificates**

- On a posted payment or journal entry with withholding tax, an alert
  tells that the certificate is not yet created. Click
  `Create withholding tax cert.`
- The certificates are created per partner and PND form. The PND form
  defaults from the PND tax tags of the tax, otherwise from the partner,
  i.e., company: PND53, individual: PND3, and can be edited. The type of
  income defaults from the income tax type of the tax, and the tax payer
  from the withholding condition of the payment. Check the type of
  income and income code, then confirm the certificate.
- Certificates are listed in Accounting \> Vendors \> WHT Certificates.
- Print a done certificate with `Print 50 Tawi`, the standard 50 Tawi
  report of `l10n_th` filled from the certificate. Several certificates
  are downloaded as a ZIP file with Action \> Thailand: Print 50 tawi.
  These replace the standard ones of payments, which are hidden.
- Send the 50 Tawi of a done certificate to the partner with
  `Send by Email`.
- Resetting to draft or cancelling the payment or journal entry also
  cancels its certificates.

**Reports**

Go to Accounting \> Reporting \> Thai Accounting Reports \>
Withholding Tax

## Personal Income Tax (PIT)

- Set the PIT tax in `Taxes` of the bill lines, e.g., for freelancers.
  It is 0% on the bill.
- Click Pay and select `Withhold`. The PIT is computed on the payment
  from the yearly income accumulated by the partner, with the PIT rate
  table of the payment year. The yearly income includes the base of the
  posted payments and journal entries of the partner.
- A certificate can be created from the payment as for any other
  withholding tax.
- Go to Accounting \> Reporting \> Thai Accounting Reports \>
  Personal Income Tax to see the yearly income and the PIT withheld.

## Tax Invoice

The tax invoice is recorded on each journal entry with VAT, in the
`Tax Invoice` tab, and listed in Accounting \> Accounting \>
Tax Invoices. The fields are the tax invoice number and date, and the
number of months of late report.

Note: the table `account.move.tax.invoice` is the main source of the
Thai VAT report.

**Customer Invoice and Payment**

- Create a customer invoice and choose the sales VAT or undue VAT
- Post the invoice and register the payment as usual. The tax invoice is
  numbered when posting, by the tax sequence, or by the invoice or
  payment number (see the configuration).

**Vendor Bill with Input VAT**

- Create a vendor bill and choose the Input VAT
- In the `Tax Invoice` tab, fill in `Tax Invoice` and `Tax Date` given by
  your vendor. They are required before posting.
- Post the vendor bill, the tax invoice keeps the number and date.

**Vendor Bill with Undue Input VAT**

- Create a vendor bill and choose the Undue Input VAT, then post it
- Register the payment as usual
- The cash basis entry that clears the undue VAT is created, but it stays
  in **Draft** until the vendor's tax invoice is filled in
- In the `Tax Invoice` tab of the payment, fill in the Tax Invoice
  Number and Tax Date, then click `Clear Tax`. The cash basis entry is
  **Posted** (or post the entry itself).

Note: when a bill is netted with a refund or a journal entry, Odoo 20 does
not create a cash basis entry.

**Report Late**

A vendor tax invoice dated in an earlier month than the accounting date can
be reported late, up to 6 months. `Report Late` is proposed when the tax
invoice date is filled in, and the report date is then moved to the end of
the later month.

**Split**

In draft, use the `Split` button on a line of the `Tax Invoice` tab to copy
it, when the vendor issues several tax invoices for the same journal item.
Adjust the tax base and tax amount of each one.

**Credit Notes and Reversals**

When reversing a vendor bill or entry, the reversal wizard asks for the
vendor credit note number and date. The tax invoice of the reversal has
a negative base and amount.

**Manual Tax Invoice**

On journal entries, check `Manual Tax Invoice` on a journal item (e.g., a
VAT account line without tax) to create its tax invoice, for example,
for a purchase VAT recorded manually.
