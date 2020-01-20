# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging
from io import StringIO

from odoo import models

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug("Can not import csvwriter`.")


class WithholdingTaxCSV(models.AbstractModel):
    _name = "withholding.tax.csv"
    _description = "Report Withholding Tax CSV"

    def _get_objs_for_report(self, docids, data):
        """
        Returns objects for csv report.  From WebUI these
        are either as docids taken from context.active_ids or
        in the case of wizard are in data.  Manual calls may rely
        on regular context, setting docids, or setting data.

        :param docids: list of integers, typically provided by
            qwebactionmanager for regular Models.
        :param data: dictionary of data, if present typically provided
            by qwebactionmanager for TransientModels.
        :param ids: list of integers, provided by overrides.
        :return: recordset of active model for ids.
        """
        if docids:
            ids = docids
        elif data and "context" in data:
            ids = data["context"].get("active_ids", [])
        else:
            ids = self.env.context.get("active_ids", [])
        return self.env[self.env.context.get("active_model")].browse(ids)

    def create_csv_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)
        file_data = StringIO()
        file = csv.DictWriter(file_data, **self.csv_report_options())
        self.generate_csv_report(file, data, objs)
        file_data.seek(0)
        return file_data.read(), "csv"

    def csv_report_options(self):
        """
        :return: dictionary of parameters. At least return 'fieldnames', but
        you can optionally return parameters that define the export format.
        Valid parameters include 'delimiter', 'quotechar', 'escapechar',
        'doublequote', 'skipinitialspace', 'lineterminator', 'quoting'.
        """
        return {"fieldnames": []}

    def generate_csv_report(self, file, data, objs):
        raise NotImplementedError()


class ReportWithholdingTaxCSV(models.AbstractModel):
    _name = "report.report_withholding_tax_csv"
    _inherit = "report.report_csv.abstract"
    _description = "Report Withholding Tax CSV"

    def generate_csv_report(self, writer, data, objs):
        writer.writeheader()
        for obj in objs:
            for idx, line in enumerate(obj.results):
                writer.writerow(
                    {
                        "sequence": idx + 1,
                        "vat": line.cert_id.supplier_partner_id.vat or "",
                        "display_name": line.cert_id.supplier_partner_id.display_name,
                        "street": line.cert_id.supplier_partner_id.street,
                        "date": line.cert_id.date,
                        "income_desc": line.wt_cert_income_desc or "",
                        "tax": line.wt_percent / 100 or 0.00,
                        "base_amount": line.base or 0.00,
                        "tax_amount": line.amount or 0.00,
                        "tax_payer": line.cert_id.tax_payer,
                        "payment_id": line.cert_id.payment_id.display_name,
                    }
                )

    def csv_report_options(self):
        res = super().csv_report_options()
        res["fieldnames"].append("sequence")
        res["fieldnames"].append("vat")
        res["fieldnames"].append("display_name")
        res["fieldnames"].append("street")
        res["fieldnames"].append("date")
        res["fieldnames"].append("income_desc")
        res["fieldnames"].append("tax")
        res["fieldnames"].append("base_amount")
        res["fieldnames"].append("tax_amount")
        res["fieldnames"].append("tax_payer")
        res["fieldnames"].append("payment_id")
        res["delimiter"] = ";"
        res["quoting"] = csv.QUOTE_ALL
        return res
