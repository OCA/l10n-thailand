The ``l10n_th_bank_payment_export`` module provides a **base wizard model** to support exporting payment files in **text format**, which is commonly required by Thai banks.

This module itself does **not generate a payment file directly**, but serves as a foundation that other modules can extend to support bank-specific formats (e.g. KTB, BBL, SCB, etc.)

**Key Features:**

- Supports exporting payments to a bank-specific text format.
- Includes a flexible **template system** to define default values.
- Export structure can be configured dynamically using conditions and expressions.

.. note::
   This module requires further development to be functional with a specific bank. See module ``l10n_th_bank_payment_export_ktb`` as a reference implementation.
