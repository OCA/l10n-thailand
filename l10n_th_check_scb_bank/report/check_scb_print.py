# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models

DEFAULT_FACTURX_DATE_FORMAT = "%d/%m/%Y"


class ReportCheckPrintTop(models.AbstractModel):
    _name = "report.l10n_th_check_scb_bank.report_check_scb_base"
    _inherit = "report.account_check_printing_report_base.report_check_base"
    _description = "report check scb bank"

    def format_date(self, date):
        # Format the date in the Factur-x standard.
        return date.strftime(DEFAULT_FACTURX_DATE_FORMAT)

    def fill_bracket_amount_text(self, amount, currency_id):
        lang = self.env.user.lang
        if currency_id.name == "THB":
            lang = "th_TH"
        amount_words = currency_id.with_context({"lang": lang}).amount_to_text(amount)
        str_prefix = " ".join(["(", amount_words, ")"])
        return str_prefix

    def fill_equal_number(self, amount):
        str_prefix = " ".join(["=", str("{:,.2f}".format(amount)), "="])
        return str_prefix

    @api.model
    def _get_report_values(self, docids, data=None):
        docargs = super()._get_report_values(docids, data)
        docargs["fill_equal_number"] = self.fill_equal_number
        docargs["fill_bracket_amount_text"] = self.fill_bracket_amount_text
        docargs["format_date"] = self.format_date
        return docargs
