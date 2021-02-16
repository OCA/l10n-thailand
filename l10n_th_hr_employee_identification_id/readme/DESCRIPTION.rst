This module added validation for Identification No of Employee who is a citizen of Thailand.

Validation only occurs when Employee's **Nationality** is Thailand and **Identification No** is present.

* Auto remove non-digit characters
* Must be digits with 13 lengths
* Verify checksum at last digit

Reference: `เลขประจำตัวประชาชนไทย <https://th.wikipedia.org/wiki/เลขประจำตัวประชาชนไทย>`_
