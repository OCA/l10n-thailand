from odoo import api, fields, models

from .res_users import (
    AUTO_CONVERT_100_YEARS,
    AUTO_CONVERT_PARAM,
    AUTO_CONVERT_SELECTION,
    YEAR_FORMAT_CE,
    YEAR_FORMAT_PARAM,
    YEAR_FORMAT_SELECTION,
)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.model
    def _sanitize_l10n_th_date_auto_convert_be_input_param(self):
        valid_values = {value for value, _label in AUTO_CONVERT_SELECTION}
        param = self.env["ir.config_parameter"].sudo()
        current_value = param.get_param(AUTO_CONVERT_PARAM)
        if current_value not in valid_values:
            param.set_param(AUTO_CONVERT_PARAM, AUTO_CONVERT_100_YEARS)

    @api.model
    def default_get(self, fields_list):
        self._sanitize_l10n_th_date_auto_convert_be_input_param()
        return super().default_get(fields_list)

    l10n_th_date_year_format = fields.Selection(
        selection=YEAR_FORMAT_SELECTION,
        string="Date Year Format",
        default=YEAR_FORMAT_CE,
        required=True,
        config_parameter=YEAR_FORMAT_PARAM,
        help="Choose the default year format to display.",
    )

    l10n_th_date_auto_convert_be_input = fields.Selection(
        selection=AUTO_CONVERT_SELECTION,
        string="Auto-correct BE Manual Input",
        default=AUTO_CONVERT_100_YEARS,
        required=True,
        config_parameter=AUTO_CONVERT_PARAM,
        help=(
            "Threshold value for detecting user input year as Buddhist Era "
            "(BE) or Common Era (CE) for converting BE to CE before saving "
            "the value."
        ),
    )
