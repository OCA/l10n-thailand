# Copyright 2022 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

DEFAULT_DAY_FORMAT_WHT = "%d"
DEFAULT_MONTH_FORMAT_WHT = "%m"
DEFAULT_YEAR_FORMAT_WHT = "%Y"
INCOME_TAX_FORM = {"pnd1": "P01", "pnd1a": "P01A", "pnd3": "P03", "pnd53": "P53"}


class RdWithHoldingTaxReport(models.TransientModel):
    _name = "rd.withholding.tax.report"
    _description = "WHT RD Report"

    income_tax_form = fields.Selection(
        selection=[
            ("pnd1", "PND1"),
            ("pnd1a", "PND1A"),
            ("pnd3", "PND3"),
            ("pnd53", "PND53"),
        ],
        string="Income Tax Form",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        ondelete="cascade",
    )
    date_range_id = fields.Many2one(
        comodel_name="date.range", string="Date range", required=True
    )
    date_from = fields.Date()
    date_to = fields.Date()
    show_cancel = fields.Boolean(string="Show cancelled")
    results = fields.Many2many(
        comodel_name="withholding.tax.cert.line",
        string="Results",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def format_date_dmy(self, date=None):
        if not date:
            date = fields.Date.context_today()
        year_thai = int(date.strftime(DEFAULT_YEAR_FORMAT_WHT)) + 543
        date_format = date.strftime(
            "{}/{}/{}".format(
                DEFAULT_DAY_FORMAT_WHT, DEFAULT_MONTH_FORMAT_WHT, year_thai
            )
        )
        return date_format

    def format_date(self, date=None):
        if not date:
            # date month before
            date = self.date_from
        year_thai = int(date.strftime(DEFAULT_YEAR_FORMAT_WHT)) + 543
        month = date.strftime(DEFAULT_MONTH_FORMAT_WHT)
        date_format = "{}{}".format(year_thai, month)
        return date_format

    def _get_report_base_filename(self):
        self.ensure_one()
        pnd = INCOME_TAX_FORM[self.income_tax_form]
        date_format = self.format_date()
        return "WHT-RD-{}-{}".format(pnd, date_format)

    def print_report(self, report_type="qweb-pdf"):
        self.ensure_one()
        if report_type != "qweb-pdf":
            raise ValidationError(_("Only export pdf!"))
        report_name = "l10n_th_account_tax_report_rd.report_rd_withholding_tax_qweb"
        context = dict(self.env.context)
        action = self.env["ir.actions.report"].search(
            [("report_name", "=", report_name), ("report_type", "=", report_type)],
            limit=1,
        )

        return action.with_context(context).report_action(self, config=False)

    @api.onchange("date_range_id")
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    def _compute_results(self):
        self.ensure_one()
        Result = self.env["withholding.tax.cert.line"]
        # pnd1a = pnd1
        income_tax_form = (
            "pnd1" if self.income_tax_form == "pnd1a" else self.income_tax_form
        )
        # fields required
        domain = [
            ("cert_id.income_tax_form", "=", income_tax_form),
            ("cert_id.date", ">=", self.date_from),
            ("cert_id.date", "<=", self.date_to),
            ("cert_id.company_partner_id", "=", self.company_id.partner_id.id),
            ("cert_id.state", "!=", "draft"),
        ]
        if not self.show_cancel:
            domain += [("cert_id.state", "!=", "cancel")]
        self.results = Result.search(domain)

    def _convert_result_to_dict(self, results):
        result_dict = dict()
        for line in results:
            # Prepare cert data
            if line.cert_id.id not in result_dict.keys():
                cert_data = self._prepare_cert_data(line)
                result_dict[line.cert_id.id] = cert_data
            # Add wht lines data
            wht_lines = result_dict[line.cert_id.id]["wht_lines"]
            wht_lines.append(self._prepare_line_data(line))
            result_dict[line.cert_id.id]["wht_lines"] = wht_lines
        return result_dict

    def _prepare_cert_data(self, line):
        line.ensure_one()
        partner = line.cert_id.partner_id
        # Partner Name
        lastname = partner.lastname
        firstname = partner.name[: -(len(lastname))]
        if partner.company_type == "company":
            firstname = partner.name
            lastname = ""
        # Partner Address
        address = " ".join(
            [
                x
                for x in [
                    partner.street,
                    partner.street2,
                    partner.city,
                    partner.state_id and partner.state_id.name or False,
                    partner.zip,
                    partner.country_id and partner.country_id.name or False,
                ]
                if x
            ]
        )
        # Condition
        tax_payer = 1
        if line.cert_id.tax_payer != "withholding":
            tax_payer = 2
        return {
            "partner_vat": partner.vat or "XXXXXXXXXXXXX",
            "partner_branch": partner.branch,
            "partner_firstname": firstname,
            "partner_lastname": lastname,
            "partner_address": address,
            "date": (line.cert_id.date + relativedelta(years=543)).strftime("%d/%m/%Y"),
            "tax_payer": tax_payer,
            "wht_lines": [],
        }

    def _prepare_line_data(self, line):
        line.ensure_one()
        return {
            "wht_cert_income_desc": line.wht_cert_income_desc,
            "wht_percent": line.wht_percent,
            "base": line.base,
            "amount": line.amount,
        }
