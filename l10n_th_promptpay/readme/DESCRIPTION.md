The PromptPay QR code (Thai QR Payment) allows customers to pay by scanning
a QR code with any bank's mobile application.

This module extends Odoo's built-in QR code support (`account_qr_code_emv`) to support Thai PromptPay
standards for two types of payment:

**1. PromptPay (Credit Transfer)**

For standard person-to-person or merchant payments using a PromptPay proxy ID:

- **Mobile Number** — 10-digit phone number (e.g. `0812345678`)
- **Merchant Tax ID** — 13-digit juristic person ID (e.g. `1234567890123`)
- **Ewallet ID** — e-wallet account identifier

**2. PromptPay Bill Payment**

For biller-initiated collection using a registered Biller ID (15 digits).
Supports **Reference 1** and **Reference 2** fields configurable per company,
allowing the QR code to carry invoice-specific references (e.g. customer code,
payment reference).

The module adds a **PromptPay QR Code** button on vendor/customer invoices
to generate and display the QR code in a popup dialog.

The implementation follows the EMVCo QR specification used by the Thai PromptPay network.

Note: that *Credit Transfer* is also provided by the module
`l10n_th` (Thai localization). This module can work independently without
`l10n_th`, but if `l10n_th` is installed, both modules may provide similar
QR generation capabilities.
