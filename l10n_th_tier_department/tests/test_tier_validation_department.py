# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import tagged

from odoo.addons.base_tier_validation.tests.common import CommonTierValidation


@tagged("post_install", "-at_install")
class TierTierValidationDepartment(CommonTierValidation):
    def setUp(self):
        super().setUp()
        self.dep_admin = self.env.ref("hr.dep_administration")
        self.tier_level = self.env["tier.level"]
        # Create employees for test users (department_id is a related field
        # via employee_id in Odoo 19)
        self.env["hr.employee"].create(
            {"name": self.test_user_1.name, "user_id": self.test_user_1.id}
        )
        self.env["hr.employee"].create(
            {"name": self.test_user_2.name, "user_id": self.test_user_2.id}
        )

        # Create tier definitions:
        reviewer_expression = (
            "rec.user_id.employee_id.department_id.find_reviewer_level(level=1)"
        )
        self.tier_def = self.tier_def_obj.create(
            {
                "model_id": self.tester_model.id,
                "review_type": "expression",
                "reviewer_expression": reviewer_expression,
                "definition_domain": "[('test_field', '>', 1.0)]",
            }
        )

    def test_01_tier_level(self):
        # Add tier level in department
        self.test_user_2.employee_id.department_id = self.dep_admin.id
        self.tier_level.create(
            {
                "department_id": self.dep_admin.id,
                "user_id": self.test_user_1.id,
            }
        )
        self.assertEqual(len(self.dep_admin.tier_level_ids), 1)
        self.assertEqual(self.dep_admin.tier_level_ids.level, 1)
        # Create new test record
        test_record = self.test_model.create(
            {
                "test_field": 2.5,
                "user_id": self.test_user_2.id,
            }
        )
        # Request validation
        review = test_record.request_validation()
        self.assertTrue(review)
        self.assertEqual(review.reviewer_ids, self.test_user_1)

    def test_02_tier_no_level(self):
        self.test_user_2.employee_id.department_id = self.dep_admin.id
        self.assertEqual(len(self.dep_admin.tier_level_ids), 0)
        # Create new test record
        test_record = self.test_model.create(
            {
                "test_field": 2.5,
                "user_id": self.test_user_2.id,
            }
        )
        # Request validation
        review = test_record.with_user(self.test_user_1.id).request_validation()
        self.assertTrue(review)
        # Default itself, if no tier level
        self.assertEqual(review.reviewer_ids, self.test_user_1)

    def test_03_tier_level_overflow(self):
        """Request level higher than available — should return last approver."""
        self.test_user_2.employee_id.department_id = self.dep_admin.id
        # Create only 1 tier level
        self.tier_level.create(
            {
                "department_id": self.dep_admin.id,
                "user_id": self.test_user_1.id,
            }
        )
        self.assertEqual(len(self.dep_admin.tier_level_ids), 1)
        # Ask for level 5 — exceeds available levels, should fallback to last
        reviewer = self.dep_admin.find_reviewer_level(level=5)
        self.assertEqual(reviewer, self.test_user_1)

    def test_04_tier_level_multi(self):
        """Multiple tier levels — verify correct level assignment."""
        self.test_user_2.employee_id.department_id = self.dep_admin.id
        # Create 2 tier levels with different sequences
        level_1 = self.tier_level.create(
            {
                "department_id": self.dep_admin.id,
                "user_id": self.test_user_1.id,
                "sequence": 10,
            }
        )
        level_2 = self.tier_level.create(
            {
                "department_id": self.dep_admin.id,
                "user_id": self.test_user_2.id,
                "sequence": 20,
            }
        )
        # Verify computed levels
        self.assertEqual(level_1.level, 1)
        self.assertEqual(level_2.level, 2)
        # Level 1 returns user_1, level 2 returns user_2
        self.assertEqual(self.dep_admin.find_reviewer_level(level=1), self.test_user_1)
        self.assertEqual(self.dep_admin.find_reviewer_level(level=2), self.test_user_2)

    def test_05_find_reviewer_level_zero(self):
        """level=0 (default) should return current user regardless of tiers."""
        self.test_user_2.employee_id.department_id = self.dep_admin.id
        self.tier_level.create(
            {
                "department_id": self.dep_admin.id,
                "user_id": self.test_user_1.id,
            }
        )
        # level=0 means no specific level requested — return current user
        reviewer = self.dep_admin.find_reviewer_level(level=0)
        self.assertEqual(reviewer, self.env.user)
