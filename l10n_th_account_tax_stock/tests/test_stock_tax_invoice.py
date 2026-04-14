# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestStockTaxInvoice(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.input_vat_acct = cls.env["account.account"].create(
            {
                "name": "Input VAT 7%",
                "code": "TEST.V7",
                "account_type": "liability_current",
            }
        )

        # Purchase tax 7% on invoice
        cls.tax_7 = cls.env["account.tax"].create(
            {
                "name": "Test Purchase VAT 7%",
                "amount": 7.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "tax_exigibility": "on_invoice",
                "invoice_repartition_line_ids": [
                    Command.create(
                        {"factor_percent": 100.0, "repartition_type": "base"}
                    ),
                    Command.create(
                        {
                            "factor_percent": 100.0,
                            "repartition_type": "tax",
                            "account_id": cls.input_vat_acct.id,
                        }
                    ),
                ],
                "refund_repartition_line_ids": [
                    Command.create(
                        {"factor_percent": 100.0, "repartition_type": "base"}
                    ),
                    Command.create(
                        {
                            "factor_percent": 100.0,
                            "repartition_type": "tax",
                            "account_id": cls.input_vat_acct.id,
                        }
                    ),
                ],
            }
        )

        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Test Product A",
                "type": "consu",
                "standard_price": 100.0,
                "list_price": 100.0,
            }
        )

        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Test Vendor",
                "supplier_rank": 1,
                "is_company": True,
            }
        )

    def _make_po(self, qty, price_unit=100.0):
        """Create and confirm a PO with a single line."""
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "product_qty": qty,
                            "price_unit": price_unit,
                            "taxes_id": [Command.set(self.tax_7.ids)],
                        }
                    )
                ],
            }
        )
        po.button_confirm()
        return po

    def _validate_picking(self, picking, qty):
        """Validate *picking* with *qty* done on the first move.

        If *qty* is less than the planned quantity a backorder is created.
        Returns the validated picking.
        """
        move = picking.move_ids[0]
        move.quantity = qty
        move.picked = True

        result = picking.button_validate()

        # button_validate may return a wizard dict when a backorder is needed
        if isinstance(result, dict) and result.get("res_model"):
            wizard = (
                self.env[result["res_model"]]
                .browse(result.get("res_id"))
                .with_context(**result.get("context", {}))
            )
            wizard.process()

        return picking

    def _set_tax_info(self, picking, number, date):
        picking.write(
            {
                "tax_invoice_number": number,
                "tax_invoice_date": fields.Date.to_date(date),
            }
        )

    def _tax_inv_map(self, invoice):
        """Return {(number, date): tax_base_amount} for quick assertions."""
        return {
            (ti.tax_invoice_number, ti.tax_invoice_date): ti.tax_base_amount
            for ti in invoice.tax_invoice_ids
        }

    def test_01_single_picking_single_bill(self):
        """1 IN with tax info -> 1 bill, tax_invoice propagated from picking."""
        po = self._make_po(qty=10)
        picking = po.picking_ids
        self._set_tax_info(picking, "T001", "2026-04-01")
        self._validate_picking(picking, qty=10)

        po.action_create_invoice()
        bills = po.invoice_ids
        self.assertEqual(len(bills), 1)

        tax_invs = bills.tax_invoice_ids
        self.assertEqual(len(tax_invs), 1)
        self.assertEqual(tax_invs.tax_invoice_number, "T001")
        self.assertEqual(tax_invs.tax_invoice_date, fields.Date.to_date("2026-04-01"))
        # Base = 10 qty × 100 price, tax = 7%
        self.assertAlmostEqual(tax_invs.tax_base_amount, 1000.0)
        self.assertAlmostEqual(tax_invs.balance, 70.0)

    def test_02_single_picking_no_tax_info(self):
        """1 IN without tax info -> bill created normally, tax invoice unchanged."""
        po = self._make_po(qty=10)
        picking = po.picking_ids
        # Intentionally leave tax_invoice_number/date blank
        self._validate_picking(picking, qty=10)

        po.action_create_invoice()
        bills = po.invoice_ids
        self.assertEqual(len(bills), 1)

        tax_invs = bills.tax_invoice_ids
        self.assertEqual(len(tax_invs), 1)
        self.assertFalse(tax_invs.tax_invoice_number)
        self.assertFalse(tax_invs.tax_invoice_date)

    def test_03_two_pickings_one_bill_equal_split(self):
        """2 INs (equal qty) billed together -> 1 bill, 2 split tax_invoice records."""
        po = self._make_po(qty=20)

        # First partial receipt
        picking1 = po.picking_ids
        self._set_tax_info(picking1, "T001", "2026-04-01")
        self._validate_picking(picking1, qty=10)

        # Second receipt (backorder)
        picking2 = po.picking_ids - picking1
        self._set_tax_info(picking2, "T002", "2026-04-02")
        self._validate_picking(picking2, qty=10)

        po.action_create_invoice()
        bills = po.invoice_ids
        self.assertEqual(len(bills), 1, "Should create a single bill")

        tax_invs = bills.tax_invoice_ids
        self.assertEqual(len(tax_invs), 2, "Tax invoices should be split into 2")

        inv_map = self._tax_inv_map(bills)
        key1 = ("T001", fields.Date.to_date("2026-04-01"))
        key2 = ("T002", fields.Date.to_date("2026-04-02"))
        self.assertIn(key1, inv_map)
        self.assertIn(key2, inv_map)
        # 50 / 50 split: each 1000 base, 70 tax
        self.assertAlmostEqual(inv_map[key1], 1000.0)
        self.assertAlmostEqual(inv_map[key2], 1000.0)
        # Amounts must sum exactly to the total base
        total_base = sum(ti.tax_base_amount for ti in tax_invs)
        self.assertAlmostEqual(total_base, 2000.0)
        total_tax = sum(ti.balance for ti in tax_invs)
        self.assertAlmostEqual(total_tax, 140.0)

    def test_04_two_pickings_two_bills_sequential(self):
        """2 INs billed one by one -> each bill carries only its own picking's data."""
        po = self._make_po(qty=20)

        # First partial receipt → create bill immediately
        picking1 = po.picking_ids
        self._set_tax_info(picking1, "T001", "2026-04-01")
        self._validate_picking(picking1, qty=10)

        po.action_create_invoice()
        bill1 = po.invoice_ids
        self.assertEqual(len(bill1), 1)
        tax_invs1 = bill1.tax_invoice_ids
        self.assertEqual(len(tax_invs1), 1)
        self.assertEqual(tax_invs1.tax_invoice_number, "T001")
        self.assertAlmostEqual(tax_invs1.tax_base_amount, 1000.0)

        # Second receipt → create second bill
        picking2 = po.picking_ids - picking1
        self._set_tax_info(picking2, "T002", "2026-04-02")
        self._validate_picking(picking2, qty=10)

        po.action_create_invoice()
        bill2 = po.invoice_ids - bill1
        self.assertEqual(len(bill2), 1)
        tax_invs2 = bill2.tax_invoice_ids
        self.assertEqual(len(tax_invs2), 1)
        self.assertEqual(tax_invs2.tax_invoice_number, "T002")
        self.assertEqual(tax_invs2.tax_invoice_date, fields.Date.to_date("2026-04-02"))
        # Bill 2 covers only picking 2 (10 qty × 100 = 1000 base, 70 tax)
        self.assertAlmostEqual(tax_invs2.tax_base_amount, 1000.0)
        self.assertAlmostEqual(tax_invs2.balance, 70.0)

    def test_05_three_pickings_uneven_split(self):
        """3 INs with uneven qty billed together -> 3 split records,
        amounts sum correctly."""
        po = self._make_po(qty=30)

        # Receipt 1: 10 qty
        picking1 = po.picking_ids
        self._set_tax_info(picking1, "T001", "2026-04-01")
        self._validate_picking(picking1, qty=10)

        # Receipt 2: 5 qty
        picking2 = po.picking_ids - picking1
        self._set_tax_info(picking2, "T002", "2026-04-02")
        self._validate_picking(picking2, qty=5)

        # Receipt 3: remaining 15 qty
        picking3 = po.picking_ids - picking1 - picking2
        self._set_tax_info(picking3, "T003", "2026-04-03")
        self._validate_picking(picking3, qty=15)

        po.action_create_invoice()
        bills = po.invoice_ids
        self.assertEqual(len(bills), 1)

        tax_invs = bills.tax_invoice_ids
        self.assertEqual(len(tax_invs), 3, "Should have 3 split tax invoice records")

        inv_map = self._tax_inv_map(bills)
        key1 = ("T001", fields.Date.to_date("2026-04-01"))
        key2 = ("T002", fields.Date.to_date("2026-04-02"))
        key3 = ("T003", fields.Date.to_date("2026-04-03"))
        self.assertIn(key1, inv_map)
        self.assertIn(key2, inv_map)
        self.assertIn(key3, inv_map)

        # Ratios: T001=10/30, T002=5/30, T003=15/30
        # Total base = 3000, total tax = 210
        total_base = 3000.0
        total_tax = 210.0
        self.assertAlmostEqual(inv_map[key1], round(total_base * 10 / 30, 2), places=1)
        self.assertAlmostEqual(inv_map[key2], round(total_base * 5 / 30, 2), places=1)

        # Verify the grand totals are exact (rounding absorbed by last group)
        self.assertAlmostEqual(
            sum(ti.tax_base_amount for ti in tax_invs), total_base, places=2
        )
        self.assertAlmostEqual(sum(ti.balance for ti in tax_invs), total_tax, places=2)

    def test_06_is_stock_split_flag_prevents_recompute(self):
        """is_stock_split=True records must not have amounts overridden by compute."""
        po = self._make_po(qty=20)

        picking1 = po.picking_ids
        self._set_tax_info(picking1, "T001", "2026-04-01")
        self._validate_picking(picking1, qty=10)

        picking2 = po.picking_ids - picking1
        self._set_tax_info(picking2, "T002", "2026-04-02")
        self._validate_picking(picking2, qty=10)

        po.action_create_invoice()
        bill = po.invoice_ids
        tax_invs = bill.tax_invoice_ids

        # All split records should be flagged
        self.assertTrue(
            all(ti.is_stock_split for ti in tax_invs),
            "All tax invoice records should have is_stock_split=True",
        )

        # Record the split amounts before triggering a recompute
        amounts_before = {ti.id: ti.tax_base_amount for ti in tax_invs}

        # Force a recompute by calling the compute method directly
        tax_invs._compute_tax_amount()

        # Amounts must remain unchanged (compute should skip is_stock_split records)
        for ti in tax_invs:
            self.assertAlmostEqual(
                ti.tax_base_amount,
                amounts_before[ti.id],
                msg=f"tax_base_amount changed after recompute for record {ti.id}",
            )
