from odoo import api, fields, models

from .res_users import YEAR_FORMAT_BE, format_buddhist_era_year


class DateConverter(models.AbstractModel):
    _inherit = "ir.qweb.field.date"

    @api.model
    def get_available_options(self):
        options = super().get_available_options()
        options.update(
            year_format=dict(
                type="selection",
                selection=[
                    ("system", "User/System Default"),
                    ("ce", "CE"),
                    ("be", "BE"),
                ],
                string="Year format",
            )
        )
        return options

    @api.model
    def value_to_html(self, value, options):
        formatted_value = super().value_to_html(value, options)
        year_format = self.env.user._get_l10n_th_effective_date_year_format(
            element_year_format=options.get("year_format")
        )
        if year_format != YEAR_FORMAT_BE:
            return formatted_value
        if isinstance(value, str):
            value = fields.Date.from_string(value)
        return format_buddhist_era_year(formatted_value, value)


class DateTimeConverter(models.AbstractModel):
    _inherit = "ir.qweb.field.datetime"

    @api.model
    def get_available_options(self):
        options = super().get_available_options()
        options.update(
            year_format=dict(
                type="selection",
                selection=[
                    ("system", "User/System Default"),
                    ("ce", "CE"),
                    ("be", "BE"),
                ],
                string="Year format",
            )
        )
        return options

    @api.model
    def value_to_html(self, value, options):
        formatted_value = super().value_to_html(value, options)
        year_format = self.env.user._get_l10n_th_effective_date_year_format(
            element_year_format=options.get("year_format")
        )
        if year_format != YEAR_FORMAT_BE:
            return formatted_value
        if isinstance(value, str):
            value = fields.Datetime.from_string(value)
        if value:
            converter = (
                self.with_context(tz=options["tz_name"])
                if options.get("tz_name")
                else self
            )
            value = fields.Datetime.context_timestamp(converter, value)
        return format_buddhist_era_year(formatted_value, value)
