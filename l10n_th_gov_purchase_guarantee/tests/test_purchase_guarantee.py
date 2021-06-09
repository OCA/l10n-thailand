# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestPurchaseGuarantee(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.pr_model = self.env["purchase.requisition"]
        self.po_model = self.env["purchase.order"]
        self.move_model = self.env["account.move"]
        self.move_line_model = self.env["account.move.line"]
        self.payment_register_model = self.env["account.payment.register"]
        self.account_model = self.env["account.account"]
        self.guarantee_model = self.env["purchase.guarantee"]
        self.guarantee_type_cash = self.env.ref("l10n_th_gov_purchase_guarantee.cash")
        self.main_company = self.env.ref("base.main_company")
        # add account in method type
        self.account_guarantee = self.account_model.create(
            {
                "code": "411100",
                "name": "Guarantee",
                "user_type_id": self.ref("account.data_account_type_other_income"),
                "company_id": self.main_company.id,
            }
        )
        self.guarantee_bid_guarantee = self.env.ref(
            "l10n_th_gov_purchase_guarantee.bid_guarantee"
        )
        self.guarantee_bid_guarantee.account_id = self.account_guarantee.id
        self.guarantee_performance_bond = self.env.ref(
            "l10n_th_gov_purchase_guarantee.performance_bond"
        )
        self.guarantee_performance_bond.account_id = self.account_guarantee.id
        self.guarantee_advance_payment = self.env.ref(
            "l10n_th_gov_purchase_guarantee.advance_payment_guarantee"
        )
        self.guarantee_advance_payment.account_id = self.account_guarantee.id
        self.new_guarantee_method = self.env["purchase.guarantee.method"].create(
            {
                "name": "Test new method default duplicate",
                "default_for_model": "purchase.order.po",
                "account_id": self.account_guarantee.id,
            }
        )
        self.partner1 = self.env.ref("base.res_partner_1")
        self.partner2 = self.env.ref("base.res_partner_2")
        self.product1 = self.env.ref("product.product_product_7")

    def _create_pr(self, qty, unit_price, analytic_account=False):
        pr = self.pr_model.create(
            {
                "user_id": self.env.ref("base.user_root").id,
                "type_id": self.env.ref("purchase_requisition.type_multi").id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product1.id,
                            "product_qty": qty,
                            "product_uom_id": self.product1.uom_po_id.id,
                            "price_unit": unit_price,
                            "account_analytic_id": analytic_account
                            and analytic_account.id,
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
                (
                    0,
                    0,
                    {
                        "name": guarantee.guarantee_method_id.name,
                        "account_id": guarantee.guarantee_method_id.account_id.id,
                        "quantity": 1,
                        "price_unit": guarantee.amount,
                        "analytic_account_id": guarantee.analytic_account_id.id,
                        "analytic_tag_ids": [(6, 0, guarantee.analytic_tag_ids.ids)],
                    },
                )
            ],
        }
        if type_guarantee == "receive":
            data_create["guarantee_ids"] = [(4, guarantee.id)]
            data_create["move_type"] = "out_invoice"
        elif type_guarantee == "return":
            data_create["return_guarantee_ids"] = [(4, guarantee.id)]
            data_create["move_type"] = "in_invoice"
        move = self.move_model.create(data_create)
        move.action_post()
        # Register Payment
        ctx = {
            "active_ids": [move.id],
            "active_id": move.id,
            "active_model": "account.move",
        }
        payment_wizard_form = Form(self.payment_register_model.with_context(ctx))
        payment_wizard = payment_wizard_form.save()
        payment = payment_wizard.action_create_payments()
        return payment

    def test_01_pr_guarantee(self):
        """Test process guarantee with purchase requisition"""
        analytic_camp = self.env.ref("analytic.analytic_partners_camp_to_camp")
        pr = self._create_pr(1, 100.0, analytic_account=analytic_camp)
        self.assertEqual(pr.purchase_guarantee_count, 0)
        self.assertEqual(pr.state, "draft")
        result = pr.action_view_purchase_guarantee()
        self.assertEqual(
            result["context"]["default_reference"],
            "purchase.requisition,{}".format(pr.id),
        )
        # Test create guarantee on purchase.requisition with state draft
        with self.assertRaises(UserError):
            with Form(self.guarantee_model.with_context(result["context"])) as f:
                f.name = "Test Guarantee"
        pr.action_in_progress()
        self.assertEqual(pr.state, "in_progress")
        # Create guarantee on purchase.requisition
        with Form(self.guarantee_model.with_context(result["context"])) as f:
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
        self.assertEqual(pr_guarantee.analytic_account_id, analytic_camp)
        # Check name search and name get
        self.assertEqual(
            pr_guarantee.name_get()[0][1], "{} ({})".format(pr_guarantee.name, pr.name)
        )
        self.assertEqual(len(pr_guarantee.name_search(pr.name)), 1)
        move = self.move_model.create(
            {"partner_id": self.partner1.id, "guarantee_ids": [(4, pr_guarantee.id)]}
        )
        # function 'new' can't use in unit test. So, create line directly.
        move._onchange_guarantee_ids()
        prepare_line = move._prepare_guarantee_move_line(pr_guarantee)
        self.move_line_model.create(prepare_line)
        # Test change partner after select guarantee, it should clear all line
        self.assertEqual(len(move.invoice_line_ids), 1)
        with self.assertRaises(UserError):
            with Form(move) as inv:
                inv.partner_id = self.partner2
            self.assertEqual(len(move.invoice_line_ids), 0)
            self.assertFalse(move.guarantee_ids)
            move.action_post()

        # Create new move for received guarantee
        self._create_move_payment_received_guarantee(pr_guarantee)
        self.assertEqual(pr_guarantee.amount_received, 100.0)
        self.assertTrue(pr_guarantee.invoice_ids)

        # Create new move for return guarantee
        self._create_move_payment_received_guarantee(pr_guarantee, "return")
        self.assertEqual(pr_guarantee.amount_returned, 100.0)

    def test_02_po_guarantee(self):
        """Test process guarantee with purchase order"""
        pr = self._create_pr(1, 100.0)
        pr.action_in_progress()
        purchase = self._create_purchase(pr)
        self.assertEqual(purchase.purchase_guarantee_count, 0)
        result = purchase.action_view_purchase_guarantee()
        self.assertEqual(
            result["context"]["default_reference"],
            "purchase.order,{}".format(purchase.id),
        )
        # Create guarantee on purchase.order state draft
        with Form(self.guarantee_model.with_context(result["context"])) as f:
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
        with Form(self.guarantee_model.with_context(result["context"])) as f:
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
