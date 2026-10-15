## Withholding Tax

Withholding taxes are standard taxes, there is no specific master data.

- Go to Accounting \> Configuration \> Accounting \> Taxes and create a
  tax with `Is Withholding Tax` checked and a negative rate, e.g., -3%
  for a service
- Set the withholding tax payable account on its tax repartition
- Set the standard `Income Tax Type` of the tax, it is the default type
  of income on the withholding tax certificate
- Optionally, set a PND tax tag on the repartition lines of the tax,
  e.g., `PND53` or `Income PND53`, as the standard 50 Tawi report. It
  is the default PND form of the certificate, otherwise PND53 for
  companies and PND3 for individuals. Tags for PND3 and PND53 are
  standard, this module adds PND1, PND2 and PND3a.

Go to Accounting \> Configuration \> Settings and select the
`Withholding Tax Base` account. It is used by the `WH Base` and
`Counterpart` lines of the payments with withholding tax.

To print the payer signature on the 50 Tawi, go to Accounting \>
Configuration \> Settings \> Thai Localization and check
`50 Tawi - Print Signature`. The name of the user who confirmed the
certificate is printed above the signature line.

The codes of the income types, used on the certificates, are available
in Accounting \> Configuration \> Accounting \> WHT Income Code.

## Personal Income Tax (PIT)

- Go to Accounting \> Configuration \> Accounting \> Taxes and create the
  PIT tax as a withholding tax, then check `Personal Income Tax`. The
  rate is fixed to 0% (the amount is hidden), the amount to withhold is
  computed on the payment. There can be only one PIT tax per company.
- Go to Accounting \> Configuration \> Accounting \> PIT Rate to review
  the rate tables. There is one table per calendar year, the default
  rates in effect since 2017 are provided. Create a new table when the
  rates change.

## Tax Invoices

**Preparing Undue Tax**

- Use Developer Mode
- In Chart of Accounts, add a new account for Undue Tax, if it does not
  already exist.
- As admin, add the access right `Show Full Accounting Features`
- Go to Accounting \> Configuration \> Settings and select `Cash Basis`,
  this will open the cash basis options in the Tax master data
- Go to Accounting \> Configuration \> Accounting \> Taxes, create new
  undue taxes for both sales and purchase

**Sales Tax Invoice Number**

The sales tax invoice is numbered when the entry is posted.

- For sales taxes (tax scope = Sales), choose the `Tax Invoice Sequence`
  (or create a new one) to number the tax invoice by sequence. Set the
  same sequence for the same tax on payment, i.e., Output VAT7% and
  Undue Output VAT7% must select the same sequence, so that both result
  in the same tax report.
- Otherwise, the tax invoice number is the number of the invoice. For
  undue VAT, go to Accounting \> Configuration \> Settings \> Thai
  Localization and select the `Customer Tax Invoice Number`, either the
  payment number or the invoice number.

Note: these options are not available for purchase taxes, because the tax
invoice number is from the vendor and filled in manually.

**Keep Zero Line Taxes**

To keep tax lines with zero amount (such as 0% VAT) in journal entries,
so that they appear in the tax invoices:

- Go to Accounting \> Configuration \> Settings and select
  `Keep Zero Line Taxes`
- Create an invoice or bill and select a tax with 0% rate
- Go to Journal Items, a tax line with zero value is created

Zero withholding tax lines are never kept.
