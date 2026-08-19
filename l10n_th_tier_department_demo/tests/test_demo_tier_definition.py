# Copyright 2025 Accsumana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDemoTierDefinition(TransactionCase):
    """Test that demo tier definitions are loaded correctly."""

    def test_expense_tier_definitions_exist(self):
        """Expense tier definitions should be created (inactive by default)."""
        tier_def = self.env.ref(
            "l10n_th_tier_department_demo.expense_gov_tier_definition_1",
            raise_if_not_found=False,
        )
        self.assertTrue(tier_def)
        self.assertFalse(tier_def.active)
        self.assertEqual(tier_def.review_type, "expression")

    def test_purchase_request_tier_definitions_exist(self):
        """Purchase request tier definitions should be created."""
        tier_def = self.env.ref(
            "l10n_th_tier_department_demo.purchase_request_gov_tier_definition_1",
            raise_if_not_found=False,
        )
        self.assertTrue(tier_def)
        self.assertFalse(tier_def.active)
        self.assertEqual(tier_def.review_type, "expression")
