This module addresses the two main tax requirements in Thailand.

## 1. Tax Invoice (VAT)

The point of tax invoice can occur either on the invoice (VAT) or on the
payment (undue VAT, which becomes VAT on payment).

- Tax invoices are recorded on journal entries and listed in
  Accounting \> Accounting \> Tax Invoices, the source of the Thai VAT
  report.
- The number and date of a purchase tax invoice are filled in from the
  vendor's tax invoice, sales tax invoices are numbered when posting.
- They replace the sales tax invoices of the standard `l10n_th` module,
  which are not created, and its `VAT Registered` option is hidden.

## 2. Withholding Tax and Personal Income Tax

It is built on the standard `l10n_th` and `l10n_account_withholding_tax`
modules, for Thai companies only. The withholding tax is deducted during
the payment, with two kinds of calculation.

1.  Fixed rate of the base amount, e.g., service 3%
2.  Progressive rate of the yearly accumulated income, i.e., personal
    income tax (PIT)

Withholding tax certificates, PND forms and the withholding tax and PIT
reports are provided on top of it.
