This module adds support for capturing Tax Invoice details (Number and Date) during the inventory receipt process (Stock Picking). This is particularly useful in Thai localization when vendors provide tax invoices along with the delivered goods before the actual bill is processed.

When a Vendor Bill is subsequently generated from the Purchase Order, the tax invoice information from the associated stock pickings is automatically synced to the bill's tax invoice lines. If a single bill covers multiple receipts with different tax invoice details, the system will accurately split the tax invoice records proportionally based on the receipt amounts.


This module allows users to record **Tax Invoice Number and Date** during the inventory receipt (Stock Picking) process.

This is useful for Thai localization where vendors may provide the tax invoice together with delivered goods before the Vendor Bill is created.

When generating a **Vendor Bill** from the **Purchase Order**, the tax invoice information from related receipts will be automatically synchronized to the bill.

If multiple receipts contain different tax invoice details, the system will automatically split the tax invoice records according to the corresponding receipt amounts.