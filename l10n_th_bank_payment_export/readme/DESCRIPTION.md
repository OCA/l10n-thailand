The `l10n_th_bank_payment_export` module provides a **base framework**
for exporting vendor payment data into **bank-specific text files**,
commonly required by Thai banks.

This module itself does **not generate a bank-specific payment file**,
but serves as a foundation that other modules can extend to support
specific bank formats (e.g. KTB, BBL, SCB, KBank, etc.)

**Key Features:**

- **Bank Template** - Define the text file structure using template
  lines with configurable field lengths, alignment, padding, and
  value sources (fixed or Python expression).
- **Bank Template Section** - Organize template lines into a
  hierarchical section structure (parent/child) with data-level
  iteration (Document, Payment, Invoice, Withholding Tax, or Custom).
- **Bank Payment Profile** - Pre-configure default field values per
  bank, automatically applied when creating a payment export.
- **Dual Export** - Export as `.txt` (text file) or preview as `.xlsx`
  (Excel).

> **Note:** This module requires a bank-specific extension module to be
> functional. See `l10n_th_bank_payment_export_ktb` as a reference
> implementation.
