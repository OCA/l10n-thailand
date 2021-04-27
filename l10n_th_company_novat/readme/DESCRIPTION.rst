This module allow setting No VAT Registered Entity on both company and partner (vendor/customer)

1. Ensure taxes not allowed on all documents (expense, sale, purchase, invoice)
2. Although there are no taxes incurred anywhere, system can still calculate Withholding Tax amount by vat and non-vat.

For example, given the following setup,

**Company = No-VAT = True, Vendor = No-VAT = True**

This means, the vendor is selling product/service with no VAT at 107.0 = (base amount 107.0 + tax amount 0.0)

* The company create Purchase Order and Invoice with **no vat** at 107.0
* On Inovice line, the new Vat% is 0.0, which imply 107.0 as base amount to withhold tax = 1.07

**Company = No-VAT = True, Vendor = No-VAT = False**

This means, the vendor is selling product/service with VAT 107.0 = (base amount 100.0 + tax amount 7.0)

* But, the company still create Purchase Order and Invoice with **no vat** at 107.0
* On Inovice line, the new **Vat% is 7.0**, which **help imply 100.0 as base amount** to withhold tax = 1.0
