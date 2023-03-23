# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.l10n_th_account_asset_management.tests.test_account_asset_management import (
    TestAssetManagementThailand,
)
from odoo.addons.purchase_work_acceptance.tests.test_purchase_work_acceptance import (
    TestPurchaseWorkAcceptance,
)


@tagged("post_install", "-at_install")
class TestGovAssetManagementThailand(
    TestAssetManagementThailand, TestPurchaseWorkAcceptance
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.remove_model = cls.env["account.asset.remove"]
        # Create asset profile low value
        cls.profile_low_value = cls.car5y.copy()
        cls.profile_low_value.write(
            {
                "method_number": 0,
                "account_asset_id": cls.account_expense.id,
            }
        )
        # Add permission analytic
        cls.env.user.write(
            {
                "groups_id": [
                    (4, cls.env.ref("analytic.group_analytic_accounting").id),
                    (4, cls.env.ref("analytic.group_analytic_tags").id),
                ],
            }
        )
        cls.analytic1 = cls.env.ref("analytic.analytic_administratif")
        cls.analytic_tag1 = cls.env.ref("analytic.tag_contract")

    def test_01_flow_purchase_to_asset(self):
        self.env.company.asset_move_line_analytic = True
        # Create Purchase Order
        qty = 42.0
        purchase_order = self._create_purchase_order(qty, self.product_product)
        purchase_order.button_confirm()
        self.assertEqual(purchase_order.state, "purchase")
        self.assertEqual(purchase_order.incoming_picking_count, 1)
        # Create Work Acceptance
        work_acceptance = self._create_work_acceptance(qty, purchase_order)
        work_acceptance.button_accept()
        self.assertEqual(work_acceptance.state, "accept")
        self.assertEqual(purchase_order.wa_count, 1)
        # Received Products
        picking = purchase_order.picking_ids[0]
        self.assertEqual(len(picking.move_ids_without_package), 1)
        with Form(picking) as p:
            p.wa_id = work_acceptance
        p.save()
        with self.assertRaises(ValidationError):
            picking.move_ids_without_package[0].quantity_done = 30.0
            picking.button_validate()
        picking.move_ids_without_package[0].quantity_done = 42.0
        picking.button_validate()
        # Can't set to draft wa when you validate picking
        with self.assertRaises(UserError):
            work_acceptance.button_draft()
        # Create Vendor Bill
        f = Form(self.env["account.move"].with_context(default_move_type="in_invoice"))
        f.partner_id = purchase_order.partner_id
        f.purchase_id = purchase_order
        invoice = f.save()
        invoice.wa_id = work_acceptance
        invoice_line = invoice.invoice_line_ids[0]
        with self.assertRaises(ValidationError):
            invoice_line.with_context(check_move_validity=False).write(
                {"quantity": 6.0}
            )
            invoice.action_post()  # Warn when quantity not equal to WA
        invoice_line.quantity = qty
        # Add asset profile in invoice
        invoice_line.asset_profile_id = self.car5y.id
        self.assertEqual(invoice.state, "draft")
        invoice.invoice_date = invoice.date
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        new_asset = self.env["account.asset"].search([("code", "=", invoice.name)])
        self.assertEqual(new_asset.state, "draft")
        # Check remove with state draft, it should error
        with self.assertRaises(UserError):
            new_asset.action_remove_multi_assets()
        new_asset.validate()
        # Remove with normal asset
        self.assertEqual(new_asset.state, "open")
        action = new_asset.action_remove_multi_assets()
        self.assertEqual(
            action["view_id"],
            self.env.ref(
                "l10n_th_gov_account_asset_management.account_asset_remove_view_form"
            ).id,
        )
        wiz_ctx = {"active_id": new_asset.id, "active_ids": new_asset.ids}
        wiz = self.remove_model.with_context(**wiz_ctx).create(
            {
                "date_remove": fields.Date.today(),
                "sale_value": 0.0,
                "posting_regime": "residual_value",
                "account_residual_value_id": self.account_expense.id,
                "remove_reason": "Reason Remove",
            }
        )
        wiz.remove()
        # Test remove multi asset
        wiz.remove_multi_assets()

    def test_02_flow_purchase_to_asset_low_value(self):
        self.env.company.asset_move_line_analytic = True
        # Create Purchase Order
        qty = 42.0
        purchase_order = self._create_purchase_order(qty, self.product_product)
        purchase_order.button_confirm()
        self.assertEqual(purchase_order.state, "purchase")
        self.assertEqual(purchase_order.incoming_picking_count, 1)
        # Create Work Acceptance
        work_acceptance = self._create_work_acceptance(qty, purchase_order)
        work_acceptance.button_accept()
        self.assertEqual(work_acceptance.state, "accept")
        self.assertEqual(purchase_order.wa_count, 1)
        # Received Products
        picking = purchase_order.picking_ids[0]
        self.assertEqual(len(picking.move_ids_without_package), 1)
        with Form(picking) as p:
            p.wa_id = work_acceptance
        p.save()
        with self.assertRaises(ValidationError):
            picking.move_ids_without_package[0].quantity_done = 30.0
            picking.button_validate()
        picking.move_ids_without_package[0].quantity_done = 42.0
        picking.button_validate()
        # Can't set to draft wa when you validate picking
        with self.assertRaises(UserError):
            work_acceptance.button_draft()
        # Create Vendor Bill
        f = Form(self.env["account.move"].with_context(default_move_type="in_invoice"))
        f.partner_id = purchase_order.partner_id
        f.purchase_id = purchase_order
        invoice = f.save()
        invoice.wa_id = work_acceptance
        invoice_line = invoice.invoice_line_ids[0]
        with self.assertRaises(ValidationError):
            invoice_line.with_context(check_move_validity=False).write(
                {"quantity": 6.0}
            )
            invoice.action_post()  # Warn when quantity not equal to WA
        invoice_line.quantity = qty
        # Add asset profile in invoice
        invoice_line.asset_profile_id = self.profile_low_value.id
        self.assertEqual(invoice.state, "draft")
        invoice.invoice_date = invoice.date
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        new_asset = self.env["account.asset"].search([("code", "=", invoice.name)])
        self.assertEqual(new_asset.state, "draft")
        # Check remove with state draft, it should error
        with self.assertRaises(UserError):
            new_asset.action_remove_multi_assets()
        new_asset.validate()

        # Test remove with low value and normal asset
        normal_asset = new_asset.copy()
        with Form(normal_asset) as asset:
            asset.profile_id = self.car5y
        normal_asset.validate()
        all_asset = normal_asset + new_asset
        with self.assertRaises(UserError):
            all_asset.action_remove_multi_assets()

        # Remove with low asset
        self.assertEqual(new_asset.state, "open")
        action = new_asset.action_remove_multi_assets()
        self.assertEqual(
            action["view_id"],
            self.env.ref(
                "l10n_th_gov_account_asset_management.asset_low_value_remove_form"
            ).id,
        )

    def test_03_config_analytic(self):
        self.env.company.asset_move_line_analytic = True
        asset = self.asset_model.create(
            {
                "name": "test asset analytic",
                "account_analytic_id": self.analytic1.id,
                "analytic_tag_ids": [(4, self.analytic_tag1.id)],
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
        # Test create move and check move line must accounting with analytic, tags all line
        move_id = lines[0].create_move()
        move = self.env["account.move"].browse(move_id)
        for line in move.line_ids:
            self.assertEqual(line.analytic_account_id, self.analytic1)
            self.assertEqual(line.analytic_tag_ids, self.analytic_tag1)
