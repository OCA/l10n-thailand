# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAssetManagementThailand(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_model = cls.env["account.account"]
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        # Create expense account
        account_type_expense = cls.env.ref("account.data_account_type_expenses")
        cls.account_expense = cls.account_model.create(
            {
                "code": "TEST99999-Expense",
                "name": "Account - Test Expense",
                "user_type_id": account_type_expense.id,
            }
        )
        # Create asset account
        account_type_asset = cls.env.ref("account.data_account_type_current_assets")
        cls.account_asset = cls.account_model.create(
            {
                "code": "TEST99999-Asset",
                "name": "Account - Test Asset",
                "user_type_id": account_type_asset.id,
            }
        )
        # Create Journal Purchase
        cls.purchase_journal = cls.env["account.journal"].create(
            {
                "name": "Purchase Journal - (test)",
                "code": "TEST-P",
                "type": "purchase",
            }
        )
        cls.car5y = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.account_expense.id,
                "account_asset_id": cls.account_asset.id,
                "account_depreciation_id": cls.account_asset.id,
                "journal_id": cls.purchase_journal.id,
                "name": "Cars - 5 Years",
                "method_time": "year",
                "method_number": 5,
                "method_period": "month",
            }
        )

    def test_01_calc_days_linear_limit(self):
        """Check remaining value last line must equal salvage_value."""
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1828,
                "salvage_value": 1,
                "date_start": "2019-07-07",
                "method_time": "year",
                "method": "linear-limit",
                "method_number": 5,
                "method_period": "month",
                "prorata": True,
                "days_calc": True,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        self.assertEqual(asset.depreciation_rate, 20.0)
        # check values in the depreciation board
        self.assertEqual(len(asset.depreciation_line_ids), 62)
        self.assertAlmostEqual(
            asset.depreciation_line_ids[-1].remaining_value, 1.00, places=2
        )

    def test_02_auto_close_asset(self):
        asset = self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1828,
                "salvage_value": 1,
                "date_start": "2019-07-07",
                "method_time": "year",
                "method": "linear-limit",
                "method_number": 5,
                "method_period": "year",
                "prorata": True,
                "days_calc": True,
            }
        )
        asset.compute_depreciation_board()
        asset.refresh()
        self.assertEqual(asset.state, "draft")
        asset.validate()
        self.assertEqual(asset.state, "open")
        lines = asset.depreciation_line_ids.filtered(lambda x: not x.init_entry)
        for asset_line in lines:
            asset_line.create_move()
        self.assertEqual(asset.state, "close")
        # when validate again, state must change to close
        asset.set_to_draft()
        self.assertEqual(asset.state, "draft")
        asset.validate()
        self.assertEqual(asset.state, "close")

    def test_03_asset_removal_with_value_residual(self):
        """Asset removal with value residual"""
        asset = self.asset_model.create(
            {
                "name": "test asset removal",
                "profile_id": self.car5y.id,
                "purchase_value": 1000,
                "salvage_value": 0,
                "date_start": "2019-01-01",
                "method_time": "number",
                "method_number": 10,
                "method_period": "month",
                "prorata": False,
            }
        )
        asset.compute_depreciation_board()
        asset.validate()
        lines = asset.depreciation_line_ids.filtered(lambda x: not x.init_entry)
        self.assertEqual(len(lines), 10)
        last_line = lines[-1]
        last_line["amount"] = last_line["amount"] - 0.10
        for asset_line in lines:
            asset_line.create_move()
        self.assertEqual(asset.value_residual, 0.10)
        asset.compute_depreciation_board()
        lines = asset.depreciation_line_ids.filtered(lambda x: not x.init_entry)
        self.assertEqual(len(lines), 11)
        last_line = lines[-1]
        self.assertEqual(last_line.amount, 0.10)
        last_line.create_move()
        self.assertEqual(asset.value_residual, 0)
        self.assertEqual(asset.state, "close")
