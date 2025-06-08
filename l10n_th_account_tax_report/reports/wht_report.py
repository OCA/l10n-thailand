# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import models


class WithholdingTaxReport(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_withholding_tax"
    _description = "Thai Withholding Tax Report"

    def _domain_wht(self, income_tax_form, date_from, date_to, show_cancel, company):
        # fields required
        domain = [
            (
                "cert_id.income_tax_form",
                "=",
                "pnd1" if income_tax_form == "pnd1a" else income_tax_form,
            ),
            ("cert_id.date", ">=", date_from),
            ("cert_id.date", "<=", date_to),
            ("cert_id.company_partner_id", "=", company.partner_id.id),
            ("cert_id.state", "!=", "draft"),
        ]
        if not show_cancel:
            domain.append(("cert_id.state", "!=", "cancel"))
        return domain

    def _get_wht_fields(self, income_tax_form):
        return [
            "cert_id",
            "wht_cert_income_code",
            "wht_cert_income_desc",
            "wht_cert_income_type",
            "wht_cert_bank_account",
            "wht_percent",
            "base",
            "amount",
        ]

    def _get_wht_data(self, income_tax_form, date_from, date_to, show_cancel, company):
        domain = self._domain_wht(
            income_tax_form, date_from, date_to, show_cancel, company
        )
        fields = self._get_wht_fields(income_tax_form)
        return (
            self.env["withholding.tax.cert.line"]
            .sudo()
            .search_read(
                domain=domain,
                fields=fields,
            )
        )

    def _add_data_line(self, wht_report_data):
        wht_cert_model = self.env["withholding.tax.cert"]
        partner_bank_model = self.env["res.partner.bank"]
        total_base = 0.0
        total_wht = 0.0
        for i, line in enumerate(wht_report_data):
            cert = wht_cert_model.browse(line["cert_id"][0])
            cert_cancel = cert.state == "cancel"
            selection = dict(cert._fields["tax_payer"].selection)

            # Partner
            partner = cert.partner_id
            partner_address = partner._display_address(without_company=True)
            firstname = partner.name
            lastname = partner.lastname or ""
            if lastname:
                firstname = firstname[: -(len(lastname))]
            if partner.company_type == "company":
                firstname = partner.name
                lastname = ""

            # Partner Bank Account
            if line["wht_cert_income_type"] == "4A" and line["wht_cert_bank_account"]:
                partner_bank_account = partner_bank_model.browse(
                    line["wht_cert_bank_account"][0]
                ).sanitized_acc_number
            else:
                partner_bank_account = False

            # Condition of Tax Payer
            # - Withholding Tax: 1
            # - Paid One Time
            #     - PND53: 2
            #     - Not PND53: 3
            # - Paid Continuously
            #     - PND53: 3
            #     - Not PND53: 2
            if cert.tax_payer == "withholding":
                cert_tax_payer_code = 1
            elif cert.tax_payer == "paid_one_time":  # Paid One Time
                cert_tax_payer_code = 2 if cert.income_tax_form == "pnd53" else 3
            else:  # Paid Continuously
                cert_tax_payer_code = 3 if cert.income_tax_form == "pnd53" else 2

            # Add header data to line
            line.update(
                {
                    "row_number": i + 1,
                    "cert_cancel": cert_cancel,
                    "cert_date": cert.date,
                    "cert_date_str": cert.date.strftime("%d/%m/%Y"),
                    "cert_name": cert.name,
                    "cert_tax_payer": cert.tax_payer,
                    "cert_tax_payer_display": selection.get(cert.tax_payer),
                    "cert_tax_payer_code": cert_tax_payer_code,
                    "partner_id": partner.id,
                    "partner_name": not cert_cancel
                    and partner.display_name
                    or "Cancelled",
                    "partner_title": partner.title.name,
                    "partner_firstname": firstname,
                    "partner_lastname": lastname,
                    "partner_address": not cert_cancel and partner_address or False,
                    "partner_street": not cert_cancel and partner.street or False,
                    "partner_street2": not cert_cancel and partner.street2 or False,
                    "partner_city": not cert_cancel and partner.city or False,
                    "partner_state": not cert_cancel and partner.state_id.name or False,
                    "partner_zip": not cert_cancel and partner.zip or False,
                    "partner_country": not cert_cancel
                    and partner.country_id.name
                    or False,
                    "partner_vat": partner.vat,
                    "partner_branch": partner.company_registry,
                    "partner_bank_account": partner_bank_account,
                }
            )
            total_base += line["base"]
            total_wht += line["amount"]
        return total_base, total_wht, wht_report_data

    def _get_wht_group_partner(self, wht_report_data):
        grouped = defaultdict(list)
        wht_groupby_partner = []

        for row in wht_report_data:
            grouped[row["partner_id"]].append(row)

        for idx, (partner_id, rows) in enumerate(grouped.items(), start=1):
            total_base = sum(r["base"] for r in rows)
            total_amount = sum(r["amount"] for r in rows)
            first_row = rows[0]
            wht_groupby_partner.append(
                {
                    "row_number": idx,
                    "partner_id": partner_id,
                    "partner_firstname": first_row["partner_firstname"],
                    "partner_lastname": first_row["partner_lastname"],
                    "partner_address": first_row["partner_address"],
                    "partner_vat": first_row["partner_vat"],
                    "partner_branch": first_row["partner_branch"],
                    "cert_tax_payer_code": first_row["cert_tax_payer_code"],
                    "total_base": total_base,
                    "total_amount": total_amount,
                }
            )
        return wht_groupby_partner

    def _get_report_values(self, docids, data):
        docs = self.env["withholding.tax.report.wizard"].browse(docids)
        data = docs._prepare_report_wht()

        company = self.env["res.company"].browse(data["company_id"])
        date_from = data["date_from"]
        date_to = data["date_to"]
        income_tax_form = data["income_tax_form"]
        show_cancel = data["show_cancel"]

        wht_report_data = self._get_wht_data(
            income_tax_form=income_tax_form,
            date_from=date_from,
            date_to=date_to,
            show_cancel=show_cancel,
            company=company,
        )

        # Add parameter to line
        total_base, total_wht, wht_report_data = self._add_data_line(wht_report_data)

        if income_tax_form == "pnd1a" or self.env.context.get("need_group_by_partner"):
            wht_groupby_partner = self._get_wht_group_partner(wht_report_data)
        else:
            wht_groupby_partner = []

        return {
            "doc_ids": docids,
            "doc_model": "withholding.tax.report.wizard",
            "docs": docs,
            "wht_report_format": company.wht_report_format,
            "company_name": company.display_name,
            "company_vat": company.partner_id.vat,
            "company_branch": company.partner_id.company_registry,
            "date_from": date_from,
            "date_to": date_to,
            "income_tax_form": income_tax_form,
            "show_cancel": show_cancel,
            "total_base": total_base,
            "total_wht": total_wht,
            "wht_report_data": wht_report_data,
            "wht_groupby_partner": wht_groupby_partner,
        }
