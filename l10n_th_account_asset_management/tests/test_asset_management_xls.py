# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged

from odoo.addons.account_asset_management.tests.test_asset_management_xls import (
    TestAssetManagementXls,
)


@tagged("post_install", "-at_install")
class TestAssetManagementXlsThailand(TestAssetManagementXls):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
