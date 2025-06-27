# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestPurchaseGuarantee(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pr_model = cls.env["purchase.requisition"]
        cls.po_model = cls.env["purchase.order"]
        cls.move_model = cls.env["account.move"]
        cls.move_line_model = cls.env["account.move.line"]
        cls.payment_register_model = cls.env["account.payment.register"]
        cls.account_model = cls.env["account.account"]
        cls.guarantee_model = cls.env["purchase.guarantee"]
        cls.guarantee_type_cash = cls.env.ref("l10n_th_gov_purchase_guarantee.cash")

        # add account in method type
        cls.account_guarantee = cls.account_model.create(
            {
                "code": "411100",
                "name": "Guarantee",
                "account_type": "income",
            }
        )
        cls.guarantee_bid_guarantee = cls.env.ref(
            "l10n_th_gov_purchase_guarantee.bid_guarantee"
        )
        cls.guarantee_bid_guarantee.account_id = cls.account_guarantee.id
        cls.guarantee_performance_bond = cls.env.ref(
            "l10n_th_gov_purchase_guarantee.performance_bond"
        )
        cls.guarantee_performance_bond.account_id = cls.account_guarantee.id
        cls.guarantee_advance_payment = cls.env.ref(
            "l10n_th_gov_purchase_guarantee.advance_payment_guarantee"
        )
        cls.guarantee_advance_payment.account_id = cls.account_guarantee.id
        cls.new_guarantee_method = cls.env["purchase.guarantee.method"].create(
            {
                "name": "Test new method default duplicate",
                "default_for_model": "purchase.order.po",
                "account_id": cls.account_guarantee.id,
            }
        )
        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.partner2 = cls.env.ref("base.res_partner_2")
        cls.product1 = cls.env.ref("product.product_product_7")

    def _create_pr(self, qty, unit_price, analytic_distribution=False):
        pr = self.pr_model.create(
            {
                "vendor_id": self.partner1.id,
                "requisition_type": "blanket_order",
                "line_ids": [
                    Command.create(
                        {
                            "product_id": self.product1.id,
                            "product_qty": qty,
                            "product_uom_id": self.product1.uom_po_id.id,
                            "price_unit": unit_price,
                            "analytic_distribution": analytic_distribution or {},
                        },
                    )
                ],
            }
        )
        return pr

    def _create_purchase(self, pr=False):
        Purchase = self.env["purchase.order"]
        view_id = "purchase.purchase_order_form"
        with Form(Purchase, view=view_id) as po:
            po.partner_id = self.partner1
            po.requisition_id = pr
        purchase = po.save()
        return purchase

    def _create_move_payment_received_guarantee(
        self, guarantee, type_guarantee="receive"
    ):
        data_create = {
            "partner_id": self.partner1.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": guarantee.guarantee_method_id.name,
                        "account_id": guarantee.guarantee_method_id.account_id.id,
                        "quantity": 1,
                        "price_unit": guarantee.amount,
                        "analytic_distribution": guarantee.analytic_distribution,
                        "analytic_tag_ids": [
                            Command.set(guarantee.analytic_tag_ids.ids)
                        ],
                    },
                )
            ],
        }
        if type_guarantee == "receive":
            data_create["guarantee_ids"] = [Command.link(guarantee.id)]
            data_create["move_type"] = "out_invoice"
        elif type_guarantee == "return":
            data_create["return_guarantee_ids"] = [Command.link(guarantee.id)]
            data_create["move_type"] = "in_invoice"
        move = self.move_model.create(data_create)
        move.action_post()
        # Register Payment
        ctx = {
            "active_ids": [move.id],
            "active_id": move.id,
            "active_model": "account.move",
        }
        payment_wizard_form = Form(self.payment_register_model.with_context(**ctx))
        payment_wizard = payment_wizard_form.save()
        payment = payment_wizard.action_create_payments()
        return payment

    def test_01_pr_guarantee(self):
        """Test process guarantee with purchase requisition"""
        analytic_camp = self.env.ref("analytic.analytic_partners_camp_to_camp")
        analytic_distribution = {str(analytic_camp.id): 100}
        pr = self._create_pr(1, 100.0, analytic_distribution=analytic_distribution)
        self.assertEqual(pr.purchase_guarantee_count, 0)
        self.assertEqual(pr.state, "draft")
        result = pr.action_view_purchase_guarantee()
        self.assertEqual(
            result["context"]["default_reference"],
            f"purchase.requisition,{pr.id}",
        )
        # Test create guarantee on purchase.requisition with state draft
        with self.assertRaisesRegex(
            UserError, "Purchase Agreement must be in status: Confirmed"
        ):
            Form(self.guarantee_model.with_context(**result["context"]))

        pr.action_confirm()
        self.assertEqual(pr.state, "confirmed")
        # Create guarantee on purchase.requisition
        with Form(self.guarantee_model.with_context(**result["context"])) as f:
            f.partner_id = self.partner1
            f.guarantee_type_id = self.guarantee_type_cash
            f.amount = 100.0
            f.date_guarantee_receive = fields.Date.today()
            f.document_ref = "ref"
        pr_guarantee = f.save()
        self.assertEqual(pr.purchase_guarantee_count, 1)
        self.assertEqual(pr_guarantee.guarantee_method_id, self.guarantee_bid_guarantee)
        self.assertEqual(pr_guarantee.reference, pr)
        self.assertEqual(pr_guarantee.amount_received, 0.0)
        self.assertEqual(pr_guarantee.amount_returned, 0.0)
        self.assertEqual(
            pr_guarantee.guarantee_method_id.account_id, self.account_guarantee
        )
        self.assertEqual(pr_guarantee.analytic_distribution, analytic_distribution)
        # Check name search and display_name
        self.assertEqual(pr_guarantee.display_name, f"{pr_guarantee.name} ({pr.name})")

        # Create invoice guarantee
        with Form(self.move_model.with_context(default_move_type="out_invoice")) as m:
            m.partner_id = self.partner1
            m.guarantee_ids = pr_guarantee
        move = m.save()
        self.assertEqual(len(move.invoice_line_ids), 1)

        # Test change partner after select guarantee, it should clear all line
        with Form(move) as m:
            m.partner_id = self.partner2
        m.save()
        self.assertEqual(len(move.invoice_line_ids), 0)
        self.assertFalse(move.guarantee_ids)
        with self.assertRaisesRegex(
            UserError, "You need to add a line before posting."
        ):
            move.action_post()

        # Create new move for received guarantee
        self._create_move_payment_received_guarantee(pr_guarantee)
        self.assertEqual(pr_guarantee.amount_received, 100.0)
        self.assertTrue(pr_guarantee.invoice_ids)

        # Create bill for return guarantee, it should auto generate new line
        with Form(self.move_model.with_context(default_move_type="in_invoice")) as m:
            m.partner_id = self.partner1
            m.return_guarantee_ids = pr_guarantee
        bill = m.save()
        self.assertEqual(len(bill.invoice_line_ids), 1)

        # Create new move for return guarantee
        self._create_move_payment_received_guarantee(pr_guarantee, "return")
        self.assertEqual(pr_guarantee.amount_returned, 100.0)

    def test_02_po_guarantee(self):
        """Test process guarantee with purchase order"""
        pr = self._create_pr(1, 100.0)
        pr.action_confirm()
        purchase = self._create_purchase(pr)
        self.assertEqual(purchase.purchase_guarantee_count, 0)
        result = purchase.action_view_purchase_guarantee()
        self.assertEqual(
            result["context"]["default_reference"],
            f"purchase.order,{purchase.id}",
        )
        # Create guarantee on purchase.order state draft
        with Form(self.guarantee_model.with_context(**result["context"])) as f:
            f.guarantee_type_id = self.guarantee_type_cash
            f.amount = 100.0
            f.date_guarantee_receive = fields.Date.today()
            f.document_ref = "ref"
        po_guarantee = f.save()
        self.assertEqual(purchase.purchase_guarantee_count, 1)
        self.assertEqual(
            po_guarantee.guarantee_method_id, self.guarantee_performance_bond
        )
        self.assertEqual(po_guarantee.reference, purchase)
        self.assertEqual(po_guarantee.amount_received, 0.0)
        self.assertEqual(po_guarantee.amount_returned, 0.0)
        self.assertEqual(
            po_guarantee.guarantee_method_id.account_id, self.account_guarantee
        )
        purchase.button_confirm()
        # Create guarantee on purchase.order state purchase
        with Form(self.guarantee_model.with_context(**result["context"])) as f:
            f.guarantee_type_id = self.guarantee_type_cash
            f.amount = 200.0
            f.date_guarantee_receive = fields.Date.today()
            f.document_ref = "ref2"
        po_guarantee2 = f.save()
        self.assertEqual(purchase.purchase_guarantee_count, 2)
        self.assertEqual(
            po_guarantee2.guarantee_method_id, self.guarantee_advance_payment
        )
        # Can edit guarantee method, if there are more than 1 method in model
        self.assertTrue(po_guarantee2.can_edit_guarantee_method)
        self.assertFalse(po_guarantee.can_edit_guarantee_method)

        # Create new move for received guarantee
        self._create_move_payment_received_guarantee(po_guarantee)
        self.assertEqual(po_guarantee.amount_received, 100.0)
        self.assertTrue(po_guarantee.invoice_ids)

        # Create new move for return guarantee
        self._create_move_payment_received_guarantee(po_guarantee, "return")
        self.assertEqual(po_guarantee.amount_returned, 100.0)

        # Create new move for received guarantee
        self._create_move_payment_received_guarantee(po_guarantee2)
        self.assertEqual(po_guarantee2.amount_received, 200.0)
        self.assertTrue(po_guarantee2.invoice_ids)

        # Create new move for return guarantee
        self._create_move_payment_received_guarantee(po_guarantee2, "return")
        self.assertEqual(po_guarantee2.amount_returned, 200.0)

    def test_03_create_guarantee_direct(self):
        guarantee = self.guarantee_model.create({"name": "TEST Direct"})
        self.assertEqual(guarantee.display_name, guarantee.name)
        self.assertFalse(guarantee.analytic_tag_ids)
