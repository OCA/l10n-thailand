# Copyright 2026 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.tools import SQL


class WHTReport(models.Model):
    """Withholding tax income and withholding, from posted journal items
    of payments and journal entries:

    - income: journal items carrying a withholding tax (payment
      "WH Base Counterpart", or the line of a manual journal entry)
    - withholding: withholding tax lines

    Amounts are signed by tax use, so refunds reduce the totals.
    """

    _name = "wht.report"
    _description = "Withholding Tax Report"
    _auto = False
    _rec_name = "partner_id"
    _order = "date desc, id desc"

    move_id = fields.Many2one(
        comodel_name="account.move", string="Journal Entry", readonly=True
    )
    payment_id = fields.Many2one(comodel_name="account.payment", readonly=True)
    journal_id = fields.Many2one(comodel_name="account.journal", readonly=True)
    partner_id = fields.Many2one(comodel_name="res.partner", readonly=True)
    company_id = fields.Many2one(comodel_name="res.company", readonly=True)
    currency_id = fields.Many2one(comodel_name="res.currency", readonly=True)
    tax_id = fields.Many2one(comodel_name="account.tax", readonly=True)
    type_tax_use = fields.Selection(
        selection=[("purchase", "Purchases"), ("sale", "Sales")],
        string="Tax Type",
        readonly=True,
    )
    is_pit = fields.Boolean(string="Personal Income Tax", readonly=True)
    line_type = fields.Selection(
        selection=[("base", "Income"), ("tax", "Withholding")],
        readonly=True,
    )
    date = fields.Date(readonly=True)
    calendar_year = fields.Char(readonly=True)
    amount_income = fields.Monetary(string="Income", readonly=True)
    amount_wht = fields.Monetary(string="Withholding Amount", readonly=True)

    def _get_wht_line_domain(self):
        return [
            ("parent_state", "=", "posted"),
            ("move_id.move_type", "=", "entry"),
            ("move_id.tax_cash_basis_origin_move_id", "=", False),
            "|",
            ("tax_line_id.is_withholding_tax", "=", True),
            "&",
            ("tax_repartition_line_id", "=", False),
            "|",
            ("tax_ids.is_withholding_tax", "=", True),
            ("tax_ids.children_tax_ids.is_withholding_tax", "=", True),
        ]

    @property
    def _table_sql(self) -> SQL:
        self.env["account.move.line"].check_access("read")
        query = (
            self.env["account.move.line"].sudo()._search(self._get_wht_line_domain())
        )
        return SQL(
            """(
            SELECT
                line.id,
                line.move_id,
                line.payment_id,
                line.journal_id,
                line.partner_id,
                line.company_id,
                line.currency_id,
                line.tax_id,
                tax.type_tax_use,
                tax.is_pit,
                line.line_type,
                line.date,
                TO_CHAR(line.date, 'YYYY') AS calendar_year,
                CASE WHEN line.line_type = 'base' THEN line.balance * sign.factor
                    ELSE 0.0 END AS amount_income,
                CASE WHEN line.line_type = 'tax' THEN -line.balance * sign.factor
                    ELSE 0.0 END AS amount_wht
            FROM (%(lines)s) line
            JOIN account_tax tax ON tax.id = line.tax_id
            -- Customer withholds us: income is credit, withholding is debit
            CROSS JOIN LATERAL (
                SELECT CASE WHEN tax.type_tax_use = 'sale' THEN -1 ELSE 1 END
                    AS factor
            ) sign
            )""",
            lines=query.subselect(*self._select_list(query.table)),
        )

    def _select_list(self, table):
        # Base line: the withholding tax in tax_ids, also inside a group tax
        base_tax = SQL(
            """(
                SELECT COALESCE(child.id, tax.id)
                FROM account_move_line_account_tax_rel rel
                JOIN account_tax tax ON tax.id = rel.account_tax_id
                LEFT JOIN account_tax_filiation_rel filiation
                    ON filiation.parent_tax = tax.id
                LEFT JOIN account_tax child
                    ON child.id = filiation.child_tax AND child.is_withholding_tax
                WHERE rel.account_move_line_id = %s
                    AND (tax.is_withholding_tax OR child.id IS NOT NULL)
                LIMIT 1
            )""",
            table.id,
        )
        return [
            SQL("%s AS id", table.id),
            SQL("%s AS move_id", table.move_id),
            SQL("%s AS payment_id", table.move_id.origin_payment_id),
            SQL("%s AS journal_id", table.journal_id),
            SQL(
                "COALESCE(%s, %s) AS partner_id",
                table.partner_id,
                table.move_id.partner_id,
            ),
            SQL("%s AS company_id", table.company_id),
            SQL("%s AS currency_id", table.company_currency_id),
            SQL("COALESCE(%s, %s) AS tax_id", table.tax_line_id, base_tax),
            SQL(
                "CASE WHEN %s IS NULL THEN 'base' ELSE 'tax' END AS line_type",
                table.tax_line_id,
            ),
            SQL("%s AS date", table.date),
            SQL("%s AS balance", table.balance),
        ]
