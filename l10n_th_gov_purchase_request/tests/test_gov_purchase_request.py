# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestGovPurchaseRequest(common.TransactionCase):
    def setUp(self):
        super().setUp()
        # Model
        self.purchase_request_model = self.env["purchase.request"]
        self.procurement_committee_model = self.env["procurement.committee"]
        self.wiz = self.env["purchase.request.line.make.purchase.requisition"]
        # Data Test
        self.product1 = self.env.ref("product.product_product_7")
        self.procurement_type1 = self.env.ref(
            "l10n_th_gov_purchase_request.procurement_type_001"
        )
        self.procurement_method1 = self.env.ref(
            "l10n_th_gov_purchase_request.procurement_specific"
        )
        self.purchase_type3 = self.env.ref(
            "l10n_th_gov_purchase_request.purchase_type_003"
        )
        self.pr_exception = self.env.ref("l10n_th_gov_purchase_request.pr_exception_4")
        self.employee1 = self.env.ref("hr.employee_hne")
        self.employee2 = self.env.ref("hr.employee_lur")
        self.employee3 = self.env.ref("hr.employee_jgo")

    def test_01_gov_purchase_request(self):
        purchase_request = self.purchase_request_model.create(
            {
                "procurement_type_id": self.procurement_type1.id,
                "procurement_method_id": self.procurement_method1.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "estimated_cost": 100.0,
                            "product_qty": 1,
                        },
                    )
                ],
            }
        )
        self.assertEqual(
            purchase_request.line_ids.product_id, self.procurement_type1.product_id
        )
        # Exceptions rule, at least 3 committees are required.
        self.assertEqual(purchase_request.state, "draft")
        purchase_request.button_to_approve()
        self.assertTrue(purchase_request.exception_ids)
        self.assertEqual(purchase_request.state, "draft")
        # Create committees
        self.procurement_committee_model.create(
            [
                {
                    "employee_id": self.employee1.id,
                    "approve_role": "chairman",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
                {
                    "employee_id": self.employee2.id,
                    "approve_role": "committee",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
                {
                    "employee_id": self.employee3.id,
                    "approve_role": "committee",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
            ]
        )
        self.assertEqual(len(purchase_request.work_acceptance_committee_ids), 3)
        # Test open purchase agreement with purchase request state draft, it should error
        with self.assertRaises(UserError):
            self.wiz.with_context(
                active_model="purchase.request.line",
                active_ids=[purchase_request.line_ids.id],
                active_id=purchase_request.line_ids.id,
            ).create({})
        purchase_request.button_to_approve()
        # Substate To Verify -> Verified
        self.assertEqual(purchase_request.state, "to_approve")
        self.assertEqual(purchase_request.substate_id.sequence, 10)
        purchase_request.with_context(to_substate_sequence=20).action_to_substate()
        self.assertEqual(purchase_request.state, "to_approve")
        self.assertEqual(purchase_request.substate_id.sequence, 20)
        purchase_request.button_approved()
        self.assertEqual(purchase_request.state, "approved")
        self.assertEqual(purchase_request.date_approved, fields.Date.today())
        # Create purchase agreement from purchase request
        wiz = self.wiz.with_context(
            active_model="purchase.request.line",
            active_ids=[purchase_request.line_ids.id],
            active_id=purchase_request.line_ids.id,
        ).create({})
        wiz.make_purchase_requisition()

    def test_02_constraint(self):
        """Test other case check constraint"""
        # Can't create purchase type with default more than 1
        with self.assertRaises(UserError):
            self.env["purchase.type"].create(
                {
                    "name": "New Type",
                    "to_create": "purchase_agreement",
                    "is_default": True,
                    "procurement_method_ids": [(6, 0, [self.procurement_method1.id])],
                }
            )
        # it should select procurement method following purchase type
        with Form(self.purchase_request_model) as pr:
            pr.purchase_type_id = self.purchase_type3
            pr.procurement_type_id = self.procurement_type1
            pr.expense_reason = "Test Reason"
        purchase_request = pr.save()
        self.assertEqual(
            pr.procurement_method_id, self.purchase_type3.procurement_method_ids
        )
        purchase_request.write(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "estimated_cost": 100.0,
                            "product_qty": 1,
                        },
                    )
                ],
                "work_acceptance_committee_ids": [
                    (
                        0,
                        0,
                        {
                            "employee_id": self.employee1.id,
                            "approve_role": "committee",
                            "committee_type": "work_acceptance",
                        },
                    )
                ],
            }
        )
        purchase_request.button_to_approve()
        # Substate To Verify -> Verified
        self.assertEqual(purchase_request.state, "to_approve")
        self.assertEqual(purchase_request.substate_id.sequence, 10)
        purchase_request.with_context(to_substate_sequence=20).action_to_substate()
        self.assertEqual(purchase_request.state, "to_approve")
        self.assertEqual(purchase_request.substate_id.sequence, 20)
        purchase_request.button_approved()
        self.assertEqual(purchase_request.state, "approved")
        self.assertEqual(purchase_request.date_approved, fields.Date.today())
        # Test open purchase agreement with purchase type expense, it should error
        with self.assertRaises(UserError):
            self.wiz.with_context(
                active_model="purchase.request",
                active_ids=[purchase_request.id],
                active_id=purchase_request.id,
            ).create({})
