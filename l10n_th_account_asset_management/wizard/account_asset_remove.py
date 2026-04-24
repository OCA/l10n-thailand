# Copyright 2023 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models


class AccountAssetRemove(models.TransientModel):
    _inherit = "account.asset.remove"

    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Taxes",
        domain="[('type_tax_use', '=', 'sale')]",
        check_company=True,
    )
    asset_sub_state_id = fields.Many2one(
        comodel_name="account.asset.sub.state",
        string="Sub-Status",
        domain="[('removed', '=', True), '|', ('company_id', '=', False), "
        "('company_id', '=', company_id)]",
        default=lambda self: self.env["account.asset.sub.state"].search(
            [
                ("removed", "=", True),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        ),
        check_company=True,
    )

    def _get_inv_lines(self, assets):
        return [
            Command.create(
                {
                    "name": asset.name,
                    "account_id": self.account_sale_id.id,
                    "price_unit": self.sale_value,
                    "quantity": 1.0,
                    "tax_ids": [Command.set(self.tax_ids.ids)],
                }
            )
            for asset in assets
        ]

    def _get_invoice(self, invoice_line_dict):
        return {
            "move_type": "out_invoice",
            "invoice_date": self.date_remove,
            "company_id": self.company_id.id,
            "invoice_line_ids": invoice_line_dict,
        }

    def _create_sale_invoice(self, assets):
        """Create one draft Customer Invoice with one line per asset.

        Only runs when tax_ids is set, sale_value > 0, and posting regime
        is gain_loss_on_sale. Each line carries asset_id so the invoice is
        discoverable via asset.account_move_line_ids for every asset.
        """
        currency = self.company_id.currency_id
        move_model = self.env["account.move"]
        if not (
            self.tax_ids
            and currency.compare_amounts(self.sale_value, 0) > 0
            and self.posting_regime == "gain_loss_on_sale"
        ):
            return move_model

        invoice_line_dict = self._get_inv_lines(assets)
        invoice_dict = self._get_invoice(invoice_line_dict)
        move = move_model.with_context(default_move_type="out_invoice").create(
            invoice_dict
        )
        assets.write({"sale_invoice_id": move.id})
        return move

    def remove(self):
        res = super().remove()
        asset_ids = self.env.context.get("active_ids", [])
        assets = self.env["account.asset"].browse(asset_ids)
        asset_sub_state = self.asset_sub_state_id
        if not asset_sub_state:
            asset_sub_state = self.env["account.asset.sub.state"].search(
                [
                    ("removed", "=", True),
                    "|",
                    ("company_id", "=", False),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
        if asset_sub_state:
            assets.write({"asset_sub_state_id": asset_sub_state.id})
        self._create_sale_invoice(assets)
        return res
