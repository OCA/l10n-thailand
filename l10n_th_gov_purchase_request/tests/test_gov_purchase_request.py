# Copyright 2022 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestGovPurchaseRequest(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Model
        cls.purchase_request_model = cls.env["purchase.request"]
        cls.procurement_committee_model = cls.env["procurement.committee"]
        cls.wiz = cls.env["purchase.request.line.make.purchase.requisition"]
        # Data Test
        cls.product1 = cls.env.ref("product.product_product_7")
        cls.procurement_type1 = cls.env.ref(
            "l10n_th_gov_purchase_request.procurement_type_001"
        )
        cls.procurement_method1 = cls.env.ref(
            "l10n_th_gov_purchase_request.procurement_specific"
        )
        cls.purchase_type3 = cls.env.ref(
            "l10n_th_gov_purchase_request.purchase_type_003"
        )
        cls.pr_exception = cls.env.ref("l10n_th_gov_purchase_request.pr_exception_4")
        cls.employee1 = cls.env.ref("hr.employee_hne")
        cls.employee2 = cls.env.ref("hr.employee_lur")
        cls.employee3 = cls.env.ref("hr.employee_jgo")

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
                    "name": "Chairman",
                    "approve_role": "chairman",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
                {
                    "name": self.employee2.display_name,
                    "approve_role": "committee",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
                {
                    "name": self.employee3.display_name,
                    "approve_role": "committee",
                    "committee_type": "work_acceptance",
                    "request_id": purchase_request.id,
                },
            ]
        )
        self.assertEqual(len(purchase_request.work_acceptance_committee_ids), 3)
        # Assign employee as committee
        purchase_request.work_acceptance_committee_ids[0].employee_id = self.employee1
        self.assertEqual(len(purchase_request.work_acceptance_committee_ids), 3)
        self.assertEqual(
            purchase_request.work_acceptance_committee_ids[0].name,
            self.employee1.display_name,
        )
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
                            "name": self.employee1.display_name,
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

    def _create_purchase_request(self):
        return self.purchase_request_model.create(
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
                "work_acceptance_committee_ids": [
                    (
                        0,
                        0,
                        {
                            "name": name,
                            "approve_role": role,
                            "committee_type": "work_acceptance",
                        },
                    )
                    for name, role in (
                        ("Chairman", "chairman"),
                        ("Committee 1", "committee"),
                        ("Committee 2", "committee"),
                    )
                ],
            }
        )

    def test_03_reject_reset_procurement_only(self):
        """Only procurement can reject or reset a verified or approved PR"""
        pr_manager = common.new_test_user(
            self.env,
            login="gov_pr_manager",
            groups="purchase_request.group_purchase_request_manager",
        )
        procurement = common.new_test_user(
            self.env,
            login="gov_procurement",
            groups=(
                "purchase.group_purchase_user,"
                "purchase_request.group_purchase_request_manager"
            ),
        )
        substate_verified = self.env.ref(
            "l10n_th_gov_purchase_request.base_substate_verified"
        )
        purchase_request = self._create_purchase_request()
        # Approved document, pass by to_approve as draft -> approved
        # is blocked by purchase_request_tier_validation (if installed)
        purchase_request.state = "to_approve"
        purchase_request.state = "approved"
        with self.assertRaises(UserError):
            purchase_request.with_user(pr_manager).button_rejected()
        with self.assertRaises(UserError):
            purchase_request.with_user(pr_manager).button_draft()
        # Verified document
        purchase_request.state = "to_approve"
        purchase_request.substate_id = substate_verified
        with self.assertRaises(UserError):
            purchase_request.with_user(pr_manager).button_rejected()
        # Bypass by context
        purchase_request.with_user(pr_manager).with_context(
            bypass_pr_reject=True
        ).button_rejected()
        self.assertEqual(purchase_request.state, "rejected")
        # Procurement can do it
        purchase_request.state = "approved"
        purchase_request.with_user(procurement).button_rejected()
        self.assertEqual(purchase_request.state, "rejected")
        purchase_request.with_user(procurement).button_draft()
        self.assertEqual(purchase_request.state, "draft")

    def test_04_estimated_cost_currency(self):
        """Estimated cost is converted to the company currency"""
        purchase_request = self._create_purchase_request()
        self.assertEqual(purchase_request.get_estimated_cost_currency(), 100.0)
        # Purchase request's currency can be changed by another module
        company_currency = purchase_request.company_id.currency_id
        currency = (
            self.env["res.currency"]
            .with_context(active_test=False)
            .search([("id", "!=", company_currency.id)], limit=1)
        )
        pr_class = type(purchase_request)
        date = fields.Date.today()
        with patch.object(pr_class, "currency_id", currency):
            self.assertEqual(
                purchase_request.get_estimated_cost_currency(date),
                currency._convert(
                    100.0, company_currency, purchase_request.company_id, date
                ),
            )
            # Fields of `purchase_request_manual_currency`
            with patch.multiple(
                pr_class,
                create=True,
                manual_currency=True,
                custom_rate=2.0,
                type_currency="inverse_company_rate",
            ):
                self.assertEqual(purchase_request.get_estimated_cost_currency(), 200.0)
            with patch.multiple(
                pr_class,
                create=True,
                manual_currency=True,
                custom_rate=2.0,
                type_currency="company_rate",
            ):
                self.assertEqual(purchase_request.get_estimated_cost_currency(), 50.0)
