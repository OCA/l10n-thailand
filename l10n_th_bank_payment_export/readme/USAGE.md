There are **two ways** to create a Bank Payment Export:

## 1. From Vendor Payments

1. Go to *Invoicing \> Vendors \> Payments*
2. Select one or more payments (must be in **Paid** status with
   export status **Draft**)
3. Click *Action \> Create Bank Payment Export*

> All selected payments must share the same **Bank Payment Profile**
> and **Currency**. Each payment must have a **Vendor Bank Account**.

## 2. Directly Create Export

1. Go to *Invoicing \> Accounting \> Bank Payment Export*
2. Click *New*
3. Select a **Profile** to auto-fill default values, then choose a
   **Bank Template** and set the **Effective Date**
4. Add payment lines manually, or click *Get All Payments* to load
   all eligible payments automatically
5. Click *Confirm*

## Exporting

Once the export is confirmed, two export options are available:

- **Export Text File** — Generates a `.txt` file based on the bank
  template and changes the status to **Done**.
- **Export Excel** — Previews the export data in `.xlsx` format
  (status remains **Confirmed**).

## Managing Exports

- **Set to Draft** — Returns a confirmed export back to draft for
  editing.
- **Cancel** — Cancels the export before it is sent to the bank.
  Resets all payment export statuses to **Draft**.
- **Reject** — Rejects an exported document. Resets all payment
  export statuses to **Draft**.
- **Reject (line-level)** — Individual payment lines can be rejected
  after export. If all lines are rejected, the entire export is
  automatically rejected.

## Payment Register

When registering a payment from a vendor bill, you can:

- Set the **Bank Payment Profile** (auto-populated from the vendor's
  default profile).
- Check **Bank Payment Exported** to mark the payment as already
  exported (skips the export workflow).
