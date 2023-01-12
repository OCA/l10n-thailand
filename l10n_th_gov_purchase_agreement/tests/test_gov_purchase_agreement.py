# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase


@tagged("post_install", "-at_install")
class TestGovPurchaseAgreement(TransactionCase):
    def setUp(self):
        super().setUp()
        self.pr_model = self.env["purchase.requisition"]
        self.po_model = self.env["purchase.order"]
        self.partner1 = self.env.ref("base.res_partner_1")
        self.product1 = self.env.ref("product.product_product_7")
        self.agreement = self.env.ref("agreement.market1")
        self.agreement2 = self.env.ref("agreement.market2")

    def _create_pr(self, po_type, qty, unit_price):
        pr = self.pr_model.create(
            {
                "user_id": self.env.ref("base.user_root").id,
                "type_id": self.env.ref("purchase_requisition.type_multi").id,
                "po_type": po_type,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product1.id,
                            "product_qty": qty,
                            "product_uom_id": self.product1.uom_po_id.id,
                            "price_unit": unit_price,
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

    def test_01_po_agreement(self):
        """Test process agreement with purchase"""
        pr = self._create_pr("agreement", 1, 100.0)
        pr.action_in_progress()
        purchase = self._create_purchase(pr)
        # No agreement. can't confirm
        self.assertEqual(len(purchase.agreement_ids.ids), 0)
        with self.assertRaises(UserError):
            purchase.button_confirm()
        self.assertFalse(self.agreement.purchase_order_id)
        # Test partner difference on purchase and agreement
        with self.assertRaises(UserError):
            self.agreement.purchase_order_id = purchase.id
        # Test change purchase in agreement, partner will change following purchase
        old_partner = self.agreement.partner_id
        with Form(self.agreement) as ag:
            ag.purchase_order_id = purchase
        ag.save()
        self.assertNotEqual(self.agreement.partner_id, old_partner)
        self.assertEqual(self.agreement.partner_id, self.partner1)
        # check agreement on purchase
        self.assertEqual(purchase.agreement_count, 1)
        action = purchase.action_view_agreement()
        self.assertEqual(action["res_id"], self.agreement.id)
        # Add duplicate purchase into new agreement
        with Form(self.agreement2) as ag:
            ag.purchase_order_id = purchase
        ag.save()
        self.assertEqual(purchase.agreement_count, 2)
        action = purchase.action_view_agreement()
        self.assertEqual(action["domain"][0][2], purchase.agreement_ids.ids)
        # Test inverse, it should be not change
        self.assertFalse(self.agreement.invoice_plan_ids)
        self.assertFalse(purchase.invoice_plan_ids)
        self.agreement._inverse_invoice_plan_ids()
        self.assertFalse(self.agreement.invoice_plan_ids)
        self.assertFalse(purchase.invoice_plan_ids)
        # _inverse_invoice_plan_ids
        purchase.button_confirm()
