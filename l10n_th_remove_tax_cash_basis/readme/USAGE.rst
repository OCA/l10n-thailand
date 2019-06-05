**Preparing Undue Tax**

- Use Developer Mode
- In Chart of Account, add new account for Undue Tax, if not already exists.
- As admin, add access rights ``Show Full Accounting Features``
- Go to Invoicing > Configuration > Settings and select ``Cash Basis``, this will open cash basis options in Tax master data
- Go to Invoicing > Configuration > Accounting > Taxes, create new undue tax for both sales and purchase

**Case Supplier Invoice/Payment**

**1) Case Undue Input VAT**

- Create new vendor bill and choose Undue Input VAT
- Validate vendor bill, journal entry will be created with Undue VAT
- Register payment as per normal, this will create new payment document as per normal
- From this process, the journal entry (cash basis) for clear undue is created, but it will be in state **Draft** and **Delete Line Base Tax Received Account** in journal entry
