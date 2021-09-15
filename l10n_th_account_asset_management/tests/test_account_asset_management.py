# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAssetManagementThailand(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        cls.car5y = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
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
                "method_period": "month",
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
