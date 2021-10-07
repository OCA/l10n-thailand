This module now support both withholding tax and personal income tax.

Withholding Tax is tax to be withhold when register payment. Withholding tax is calculated by percent.

Personal Income Tax is just another type of Withholding Tax, with some difference,

1. The amount to be withheld is calculated base on progressive rate (PIT Rate table)
2. The witholding amount is saved in account.withholding.move table, and used on next calc.
3. Normally, the certification will be printed out at the end of year, for a person (partner)

Reference:
https://www.rd.go.th/fileadmin/user_upload/AEC/AseanTax-Thailand.pdf
