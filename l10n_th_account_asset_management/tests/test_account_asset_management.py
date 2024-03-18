# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase


@tagged("post_install", "-at_install")
class TestAssetManagementThailand(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_model = cls.env["account.account"]
        cls.asset_model = cls.env["account.asset"]
        cls.asset_parent_model = cls.env["account.asset.parent"]
        cls.asset_remove_model = cls.env["account.asset.remove"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        cls.asset_transfer_model = cls.env["account.asset.transfer"]
        # Create Journal Transfer
        cls.misc_transfer_journal = cls.env["account.journal"].create(
            {
                "name": "Misc Transfer Journal - (test)",
                "code": "MiscT-Test",
                "type": "general",
            }
        )
        # Create expense account
        cls.account_expense = cls.account_model.create(
            {
                "code": "TEST99999.Expense",
                "name": "Account - Test Expense",
                "account_type": "expense",
            }
        )
        # Create asset account
        cls.account_asset = cls.account_model.create(
            {
                "code": "TEST99999.Asset",
                "name": "Account - Test Asset",
                "account_type": "asset_current",
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
        # Profile Under Construction
        cls.profile_auc = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.account_expense.id,
                "account_asset_id": cls.account_asset.id,
                "account_depreciation_id": cls.account_asset.id,
                "journal_id": cls.purchase_journal.id,
                "transfer_journal_id": cls.misc_transfer_journal.id,
                "asset_product_item": True,
                "name": "Asset Under Construction",
                "method_time": "year",
                "method_number": 0,
                "method_period": "year",
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
        asset.invalidate_recordset()
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
        asset.invalidate_recordset()
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

    def test_04_parent_asset(self):
        parent_asset = self.asset_parent_model.create([{"name": "Parent Test"}])
        self.assertNotEqual(parent_asset.code, "/")
        # Check display name of parent asset must show code
        display_name = "[{}] {}".format(parent_asset.code, parent_asset.name)
        self.assertEqual(parent_asset.display_name, display_name)
        # Check search with code 'ASP' and != 'ASP'
        result_search = parent_asset.name_search("ASP")
        self.assertTrue(result_search)
        result_search = parent_asset.name_search("ASP", operator="!=")
        self.assertEqual(result_search, [])
        # Parent asset link to asset (0 asset, 1 parent)
        action = parent_asset.action_view_assets()
        self.assertEqual(action, {"type": "ir.actions.act_window_close"})
        # Create asset and link to parent asset (1 asset, 1 parent)
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
                "parent_id": parent_asset.id,
            }
        )
        self.assertEqual(asset.parent_id, parent_asset)
        action = parent_asset.action_view_assets()
        self.assertEqual(action["views"][0][1], "form")
        self.assertEqual(len(parent_asset.asset_ids), 1)
        # Create asset and link to parent asset (2 asset, 1 parent)
        asset = self.asset_model.create(
            {
                "name": "test asset2",
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
                "parent_id": parent_asset.id,
            }
        )
        action = parent_asset.action_view_assets()
        self.assertEqual(len(parent_asset.asset_ids), 2)
        self.assertEqual(action["domain"][0][2], parent_asset.asset_ids.ids)

    def test_05_substate_asset_remove(self):
        asset = self.asset_model.create(
            {
                "name": "test asset2",
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
        asset.validate()
        remove_model = self.asset_remove_model.with_context(
            active_id=asset.id, active_ids=asset.ids
        )
        with Form(remove_model) as f:
            f.posting_regime = "residual_value"
            f.account_residual_value_id = self.account_expense
        wiz = f.save()
        # Defualt substate is check remove first line
        self.assertTrue(wiz.asset_sub_state_id)
        substate_default = wiz.asset_sub_state_id
        # Test remove without substate
        wiz.asset_sub_state_id = False
        wiz.remove()
        # state asset change to remove and substate will default
        self.assertEqual(asset.state, "removed")
        self.assertEqual(asset.asset_sub_state_id, substate_default)

    def test_06_substate_asset_transfer(self):
        asset_auc = self.asset_model.create(
            {
                "name": "test asset2",
                "profile_id": self.profile_auc.id,
                "purchase_value": 1828,
                "salvage_value": 1,
                "date_start": "2019-07-07",
                "method_time": "year",
                "method": "linear-limit",
                "method_number": 0,
                "method_period": "year",
                "prorata": True,
                "days_calc": True,
            }
        )
        asset_auc.validate()
        # Create Asset Transfer
        transfer_form = Form(
            self.asset_transfer_model.with_context(active_ids=asset_auc.ids)
        )
        transfer_wiz = transfer_form.save()
        with transfer_form.to_asset_ids.new() as to_asset:
            to_asset.asset_name = "Asset 1"
            to_asset.asset_profile_id = self.car5y
            to_asset.quantity = 1
            to_asset.price_unit = 1828
        transfer_form.save()
        self.assertTrue(transfer_wiz.asset_sub_state_id)
        transfer_wiz.transfer()
        # Source Asset change state to removed and substate equal transfer substate
        self.assertEqual(asset_auc.state, "removed")
        self.assertEqual(asset_auc.asset_sub_state_id, transfer_wiz.asset_sub_state_id)
