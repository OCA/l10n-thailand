# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

INCOME_TAX_FORM = {
    "pnd1": "P01",
    "pnd1a": "P01A",
    "pnd2": "P02",
    "pnd3": "P03",
    "pnd53": "P53",
}


class WithHoldingTaxReportWizard(models.TransientModel):
    _name = "withholding.tax.report.wizard"
    _description = "Withholding Tax Report Wizard"

    income_tax_form = fields.Selection(
        selection=[
            ("pnd1", "PND1"),
            ("pnd1a", "PND1A"),
            ("pnd2", "PND2"),
            ("pnd3", "PND3"),
            ("pnd53", "PND53"),
        ],
        required=True,
    )
    date_range_id = fields.Many2one(comodel_name="date.range", string="Date Range")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        domain=lambda self: self._get_domain_company_id(),
        string="Company",
        required=True,
        ondelete="cascade",
    )
    show_cancel = fields.Boolean(
        string="Show Cancelled",
        default=True,
    )
    results = fields.Many2many(
        comodel_name="withholding.tax.cert.line",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    @api.constrains("date_from", "date_to")
    def check_date_from_to(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(_("Date From must not be after Date To"))

    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._export(report_type)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def button_export_txt(self):
        self.ensure_one()
        report_type = "qweb-text"
        return self._export(report_type)

    def _export(self, report_type):
        """Default export is PDF."""
        return self._print_report(report_type)

    def _print_report(self, report_type):
        self.ensure_one()
        if report_type == "xlsx":
            report_name = "l10n_th_account_tax_report.report_withholding_tax_xlsx"
        elif report_type == "qweb-text":
            report_name = "l10n_th_account_tax_report.report_withholding_tax_text"
        else:
            if self.company_id.wht_report_format == "rd" and report_type == "qweb-pdf":
                report_name = "l10n_th_account_tax_report.report_rd_withholding_tax"
            else:
                report_name = "l10n_th_account_tax_report.report_withholding_tax"
        return (
            self.env["ir.actions.report"]
            .search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
            .report_action(self, config=False)
        )

    def _get_domain_company_id(self):
        selected_companies = self.env["res.company"].browse(
            self.env.context.get("allowed_company_ids")
        )
        return [("id", "in", selected_companies.ids)]

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    def _get_domain_wht(self):
        # fields required
        domain = [
            (
                "cert_id.income_tax_form",
                "=",
                "pnd1" if self.income_tax_form == "pnd1a" else self.income_tax_form,
            ),
            ("cert_id.date", ">=", self.date_from),
            ("cert_id.date", "<=", self.date_to),
            ("cert_id.company_partner_id", "=", self.company_id.partner_id.id),
            ("cert_id.state", "!=", "draft"),
        ]
        if not self.show_cancel:
            domain.append(("cert_id.state", "!=", "cancel"))
        return domain

    def _compute_results(self):
        self.ensure_one()
        domain = self._get_domain_wht()
        self.results = self.env["withholding.tax.cert.line"].sudo().search(domain)

    def _create_text(self, docs):
        """Text File PND
        - PND1 :
            1. income code
            2. index
            3. vat
            4. title
            5. firstname
            6. lastname
            7. date
            8. type of income
            9. base amount
            10. wht amount
            11. tax payer

        - PND3 :
            1. index
            2. vat
            3. tax branch
            4. title
            5. firstname
            6. lastname
            7-11. Street, Street2, City, State ID, zip
            12. date
            13. type of income (description)
            14. wht percent
            15. base amount
            16. wht amount
            17. tax payer

        - PND53 :
            1. index
            2. vat
            3. tax branch
            4. name
            5-9. Street, Street2, City, State ID, zip
            10. date
            11. type of income (description)
            12. wht percent
            13. base amount
            14. wht amount
            15. tax payer
            16. tax branch
        """
        self.ensure_one()
        for obj in docs:
            text = ""
            for idx, line in enumerate(obj.results):
                income_code = (
                    line.wht_cert_income_code
                    and "{}|".format(line.wht_cert_income_code.code)
                    or ""
                )
                partner_id = line.cert_id.partner_id
                vat = partner_id.vat or ""
                type_income_desc = (
                    line.wht_income_tax_form != "pnd1"
                    and "{}|{}|".format(
                        line.wht_cert_income_desc, int(line.wht_percent)
                    )
                    or ""
                )
                name = obj.find_information(partner_id, line)
                address = obj.find_address(partner_id, line)
                tax_branch = (
                    line.wht_income_tax_form in ["pnd53", "pnd3"]
                    and "|{}".format(partner_id.branch or "00000")
                    or ""
                )
                # For case show cancelled, amount must show 0.0
                cancel = line.cert_id.state == "cancel"
                text += (
                    "{income_code}{index}|{vat}{tax_branch}|{name}|{address}{date}|"
                    "{type_income_desc}{base_amount}|{wht_amount}|{tax_payer}"
                    "\n".format(
                        income_code=income_code,  # for pnd1 only
                        index=idx + 1,
                        vat=vat,
                        tax_branch=tax_branch,
                        name=name,
                        address=address
                        and "{}|".format(address)
                        or "",  # pnd3, 53 (optional)
                        date=self.format_wht_date_dmy(line.cert_id.date),
                        type_income_desc=type_income_desc,
                        base_amount=not cancel and "{:,.2f}".format(line.base) or 0.00,
                        wht_amount=not cancel and "{:,.2f}".format(line.amount) or 0.00,
                        tax_payer=self._convert_tax_payer(line.cert_id.tax_payer),
                    )
                )
        return text

    def find_information(self, partner_id, line):
        # PND53
        if line.wht_income_tax_form == "pnd53":
            name = "{}".format(
                partner_id.company_type == "person"
                and (partner_id.firstname or partner_id.lastname)
                or partner_id.name_company
            )
        # PND3, PND1, PND1A
        else:
            name = (
                partner_id.company_type == "person"
                and self._get_name_filter(
                    title=partner_id.title.name,
                    firstname=partner_id.firstname,
                    lastname=partner_id.lastname,
                )
                or self._get_name_filter(firstname=partner_id.name_company)
            )
        return name

    def _get_name_filter(self, title=False, firstname=False, lastname=False):
        return "{}|{}|{}".format(title or "", firstname or "", lastname or "")

    def find_address(self, partner_id, line):
        if line.wht_income_tax_form == "pnd1":
            return ""
        return "|".join(
            [
                partner_id.street or "",
                partner_id.street2 or "",
                partner_id.city or "",
                partner_id.state_id.name or "",
                partner_id.zip or "",
            ]
        )

    def format_wht_date_dmy(self, date, format_date=None):
        year_thai = date.year + 543
        date_format = "{}{}{}".format(
            str(date.day).zfill(2), str(date.month).zfill(2), year_thai
        )
        return date_format

    def _convert_tax_payer(self, tax_payer):
        if tax_payer == "withholding":
            return 1
        if tax_payer == "paid_continue":
            return 2
        return 3  # Paid One Time

    def _prepare_cert_data(self, line):
        line.ensure_one()
        partner = line.cert_id.partner_id
        # Partner Name
        firstname = partner.name
        lastname = partner.lastname or ""
        if lastname:
            firstname = firstname[: -(len(lastname))]
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
        # Condition of Tax Payer
        # - Withholding Tax: 1
        # - Paid One Time
        #     - PND53: 2
        #     - Not PND53: 3
        # - Paid Continuously
        #     - PND53: 3
        #     - Not PND53: 2
        if line.cert_id.tax_payer == "withholding":
            tax_payer = 1
        elif line.cert_id.tax_payer == "paid_one_time":  # Paid One Time
            tax_payer = 2 if line.cert_id.income_tax_form == "pnd53" else 3
        else:  # Paid Continuously
            tax_payer = 3 if line.cert_id.income_tax_form == "pnd53" else 2

        return {
            "partner_vat": partner.vat or " " * 13,  # space when no vat
            "partner_branch": partner.branch,
            "partner_bank_account": line.wht_cert_bank_account.sanitized_acc_number
            if line.wht_cert_income_type == "4A"
            else "",
            "partner_firstname": firstname,
            "partner_lastname": lastname,
            "partner_address": address,
            "date": (line.cert_id.date + relativedelta(years=543)).strftime("%d/%m/%Y"),
            "tax_payer": tax_payer,
            "total_base": 0.0,
            "total_amount": 0.0,
            "wht_lines": [],
        }

    def _convert_result_to_dict(self, results):
        """Function for rd format"""
        result_dict = dict()
        for line in results:
            key = (
                line.cert_id.partner_id.id
                if self.income_tax_form in self._get_income_tax_form_group_partner()
                else line.cert_id.id
            )
            # Prepare cert data
            if key not in result_dict.keys():
                cert_data = self._prepare_cert_data(line)
                result_dict[key] = cert_data
            # Add wht lines data
            wht_line = self._prepare_line_data(line)
            wht_lines = result_dict[key]["wht_lines"]
            wht_lines.append(wht_line)
            result_dict[key]["wht_lines"] = wht_lines
            # Compute total
            result_dict[key]["total_base"] += wht_line["base"]
            result_dict[key]["total_amount"] += wht_line["amount"]
        return result_dict

    def _get_income_tax_form_group_partner(self):
        """Hook function"""
        return ["pnd1a"]

    def _prepare_line_data(self, line):
        line.ensure_one()
        return {
            "wht_cert_income_desc": line.wht_cert_income_desc,
            "wht_percent": line.wht_percent,
            "base": line.base,
            "amount": line.amount,
        }

    def format_date_ym_wht(self, date=None):
        date = date or self.date_from
        year_thai = date.year + 543
        date_format = "{}{}".format(year_thai, str(date.month).zfill(2))
        return date_format

    def _get_report_base_filename(self):
        self.ensure_one()
        pnd = INCOME_TAX_FORM[self.income_tax_form]
        date_format = self.format_date_ym_wht()
        return "WHT-{}-{}".format(pnd, date_format)
