# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class ThaiTaxReport(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_thai_tax"
    _description = "Thai Tax Report"

    def _query_select_tax(self):
        return """
            ROW_NUMBER() OVER (ORDER BY tax_date, tax_invoice_number) AS row_number,
            company_id, account_id, partner_id, tax_invoice_number,
            TO_CHAR(tax_date, 'DD/MM/YYYY') AS tax_date,
            name, sum(tax_base_amount) tax_base_amount,
            sum(tax_amount) tax_amount
        """

    def _query_select_sub_tax(self):
        return """t.id, t.company_id, ml.account_id, t.partner_id,
            CASE WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                THEN t.tax_invoice_number
            ELSE
                t.tax_invoice_number || ' (VOID)'
            END AS tax_invoice_number,
            t.tax_invoice_date AS tax_date,
            CASE WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                THEN t.tax_base_amount
            ELSE 0.0
            END AS tax_base_amount,
            CASE WHEN ml.parent_state = 'posted' AND t.reversing_id IS NULL
                THEN t.balance
            ELSE 0.0
            END AS tax_amount,
            CASE WHEN m.ref IS NOT NULL
                THEN m.ref
            ELSE ml.move_name
            END AS name
        """

    def _query_groupby_tax(self):
        return "company_id, account_id, partner_id, tax_invoice_number, tax_date, name"

    def _domain_where_clause_tax(self, show_cancel):
        condition = "IN ('posted', 'cancel')" if show_cancel else "= 'posted'"
        return " ".join(["ml.parent_state", condition])

    def _get_tax_data(self, tax_id, date_from, date_to, show_cancel, company_id):
        domain = self._domain_where_clause_tax(show_cancel)
        self._cr.execute(
            f"""
            SELECT {self._query_select_tax()}
            FROM (
                SELECT {self._query_select_sub_tax()}
                FROM account_move_tax_invoice t
                JOIN account_move_line ml ON ml.id = t.move_line_id
                JOIN account_move m ON m.id = ml.move_id
                WHERE {domain}
                    AND t.tax_invoice_number IS NOT NULL
                    AND ml.account_id IN (
                        SELECT account_id
                        FROM account_tax_repartition_line
                        WHERE account_id is not null AND tax_id = %s
                        GROUP BY account_id
                    )
                    -- query condition with normal report date by report date
                    -- and late report date within range date end
                    AND (
                        (t.report_date >= %s AND t.report_date <= %s)
                        OR (
                            t.report_late_mo != '0' AND
                            EXTRACT(MONTH FROM t.report_date) <= %s AND
                            EXTRACT(YEAR FROM t.report_date) <= %s AND
                            EXTRACT(MONTH FROM t.report_date) >= %s AND
                            EXTRACT(YEAR FROM t.report_date) >= %s
                        )
                    )
                AND ml.company_id = %s
                AND t.reversed_id is null
            ) a
            GROUP BY {self._query_groupby_tax()}
            ORDER BY tax_date, tax_invoice_number
        """,
            (
                tax_id,
                date_from,
                date_to,
                date_to.month,
                date_to.year,
                date_from.month,
                date_from.year,
                company_id,
            ),
        )
        tax_report_data = self._cr.dictfetchall()
        return tax_report_data

    def _add_data_line(self, tax_report_data):
        partner_model = self.env["res.partner"]
        total_base = 0.0
        total_tax = 0.0
        for line in tax_report_data:
            partner_id = partner_model.browse(line["partner_id"])
            line.update(
                {
                    "partner_name": partner_id.display_name,
                    "partner_vat": partner_id.vat,
                    "partner_branch": partner_id.company_registry,
                }
            )
            total_base += line["tax_base_amount"]
            total_tax += line["tax_amount"]
        return total_base, total_tax, tax_report_data

    def _get_report_values(self, docids, data):
        docs = self.env["tax.report.wizard"].browse(docids)
        data = docs._prepare_report_tax()

        company = self.env["res.company"].browse(data["company_id"])
        date_from = data["date_from"]
        date_to = data["date_to"]
        tax_id = data["tax_id"]
        show_cancel = data["show_cancel"]

        tax_report_data = self._get_tax_data(
            tax_id=tax_id,
            date_from=date_from,
            date_to=date_to,
            show_cancel=show_cancel,
            company_id=company.id,
        )

        # Add parameter to line
        total_base, total_tax, tax_report_data = self._add_data_line(tax_report_data)

        return {
            "doc_ids": docids,
            "doc_model": "tax.report.wizard",
            "docs": docs,
            "tax_report_format": company.tax_report_format,
            "company_name": company.display_name,
            "company_vat": company.partner_id.vat,
            "company_branch": company.partner_id.company_registry,
            "date_from": date_from,
            "date_to": date_to,
            "tax_id": tax_id,
            "show_cancel": show_cancel,
            "total_base": total_base,
            "total_tax": total_tax,
            "tax_report_data": tax_report_data,
        }
