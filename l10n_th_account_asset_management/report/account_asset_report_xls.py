# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


class AssetReportXlsx(models.AbstractModel):
    _inherit = "report.account_asset_management.asset_report_xls"

    def _get_asset_template(self):
        res = super()._get_asset_template()
        res.update(
            {
                "profile": {
                    "header": {"type": "string", "value": _("Asset Profile")},
                    "asset": {
                        "type": "string",
                        "value": self._render("asset.profile_id.name"),
                    },
                    "width": 40,
                },
                "depreciation_rate": {
                    "header": {
                        "type": "string",
                        "value": _("Depreciation Rate"),
                        "format": FORMATS["format_theader_yellow_right"],
                    },
                    "asset": {
                        "type": "number",
                        "value": self._render("asset.depreciation_rate"),
                        "format": FORMATS["format_tcell_amount_right"],
                    },
                    "width": 18,
                },
            }
        )
        return res
