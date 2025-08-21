# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from collections import defaultdict

from odoo import models
from odoo.exceptions import UserError


class WithholdingTaxReportText(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_withholding_tax_text"
    _inherit = [
        "report.l10n_th_account_tax_report.report_withholding_tax",
        "thai.utils",
    ]
    _description = "Thai Withholding Tax Report Text"

    def _convert_wht_tax_payer(self, tax_payer):
        if tax_payer == "withholding":
            return 1
        if tax_payer == "paid_continue":
            return 2
        return 3  # Paid One Time

    def _prepare_display_wht_textfile(self, record, prefix=""):
        args = defaultdict(str)
        for field in record:
            key = f"{prefix}{field}" if prefix else field
            if field == "cert_date":
                args[key] = self.format_thai_date(
                    record[field],
                    month_format="numeric",
                    format_date="{day:02d}{month}{year}",
                )
            elif field in ["base", "amount"]:
                args[key] = f"{record[field]:,.2f}"
            elif field == "cert_tax_payer":
                args[key] = self._convert_wht_tax_payer(record[field])
            elif field == "wht_percent":
                args[key] = int(record[field])
            else:
                args[key] = record[field] or ""
        return args

    def _extract_fields_from_template(self, wht_textfile_format):
        return re.findall(r"%\((.*?)\)s", wht_textfile_format)

    def _get_wht_group_cert(self, wht_report_data):
        grouped = defaultdict(list)
        wht_groupby_cert = []

        for row in wht_report_data:
            grouped[row["cert_id"]].append(row)

        for idx, (cert_id, rows) in enumerate(grouped.items(), start=1):
            first_row = rows[0]
            cert_cancel = first_row["cert_cancel"]

            wht_groupby_cert.append(
                {
                    # Header
                    "row_number": idx,
                    "cert_cancel": cert_cancel,
                    "cert_date": first_row["cert_date"],
                    "cert_date_str": first_row["cert_date_str"],
                    "cert_name": first_row["cert_name"],
                    "cert_tax_payer": first_row["cert_tax_payer"],
                    "cert_tax_payer_display": first_row["cert_tax_payer_display"],
                    "cert_tax_payer_code": first_row["cert_tax_payer_code"],
                    "partner_id": first_row["partner_id"],
                    "partner_name": first_row["partner_name"],
                    "partner_title": first_row["partner_title"],
                    "partner_firstname": first_row["partner_firstname"],
                    "partner_lastname": first_row["partner_lastname"],
                    "partner_address": first_row["partner_address"],
                    "partner_street": first_row["partner_street"],
                    "partner_street2": first_row["partner_street2"],
                    "partner_city": first_row["partner_city"],
                    "partner_state": first_row["partner_state"],
                    "partner_zip": first_row["partner_zip"],
                    "partner_country": first_row["partner_country"],
                    "partner_vat": first_row["partner_vat"],
                    "partner_branch": first_row["partner_branch"],
                    "partner_bank_account": first_row["partner_bank_account"],
                    "cert_id": cert_id,
                    # Lines
                    "lines": rows,
                }
            )
        return wht_groupby_cert

    def _text_wht_pnd1(self, report_values, wht_textfile_format):
        wht_code_income = self.env["withholding.tax.code.income"]
        text = ""
        for line in report_values["wht_report_data"]:
            if line["wht_cert_income_code"]:
                wht_code_income = wht_code_income.browse(
                    line["wht_cert_income_code"][0]
                )
            args = defaultdict(str, {"income_code": wht_code_income.code or ""})
            for field in line:
                if field == "cert_date":
                    args[field] = self.format_thai_date(
                        line[field],
                        month_format="numeric",
                        format_date="{day:02d}{month}{year}",
                    )
                elif field in ["base", "amount"]:
                    args[field] = f"{line[field]:,.2f}"
                elif field == "cert_tax_payer":
                    args[field] = self._convert_wht_tax_payer(line[field])
                elif field == "wht_percent":
                    args[field] = int(line[field])
                else:
                    args[field] = line[field] or ""

            text += wht_textfile_format % args
        return text

    def _create_text_wht(self, report_values, wht_textfile_format):
        text = ""
        # NOTE: PND1 support 1 line only
        if report_values["income_tax_form"] == "pnd1":
            text = self._text_wht_pnd1(report_values, wht_textfile_format)
            return text

        wht_groupby_cert = self._get_wht_group_cert(report_values["wht_report_data"])
        loop_fields = [
            f
            for f in self._extract_fields_from_template(wht_textfile_format)
            if f.startswith("loop_")
        ]

        max_lines = (
            max(len(cert["lines"]) for cert in wht_groupby_cert)
            if wht_groupby_cert
            else 0
        )
        for cert in wht_groupby_cert:
            args = self._prepare_display_wht_textfile(cert)

            if loop_fields:
                loop_parts = []
                for i in range(max_lines):
                    if i < len(cert["lines"]):
                        line_args = self._prepare_display_wht_textfile(
                            cert["lines"][i], prefix="loop_"
                        )
                        loop_parts.append(
                            "".join([f"|{line_args[f]}" for f in loop_fields])
                        )
                    else:
                        loop_parts.append("".join(["|" for _ in loop_fields]))

                args["__loop__"] = "".join(loop_parts)

                wht_textfile_format = wht_textfile_format.replace(
                    "|".join([f"%({f})s" for f in loop_fields]),
                    "%(__loop__)s",
                )

            text += wht_textfile_format % args
        return text

    def _get_report_values(self, docids, data):
        report_values = super()._get_report_values(docids, data)
        data = report_values["docs"]._prepare_report_wht()

        company = self.env["res.company"].browse(data["company_id"])

        try:
            wht_textfile_format = company[
                f"wht_text_file_{report_values['income_tax_form']}_format"
            ]
        except Exception as e:
            raise UserError(
                f"Not implement {report_values['income_tax_form']} yet"
            ) from e

        text_file_value = self._create_text_wht(report_values, wht_textfile_format)
        report_values["text_file_value"] = text_file_value
        return report_values
