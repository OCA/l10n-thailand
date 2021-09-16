You can config PIT Rate following,

#. Go to Invoicing > Configuration > Accounting > PIT Rate
#. Add default field 'Withholding Tax Account' and 'Type of Income' when you selected bills is PIT (if any)
#. Change range or tax rate (if any)

After you config PIT Rate,

#. Create Vendor Bills
#. Check Account PIT. It will default 'Type of Income' from PIT Rate menu
#. Confirm > Register Payment
#. It will compute amount withholding tax. If calculated tax with partner and there is a tax, it will auto deduct amount to withholding tax
#. Check amount and Click Create Payment
#. It keep 'amount income' to partner and calculate when you register payment next time

**Note:** You can't register payment between check PIT and not check PIT on 1 time.
