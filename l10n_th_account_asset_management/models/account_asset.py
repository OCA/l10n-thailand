# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountAsset(models.Model):
    _name = "account.asset"
    _inherit = ["account.asset", "mail.thread", "mail.activity.mixin"]

    image = fields.Binary(
        attachment=True,
        help="This field holds the photo of the asset.",
    )
    depreciation_rate = fields.Float(
        compute="_compute_depreciation_rate",
        string="Depreciation Rate (%)",
        store=True,
    )

    @api.depends("method_number", "method")
    def _compute_depreciation_rate(self):
        for asset in self:
            asset.depreciation_rate = 0
            if asset.method in ["linear", "linear-limit"] and asset.method_number != 0:
                asset.depreciation_rate = 100.0 / asset.method_number

    def _xls_l10n_th_fields(self):
        return [
            "account",
            "number",
            "name",
            "profile",
            "code",
            "date_start",
            "purchase_value",
            "salvage_value",
            "depreciation_base",
            "depreciation_rate",
            "period_start_value",
            "period_depr",
            "period_end_depr",
            "period_end_value",
            "state",
            "date_remove",
        ]

    @api.model
    def _xls_acquisition_fields(self):
        return self._xls_l10n_th_fields()

    @api.model
    def _xls_active_fields(self):
        return self._xls_l10n_th_fields()

    @api.model
    def _xls_removal_fields(self):
        return self._xls_l10n_th_fields()

    def validate(self):
        res = super().validate()
        for asset in self:
            if (
                asset.method_number > 0
                and asset.company_currency_id.compare_amounts(
                    asset.value_residual, asset.salvage_value
                )
                == 0
            ):
                asset.state = "close"
        return res

    def _compute_depreciation_amount_per_fiscal_year(
        self, table, line_dates, depreciation_start_date, depreciation_stop_date
    ):
        """Override _compute_depreciation_amount_per_fiscal_year for Thai"""
        digits = self.env["decimal.precision"].precision_get("Account")
        fy_residual_amount = self.depreciation_base
        i_max = len(table) - 1
        asset_sign = self.depreciation_base >= 0 and 1 or -1
        day_amount = 0.0
        if self.days_calc:
            days = (depreciation_stop_date - depreciation_start_date).days + 1
            purchase_value = self.purchase_value or 0.0
            salvage_value = self.salvage_value or 0.0
            # remaining last line should value equal salvage value (For Thai)
            day_amount = (purchase_value - salvage_value) / days

        for i, entry in enumerate(table):
            if self.method_time == "year":
                year_amount = self._compute_year_amount(
                    fy_residual_amount,
                    depreciation_start_date,
                    depreciation_stop_date,
                    entry,
                )
                if self.method_period == "year":
                    period_amount = year_amount
                elif self.method_period == "quarter":
                    period_amount = year_amount / 4
                elif self.method_period == "month":
                    period_amount = year_amount / 12
                if i == i_max:
                    if self.method in ["linear-limit", "degr-limit"]:
                        fy_amount = fy_residual_amount - self.salvage_value
                    else:
                        fy_amount = fy_residual_amount
                else:
                    firstyear = i == 0 and True or False
                    fy_factor = self._get_fy_duration_factor(entry, firstyear)
                    fy_amount = year_amount * fy_factor
                if asset_sign * (fy_amount - fy_residual_amount) > 0:
                    fy_amount = fy_residual_amount
                period_amount = round(period_amount, digits)
                fy_amount = round(fy_amount, digits)
            else:
                fy_amount = False
                if self.method_time == "number":
                    number = self.method_number
                else:
                    number = len(line_dates)
                period_amount = round(self.depreciation_base / number, digits)
            entry.update(
                {
                    "period_amount": period_amount,
                    "fy_amount": fy_amount,
                    "day_amount": day_amount,
                }
            )
            if self.method_time == "year":
                fy_residual_amount -= fy_amount
                if round(fy_residual_amount, digits) == 0:
                    break
        i_max = i
        table = table[: i_max + 1]
        return table
