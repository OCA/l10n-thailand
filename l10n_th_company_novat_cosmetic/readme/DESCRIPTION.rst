This module add some cosmetic fields in purchase order, in order to
work with l10n_th_company_novat, allowing user to type in price unit in VAT manner
while purchase order line contain no vat at all.

* If a vender is a VAT registered, the cosmetic Vat% will show up with 7%
* User can then, activate the toggle beside Vat%, system will help adding up VAT to price unit,
  and calculate footer cosmatic Tax/Untaxed Amount

Purchase may not really have VAT, but it is now possible to printout form with VAT.
