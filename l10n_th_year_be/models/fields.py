from odoo import fields

from .res_users import YEAR_FORMAT_BE, YEAR_FORMAT_CE, YEAR_FORMAT_SYSTEM

VALID_YEAR_FORMATS = {YEAR_FORMAT_SYSTEM, YEAR_FORMAT_CE, YEAR_FORMAT_BE}


def _description_year_format(field):
    field_args = field.__dict__.get("_args__") or {}
    year_format = field.__dict__.get("year_format") or field_args.get("year_format")
    return year_format if year_format in VALID_YEAR_FORMATS else None


for field_class in (fields.Date, fields.Datetime):
    field_class.year_format = None
    field_class._description_year_format = property(_description_year_format)
    if ("year_format", "_description_year_format") not in field_class.description_attrs:
        field_class.description_attrs.append(
            ("year_format", "_description_year_format")
        )
