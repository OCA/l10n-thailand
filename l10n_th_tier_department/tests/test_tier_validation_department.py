# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo_test_helper import FakeModelLoader

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TierTierValidationDepartment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from odoo.addons.base_tier_validation.tests.tier_validation_tester import (
            TierDefinition,
            TierValidationTester,
        )

        cls.loader.update_registry((TierValidationTester, TierDefinition))
        cls.test_model = cls.env[TierValidationTester._name]

        cls.tester_model = cls.env["ir.model"].search(
            [("model", "=", "tier.validation.tester")]
        )

        # Access record:
        cls.env["ir.model.access"].create(
            {
                "name": "access.tester",
                "model_id": cls.tester_model.id,
                "perm_read": 1,
                "perm_write": 1,
                "perm_create": 1,
                "perm_unlink": 1,
            }
        )
        cls.dep_admin = cls.env.ref("hr.dep_administration")
        cls.tier_level = cls.env["tier.level"]

        # Create users:
        group_ids = cls.env.ref("base.group_system").ids
        cls.test_user_1 = cls.env["res.users"].create(
            {"name": "John", "login": "test1", "groups_id": [(6, 0, group_ids)]}
        )
        cls.test_user_2 = cls.env["res.users"].create(
            {"name": "Mike", "login": "test2"}
        )
        # Create tier definitions:
        cls.tier_def_obj = cls.env["tier.definition"]
        cls.tier_def = cls.tier_def_obj.create(
            {
                "model_id": cls.tester_model.id,
                "review_type": "expression",
                "reviewer_expression": "rec.user_id.department_id.find_reviewer_level(level=1)",
                "definition_domain": "[('test_field', '>', 1.0)]",
            }
        )

        cls.test_record = cls.test_model.create({"test_field": 2.5})

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    def test_01_tier_level(self):
        # Add tier level in department
        self.test_user_2.department_id = self.dep_admin.id
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
        self.test_user_2.department_id = self.dep_admin.id
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
