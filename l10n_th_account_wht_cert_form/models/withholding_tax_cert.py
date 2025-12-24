# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from dateutil.relativedelta import relativedelta

from odoo import _, models


class WithholdingTaxCert(models.Model):
    _inherit = "withholding.tax.cert"

    def _get_report_base_filename(self):
        self.ensure_one()
        return _("WHT Certificates - {name}").format(name=self.display_name or False)

    def _compute_desc_type_other(self, lines, ttype, income_type):
        base_type_other = lines.filtered(
            lambda l: l.wht_cert_income_type in [income_type]
        ).mapped(ttype)
        base_type_other = [x or "" for x in base_type_other]
        desc = ", ".join(base_type_other)
        return desc

    def _group_wht_line(self, lines):
        groups = self.env["withholding.tax.cert.line"].read_group(
            domain=[("id", "in", lines.ids)],
            fields=["wht_cert_income_type", "base", "amount"],
            groupby=["wht_cert_income_type"],
            lazy=False,
        )
        return groups

    # NOTE: Add this method for < V15 only
    def _get_period_be(self, date_start, date_end):
        month = year = "-"
        date_start = (date_start + relativedelta(years=543)).strftime("%m-%Y")
        date_end = (date_end + relativedelta(years=543)).strftime("%m-%Y")
        if date_start == date_end:
            m, year = date_end.split("-")
            month = self._get_month_thai(m)
        return [month, year]

    def _get_month_thai(self, month):
        month_thai = {
            "01": "มกราคม",
            "02": "กุมภาพันธ์",
            "03": "มีนาคม",
            "04": "เมษายน",
            "05": "พฤษภาคม",
            "06": "มิถุนายน",
            "07": "กรกฎาคม",
            "08": "สิงหาคม",
            "09": "กันยายน",
            "10": "ตุลาคม",
            "11": "พฤศจิกายน",
            "12": "ธันวาคม",
        }
        return month_thai[month]
