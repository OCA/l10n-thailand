from odoo import models

from .res_users import AUTO_CONVERT_100_YEARS, AUTO_CONVERT_PARAM


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def _get_l10n_th_year_be_session_info(self):
        auto_convert_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(AUTO_CONVERT_PARAM, default=AUTO_CONVERT_100_YEARS)
        )
        if auto_convert_value not in {"half_offset", "100_years", "200_years"}:
            auto_convert_value = AUTO_CONVERT_100_YEARS
        return {
            "l10n_th_date_year_format": (
                self.env.user._get_l10n_th_effective_date_year_format()
            ),
            "l10n_th_date_auto_convert_be_input": auto_convert_value,
        }

    def session_info(self):
        session_info = super().session_info()
        session_info.update(self._get_l10n_th_year_be_session_info())
        return session_info
