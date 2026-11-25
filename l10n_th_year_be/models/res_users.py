from odoo import fields, models

YEAR_FORMAT_PARAM = "l10n_th_year_be.year_format"
AUTO_CONVERT_PARAM = "l10n_th_year_be.auto_convert_be_input"
YEAR_FORMAT_CE = "ce"
YEAR_FORMAT_BE = "be"
YEAR_FORMAT_SYSTEM = "system"
AUTO_CONVERT_HALF_OFFSET = "half_offset"
AUTO_CONVERT_100_YEARS = "100_years"
AUTO_CONVERT_200_YEARS = "200_years"
BUDDHIST_ERA_OFFSET = 543


def format_buddhist_era_year(formatted_value, value):
    if not formatted_value or not value:
        return formatted_value
    return formatted_value.replace(
        str(value.year), str(value.year + BUDDHIST_ERA_OFFSET)
    )


YEAR_FORMAT_SELECTION = [
    (YEAR_FORMAT_CE, "Common Era (CE)"),
    (YEAR_FORMAT_BE, "Buddhist Era (BE)"),
]

USER_YEAR_FORMAT_SELECTION = [
    (YEAR_FORMAT_SYSTEM, "System Default"),
    *YEAR_FORMAT_SELECTION,
]

AUTO_CONVERT_SELECTION = [
    (
        AUTO_CONVERT_HALF_OFFSET,
        "half of 543 years",
    ),
    (
        AUTO_CONVERT_100_YEARS,
        "100 years",
    ),
    (
        AUTO_CONVERT_200_YEARS,
        "200 years",
    ),
]


class ResUsers(models.Model):
    _inherit = "res.users"

    l10n_th_date_year_format = fields.Selection(
        selection=USER_YEAR_FORMAT_SELECTION,
        string="Date Year Format",
        default=YEAR_FORMAT_SYSTEM,
        required=True,
        help="Choose how years are displayed.",
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["l10n_th_date_year_format"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["l10n_th_date_year_format"]

    def _get_l10n_th_effective_date_year_format(
        self, element_year_format=None, field_year_format=None
    ):
        self.ensure_one()
        if element_year_format in (YEAR_FORMAT_CE, YEAR_FORMAT_BE):
            return element_year_format
        if field_year_format in (YEAR_FORMAT_CE, YEAR_FORMAT_BE):
            return field_year_format
        if (
            self.l10n_th_date_year_format
            and self.l10n_th_date_year_format != YEAR_FORMAT_SYSTEM
        ):
            return self.l10n_th_date_year_format
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(YEAR_FORMAT_PARAM, default=YEAR_FORMAT_CE)
        )
