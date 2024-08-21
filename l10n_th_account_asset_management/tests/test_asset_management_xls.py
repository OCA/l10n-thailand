# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from freezegun import freeze_time

from odoo.tests.common import TransactionCase


class TestAssetManagementXlsThailand(TransactionCase):
    @classmethod
    @freeze_time("2020-02-01")
    def setUpClass(cls):
        super().setUpClass()
        cls.xls_report_name = "account_asset_management.asset_report_xls"
        cls.wiz_model = cls.env["wiz.account.asset.report"]
        group_fa = cls.env["account.asset.group"].create(
            {
                "name": "Fixed Assets",
                "code": "FA",
            }
        )

        wiz_vals = {
            "asset_group_id": group_fa.id,
            "date_from": "2020-01-01",
            "date_to": "2020-12-31",
        }
        cls.xls_report = cls.wiz_model.create(wiz_vals)
        cls.report_action = cls.xls_report.xls_export()

    @freeze_time("2020-02-01")
    def test_01_action_xls(self):
        """Check report XLS action and generate report"""
        self.assertGreaterEqual(
            self.report_action.items(),
            {
                "type": "ir.actions.report",
                "report_type": "xlsx",
                "report_name": self.xls_report_name,
            }.items(),
        )
        model = self.env["report.%s" % self.report_action["report_name"]].with_context(
            active_model=self.xls_report._name, **self.report_action["context"]
        )
        model.create_xlsx_report(self.xls_report.ids, data=self.report_action["data"])
