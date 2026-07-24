## Enable QR Code on Invoices

Before generating any PromptPay QR code, the QR code feature must be enabled
in Odoo's accounting settings.

1. Go to **Invoicing > Configuration > Settings**.
2. Under the **Customer Payments** section, enable **QR Codes**.
3. Click **Save**.

This activates the `emv_qr` QR method globally and makes the QR Code Type
field available on bank accounts.

---

## Configure Bank Account for Bill Payment / PromptPay

1. Go to **Bank Accounts**.
2. Open (or create) the company's bank account.
3. Set **Proxy Type**

---

## Configure Reference Fields (per company)

Reference 1 and Reference 2 are embedded in the Bill Payment QR code and
are typically used to identify the payer or the invoice on the biller's system.

1. Go to **Invoicing > Configuration > Settings**.
2. Under **Customer Payments**, locate:
   - **PromptPay Reference 1 Field** - field path on `account.move` used as Ref1
   - **PromptPay Reference 2 Field** - field path on `account.move` used as Ref2
3. Enter a dotted field path. Examples:

   | Value | Result |
   |---|---|
   | `partner_id.ref` | Customer's internal reference code |
   | `partner_id.name` | Customer name |
   | `name` | Invoice number (e.g. `INV/2025/00001`) |
   | `payment_reference` | Payment reference field on the invoice |

4. Click **Save**.

> **Note:** Reference 1 defaults to `partner_id.ref` if not set.
> Reference 2 is optional and can be left blank.
