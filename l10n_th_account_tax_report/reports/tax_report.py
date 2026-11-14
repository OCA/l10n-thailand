# Copyright 2025 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models
from odoo.tools import SQL


class ThaiTaxReport(models.AbstractModel):
    _name = "report.l10n_th_account_tax_report.report_thai_tax"
    _description = "Thai Tax Report"

    # The query of the report, in parts to extend it: SELECT
    # `_query_select_tax` FROM (SELECT `_query_select_sub_tax` FROM
    # `_query_from_tax` WHERE `_query_where_tax`) GROUP BY `_query_groupby_tax`.
    # Each part is an SQL object, to compose it with parameters, e.g.
    # SQL("%s AND m.branch_id = %s", super()._query_where_tax(data), data["branch_id"])

    def _query_select_tax(self):
        """Columns of a line of the report, from the columns of the tax invoices
        (`_query_select_sub_tax`)"""
        # `name` is aggregated (not grouped) so that several documents sharing
        # the same tax_invoice_number collapse into a single report line. This
        # covers cash-basis purchases where one vendor tax invoice is issued for
        # a group payment of multiple bills. Sales numbers come from a sequence
        # (unique per line) so they never merge unintentionally.
        return SQL(
            """
            ROW_NUMBER() OVER (ORDER BY tax_date, tax_invoice_number) AS row_number,
            company_id, account_id, partner_id, tax_invoice_number,
            TO_CHAR(tax_date, 'DD/MM/YYYY') AS tax_date,
            string_agg(DISTINCT name, ', ' ORDER BY name) AS name,
            array_agg(DISTINCT move_id) AS move_ids,
            sum(tax_base_amount) tax_base_amount,
            sum(tax_amount) tax_amount
            """
        )

    def _query_select_sub_tax(self):
        """Columns of the tax invoices, from the tables of `_query_from_tax`"""
        return SQL(
            """
            t.id, m.id AS move_id, t.company_id, ml.account_id, t.partner_id,
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
        )

    def _query_from_tax(self):
        """Tables of the tax invoices: t (tax invoice), ml (its journal item) and
        m (its journal entry), to join other tables"""
        return SQL(
            """
            account_move_tax_invoice t
            JOIN account_move_line ml ON ml.id = t.move_line_id
            JOIN account_move m ON m.id = ml.move_id
            """
        )

    def _query_groupby_tax(self):
        return SQL("company_id, account_id, partner_id, tax_invoice_number, tax_date")

    def _domain_where_clause_tax(self, show_cancel):
        if show_cancel:
            return SQL("ml.parent_state IN ('posted', 'cancel')")
        return SQL("ml.parent_state = 'posted'")

    def _query_where_tax(self, data):
        """Conditions on the tax invoices, from the values of the wizard
        (`tax.report.wizard._prepare_report_tax`)"""
        date_from, date_to = data["date_from"], data["date_to"]
        return SQL(
            """
            %s
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
            """,
            self._domain_where_clause_tax(data["show_cancel"]),
            data["tax_id"],
            date_from,
            date_to,
            date_to.month,
            date_to.year,
            date_from.month,
            date_from.year,
            data["company_id"],
        )

    def _get_tax_query(self, data):
        return SQL(
            """
            SELECT %s
            FROM (
                SELECT %s
                FROM %s
                WHERE %s
            ) a
            GROUP BY %s
            ORDER BY row_number, tax_date, tax_invoice_number
            """,
            self._query_select_tax(),
            self._query_select_sub_tax(),
            self._query_from_tax(),
            self._query_where_tax(data),
            self._query_groupby_tax(),
        )

    def _get_tax_data(self, data):
        # Raw query: flush all the pending writes, also of the tables joined by
        # other modules
        self.env.flush_all()
        self.env.cr.execute(self._get_tax_query(data))
        return self.env.cr.dictfetchall()

    def _add_data_line(self, tax_report_data):
        partner_model = self.env["res.partner"]
        # Read the partners and moves of all the lines at once
        partner_ids = tuple(
            {line["partner_id"] for line in tax_report_data if line["partner_id"]}
        )
        moves = self.env["account.move"].browse(
            {move_id for line in tax_report_data for move_id in line["move_ids"]}
        )
        doc_refs = {
            move.id: (
                move.ref or move.name,
                (move.tax_cash_basis_origin_move_id or move).id,
            )
            for move in moves
        }
        total_base = 0.0
        total_tax = 0.0
        for line in tax_report_data:
            line["doc_refs"] = sorted(
                {doc_refs[move_id] for move_id in line["move_ids"]}
            )
            partner_id = partner_model.browse(line["partner_id"]).with_prefetch(
                partner_ids
            )
            line.update(
                {
                    "partner_name": partner_id.display_name,
                    "partner_vat": partner_id.vat,
                    "partner_branch": partner_id._get_tax_report_branch(),
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

        tax_report_data = self._get_tax_data(data)

        # Add parameter to line
        total_base, total_tax, tax_report_data = self._add_data_line(tax_report_data)

        return {
            "doc_ids": docids,
            "doc_model": "tax.report.wizard",
            "docs": docs,
            "tax_report_format": company.tax_report_format,
            "company_name": company.display_name,
            "company_vat": company.partner_id.vat,
            "company_branch": company.partner_id._get_tax_report_branch(),
            "date_from": date_from,
            "date_to": date_to,
            "tax_id": tax_id,
            "show_cancel": show_cancel,
            "total_base": total_base,
            "total_tax": total_tax,
            "tax_report_data": tax_report_data,
        }
