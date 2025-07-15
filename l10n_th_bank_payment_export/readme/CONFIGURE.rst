Bank Payment Template
======================

Used to **group default values** for easier user selection and error reduction during data entry.

Steps:

#. Go to *Invoicing > Configuration > Payments > Bank Payment Templates*
#. Create a new template and:

   - Select the **bank**.
   - In the template lines, define **field names** and **default values**.
#. When a user selects this template during payment export, the system will **auto-fill** the corresponding values.

.. note::
   Values must be valid (existing in the system). Invalid or incorrect entries will result in an error.

Bank Export Format
===================

Defines the structure of the output **text file** according to the specific bank's requirements.

Menu: *Settings > Technical > Bank Export Format*

Format Fields:

- **Description**: Explanation of the line.
- **Condition Line**: Logic to determine whether this line should be included.
- **Group**: Used to group lines for looping purposes.
- **Loop**: Repeats the line for each ``bank.payment.export.line``.
- **Sub Loop**: Nested loop (e.g. all invoices related to a payment line).
- **Sub Value Loop**: Field needed to drive the sub loop.
- **End Line**: Adds ``/r/t`` at the end of the line (if checked).
- **Length**: Max length of the value (required for Fixed values).
- **From/To**: Character position range (start-end).
- **Alignment**: Align value to **left** or **right**.
- **Blank Space**: Filler if the value doesn’t reach the defined length.
- **Value Type**: ``Fixed`` for hardcoded value, ``Python`` for dynamic value.
- **Value**:

  - If ``Fixed``: static value to be printed.
  - If ``Python``: expression evaluated dynamically.

Python Dynamic Fields:

- ``rec``: The export document (``bank.payment.export``)
- ``line``:

  - If **no Loop**, refers to ``rec.export_line_ids``
  - If **Loop**, refers to the current line
- ``sub_line``: Object in the **Sub Loop**
- ``today``: Current date
- ``today_datetime``: Current date and time
- ``idx``: Index of the current line
- ``idx_line``: Index within the loop
- ``idx_sub_line``: Index within the sub loop
- ``wht_cert``: Withholding tax certificate (requires ``l10n_th_account_tax``)
- ``invoices``: Invoices related to the payment
