# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from odoo.addons.stock_request.tests.test_stock_request import TestStockRequest


@tagged("post_install", "-at_install")
class TestThaiGovStockRequest(TestStockRequest):
    def setUp(self):
        super().setUp()

    def test_01_defaults_order(self):
        self.env.company.stock_request_allow_virtual_loc = True
        self.customer_location = self.env["stock.location"].search(
            [
                ("company_id", "in", (self.env.company.id, False)),
                ("usage", "=", "customer"),
            ],
            limit=1,
        )
        vals = {}
        order = (
            self.request_order.with_user(self.stock_request_manager)
            .with_context(company_id=self.main_company.id)
            .create(vals)
        )
        # Location will default customer location
        self.assertEqual(order.requested_by, self.stock_request_manager)
        self.assertEqual(order.warehouse_id, self.warehouse)
        self.assertEqual(order.location_id, self.customer_location)
