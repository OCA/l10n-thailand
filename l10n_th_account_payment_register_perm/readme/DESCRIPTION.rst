By standard Odoo, from an invoice, user make payment by click on Register Payment which
launch a Payment Wizard.

This module change Payment Register Wizard which was `models.TransientModel`
into a permanent menu Payment Register `models.Model`

The way the payment works is still the same as before, but it gives extra benefits,

* By being a new stored documents, it now has states Draft/Submit/Paid/Cancel
* So, it is now possible to extend the document further, i.e., approval process.
* When payment is paid, this document keep tracks of reconciled invoices vs payments
* It is now possible to cancel the Payment Register (which will set the payment(s) to draft), and re-reconcile it back later
