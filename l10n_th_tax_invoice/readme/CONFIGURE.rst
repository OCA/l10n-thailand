For Sales Taxes (tax scope = Sales), there is option to run Tax Invoice number by sequence model.
If set properly, Tax Invoice Number will be using this sequence instead of customer invoice number / payment number

* Goto Accounting > Configuration > Invoicing > Taxes
* For sales tax, choose 'Tax Invoice Sequence' (or create new one)
* Make sure you also set the same sequence for the same tax on payment too.
  I.e., Output VAT7% and Undue Output VAT7% must select the same sequence, both both of them will result in same Tax Report

Note: this option is not avaiable for purchase tax, because the Tax Invoice Number is from vendor, and are filled manually.
