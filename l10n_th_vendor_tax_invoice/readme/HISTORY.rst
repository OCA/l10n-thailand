12.0.1.0.0 (2019-03-07)
~~~~~~~~~~~~~~~~~~~~~~~

* Start of the history

12.0.1.0.1 (2019-06-04)
~~~~~~~~~~~~~~~~~~~~~~~

* Change field name

12.0.1.1.0 (2019-06-11)
~~~~~~~~~~~~~~~~~~~~~~~

* Delete line in journal entry is not used
* Invisible required field Base Tax Received Account

12.0.2.0.0 (2019-06-22)
~~~~~~~~~~~~~~~~~~~~~~~

* Applicable to HR Expense too, when it also use Undue Tax (add depends on hr_expense)
* Add partner_id in account.payment.tax, to allow changing partner (mostly for expense case)

12.0.2.1.0 (2019-07-17)
~~~~~~~~~~~~~~~~~~~~~~~

* Add partner, invoice date/number and amount fields in Tax Adjustments Wizard (to comply with Thai tax report)
* Fix bug Tax Base amount in move line is 0 (case undue vat)
